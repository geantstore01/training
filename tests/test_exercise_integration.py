from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import datetime,timedelta,timezone
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from redis.exceptions import NoPermissionError
from shared.config import Settings
from shared.service_loader import load_service
from shared.security.sessions import session_key,unpack_refresh
from test_access_integration import lab
from test_pedagogy_integration import pedagogy

pytestmark=pytest.mark.integration

@pytest.fixture
def practice(pedagogy):
    p=pedagogy
    with ExitStack() as stack:
        for name in ["exercise","assessment"]:
            settings=Settings(service_name=name+"-service",db_name=p.engine.url.database,db_user="edu_"+name,
                db_password_file=Path("/run/secrets/db_"+name),redis_username="edu_"+name,redis_db=15,
                redis_password_file=Path("/run/secrets/redis_"+name))
            p.clients[name]=stack.enter_context(TestClient(load_service(name+"-service").build_app(settings)))
        p.e=p.clients["exercise"];p.a=p.clients["assessment"]
        p.live=make_exercise(p)
        r=p.a.post("/sessions",headers=p.headers(p.student_token));assert r.status_code==201,r.text
        p.learning=r.json()
        yield p

def make_exercise(p,kind="short_text",publish=True):
    r=p.e.post("/generate",headers=p.headers(p.creator_token),json={"slug":"test-"+uuid4().hex,
        "generation":{"template":"arithmetic","kind":kind,"seed":42,"competency_id":p.competencies[0],"source_ids":[p.source]}})
    assert r.status_code==201,r.text
    v=r.json()
    if publish: return publish_version(p,v)
    return v

def publish_version(p,v):
    path=f"/exercises/{v['exercise_id']}/versions/{v['version']}"
    r=p.e.post(path+"/submit",headers=p.headers(p.creator_token));assert r.status_code==200,r.text
    r=p.e.post(path+"/reviews",headers=p.headers(p.teacher_token),json={"decision":"approved","reason_code":"TEST_CHECKED","confirmed_human_review":True})
    assert r.status_code==200,r.text
    return r.json()

def start(p,v=None,key=None):
    r=p.a.post("/attempts",headers=p.headers(p.student_token),json={"session_id":p.learning["id"],"exercise_version_id":(v or p.live)["id"],"idempotency_key":str(key or uuid4())})
    assert r.status_code==201,r.text
    return r.json()

def answer(p,a,answers=None,v=None):
    v=v or p.live
    answers=answers if answers is not None else {k:r["expected"] for k,r in v["candidate"]["answers"].items()}
    return p.a.post(f"/attempts/{a['id']}/submit",headers=p.headers(p.student_token),json={"answers":answers})

def test_published_exercise_dto_has_no_answer_key_and_private_endpoints_deny_students(practice):
    p=practice;v=p.live;path=f"/exercises/{v['exercise_id']}/versions/1"
    r=p.e.get(path,headers=p.headers(p.student_token));assert r.status_code==200,r.text
    for forbidden in ["answer_spec","expected","candidate","known_errors","pipeline_report"]: assert forbidden not in r.text
    assert p.e.get(path+"/editorial",headers=p.headers(p.student_token)).status_code==403
    assert p.e.post(path+"/check-answer",headers=p.headers(p.student_token),json={"answers":{}}).status_code==403
    assert p.e.post("/generate",headers=p.headers(p.student_token),json={}).status_code==403
    draft=make_exercise(p,publish=False)
    assert p.e.get(f"/exercises/{draft['exercise_id']}/versions/1",headers=p.headers(p.student_token)).status_code==404
    r=p.a.post("/attempts",headers=p.headers(p.student_token),json={"session_id":p.learning["id"],"exercise_version_id":draft["id"],"idempotency_key":str(uuid4())})
    assert r.status_code==404

def test_submission_is_atomic_idempotent_and_encrypted(practice):
    p=practice;key=uuid4();a=start(p,key=key)
    assert start(p,key=key)["id"]==a["id"]
    r=answer(p,a);assert r.status_code==200,r.text
    result=r.json()
    assert result["result"]["feedback"][0]["outcome"]=="réussi"
    assert answer(p,a).json()==result
    assert answer(p,a,{"main":"incorrect"}).status_code==409
    for private in ["score","probability","evidence_count","ease_factor"]: assert private not in r.text
    with p.engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM mastery_evidence WHERE attempt_id=:id"),{"id":a["id"]})==1
        data=c.execute(text("SELECT response_ciphertext FROM answers WHERE attempt_id=:id"),{"id":a["id"]}).scalar_one()
        assert b'"response"' not in data
        assert c.scalar(text("SELECT evidence_count FROM mastery_records WHERE student_id=:student"),{"student":p.student["student_id"]})==1
    detail=p.a.get(f"/attempts/{a['id']}",headers=p.headers(p.student_token))
    assert detail.status_code==200,detail.text
    assert detail.json()["prompt"]["parts"]==p.live["prompt"]["parts"]
    assert detail.json()["responses"]["main"]==p.live["candidate"]["answers"]["main"]["expected"]
    with pytest.raises(DBAPIError):
        with p.engine.begin() as c: c.execute(text("UPDATE exercise_attempts SET score=0 WHERE id=:id"),{"id":a["id"]})


def test_correction_requires_own_nonempty_attempt_and_hints_are_progressive(practice):
    p=practice;a=start(p)
    path=f"/attempts/{a['id']}"
    assert p.a.get(path+"/correction",headers=p.headers(p.student_token)).status_code==409
    assert p.a.get(path+"/next",headers=p.headers(p.student_token)).status_code==409
    assert answer(p,a,{"main":"  "}).status_code==422
    assert p.a.get(path+"/hints/2",headers=p.headers(p.student_token)).status_code==409
    assert p.a.get(path+"/hints/1",headers=p.headers(p.student_token)).status_code==200
    assert answer(p,a).status_code==200
    assert p.a.get(path+"/correction",headers=p.headers(p.student_token)).status_code==200
    assert p.a.get(path+"/correction",headers=p.headers(p.teacher_token)).status_code==403
    stranger=p.create();token=p.login(stranger["login"])
    assert p.a.get(path+"/correction",headers=p.headers(token)).status_code in (403,404)


def test_repeating_an_assisted_solution_does_not_become_independent_evidence(practice):
    p=practice;a=start(p)
    assert p.a.get(f"/attempts/{a['id']}/hints/1",headers=p.headers(p.student_token)).status_code==200
    assert answer(p,a).status_code==200
    assert answer(p,start(p)).status_code==200
    with p.engine.connect() as connection:
        assert connection.scalar(text("SELECT evidence_count FROM mastery_records WHERE student_id=:id"),{"id":p.student["student_id"]})==0

def test_concurrent_same_attempt_has_one_assessment_event(practice):
    p=practice;a=start(p)
    with ThreadPoolExecutor(max_workers=2) as pool: rs=list(pool.map(lambda _:answer(p,a),range(2)))
    assert [r.status_code for r in rs]==[200,200],[r.text for r in rs]
    assert rs[0].json()==rs[1].json()
    with p.engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM mastery_evidence WHERE attempt_id=:id"),{"id":a["id"]})==1

def test_repeated_and_assisted_attempts_do_not_inflate_mastery(practice):
    p=practice;a=start(p);assert answer(p,a).status_code==200
    repeated=start(p);assert answer(p,repeated).status_code==200
    helped=start(p)
    r=p.a.get(f"/attempts/{helped['id']}/hints/1",headers=p.headers(p.student_token));assert r.status_code==200,r.text
    assert answer(p,helped).status_code==200
    with p.engine.connect() as c:
        assert c.scalar(text("SELECT evidence_count FROM mastery_records WHERE student_id=:id"),{"id":p.student["student_id"]})==1
        reasons=c.execute(text("SELECT reason FROM mastery_evidence WHERE student_id=:id ORDER BY created_at"),{"id":p.student["student_id"]}).scalars().all()
        assert reasons==["independent","repeated","assisted"]

def test_wrong_answers_error_patterns_and_student_scope(practice):
    p=practice
    for _ in range(2):
        r=answer(p,start(p),{"main":"999"});assert r.status_code==200,r.text
    path=f"/students/{p.student['student_id']}"
    errors=p.a.get(path+"/errors",headers=p.headers(p.student_token));assert errors.status_code==200,errors.text
    assert errors.json()[0]["error_code"]=="CALCULATION_ERROR" and errors.json()[0]["recurring"]
    assert len(p.a.get(path+"/attempts",headers=p.headers(p.student_token)).json())==2
    assert p.a.get(path+"/attempts",headers=p.headers(p.teacher_token)).status_code==404
    parent=p.create("parent");p.link(parent,p.student);token=p.login(parent["login"])
    assert p.a.get(path+"/attempts",headers=p.headers(token)).status_code==200
    stranger=p.create();stranger_token=p.login(stranger["login"])
    assert p.a.get(path+"/mastery",headers=p.headers(stranger_token)).status_code==404
    other=p.login("admin",p.other)
    assert p.a.get(path+"/errors",headers=p.headers(other)).status_code==404

def test_step_problem_tracks_each_part_without_public_grade(practice):
    p=practice;v=make_exercise(p,"step_problem");a=start(p,v)
    r=answer(p,a,{"subtotal":v["candidate"]["answers"]["subtotal"]["expected"]},v)
    assert r.status_code==200,r.text
    feedback=r.json()["result"]["feedback"]
    assert [x["outcome"] for x in feedback]==["réussi","à_revoir"]
    assert feedback[1]["error_code"]=="MISSING_ANSWER"
    with p.engine.connect() as c: assert c.scalar(text("SELECT count(*) FROM answers WHERE attempt_id=:id"),{"id":a["id"]})==2

def test_new_version_requires_review_and_old_started_attempt_remains_correctable(practice):
    p=practice;a=start(p);old=p.live
    path=f"/exercises/{old['exercise_id']}/versions"
    candidate=old["candidate"];candidate["instruction"]="Nouvelle consigne de test"
    r=p.e.post(path,headers=p.headers(p.creator_token),json={"base_version":1,"candidate":candidate})
    assert r.status_code==201,r.text
    new=publish_version(p,r.json());assert new["version"]==2
    assert p.e.get(path+"/1",headers=p.headers(p.student_token)).status_code==404
    assert answer(p,a).status_code==200
    assert p.e.post(path,headers=p.headers(p.creator_token),json={"base_version":1,"candidate":candidate}).status_code==409

def test_session_completion_unknown_parts_and_cross_session_keys(practice):
    p=practice;a=start(p)
    assert answer(p,a,{"unknown":"1"}).status_code==422
    r=p.a.post(f"/sessions/{p.learning['id']}/complete",headers=p.headers(p.student_token));assert r.status_code==200,r.text
    assert answer(p,a).status_code==409
    assert p.a.post("/sessions",headers=p.headers(p.teacher_token)).status_code==403

def test_linguistic_unknown_formulations_require_human_help_without_probability_penalty(practice):
    p=practice;c=p.live["candidate"]
    c["parts"][0]["response_type"]="text";c["parts"][0]["question"]="Écris une phrase autorisée par cette grille de test."
    c["answers"]={"main":{"mode":"formulation","expected":"Une phrase de test","variants":[],"known_errors":{}}}
    r=p.e.post("/exercises",headers=p.headers(p.creator_token),json={"slug":"test-"+uuid4().hex,"candidate":c});assert r.status_code==201,r.text
    v=publish_version(p,r.json());a=start(p,v)
    r=answer(p,a,{"main":"Une formulation non prévue par la grille"},v);assert r.status_code==200,r.text
    assert r.json()["result"]["feedback"][0]["error_code"]=="FORMULATION_NOT_RECOGNIZED"
    with p.engine.connect() as conn:
        row=conn.execute(text("SELECT applied,reason FROM mastery_evidence WHERE attempt_id=:id"),{"id":a["id"]}).one()
        assert row==(False,"unrecognized")

def test_due_queue_and_acl_separation(practice):
    p=practice;assert answer(p,start(p)).status_code==200
    path=f"/students/{p.student['student_id']}/mastery?due_only=true"
    assert p.a.get(path,headers=p.headers(p.student_token)).json()==[]
    with p.engine.begin() as c:
        c.execute(text("UPDATE spaced_repetition_items SET due_at=now()-interval '1 day' WHERE student_id=:id"),{"id":p.student["student_id"]})
    r=p.a.get(path,headers=p.headers(p.student_token));assert r.status_code==200 and len(r.json())==1,r.text
    for name in ["exercise","assessment"]:
        cache=p.clients[name].app.state.cache;key=session_key(unpack_refresh(p.student_token["refresh_token"]))
        assert cache.hgetall(key)
        with pytest.raises(NoPermissionError):cache.hset(key,"revoked","1")


def test_concurrent_distinct_exercises_preserve_both_mastery_updates(practice):
    p=practice
    other=make_exercise(p)
    first,second=start(p),start(p,other)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda item:answer(p,item[0],v=item[1]),[(first,p.live),(second,other)]))
    assert [r.status_code for r in responses]==[200,200],[r.text for r in responses]
    with p.engine.connect() as conn:
        assert conn.scalar(text("SELECT evidence_count FROM mastery_records WHERE student_id=:id"),{"id":p.student["student_id"]})==2
        assert conn.scalar(text("SELECT count(*) FROM mastery_evidence WHERE student_id=:id AND applied"),{"id":p.student["student_id"]})==2
