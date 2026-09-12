from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import datetime, timezone, timedelta
from pathlib import Path
from uuid import UUID,uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from redis.exceptions import NoPermissionError
from shared.config import Settings
from shared.service_loader import load_service
from shared.security.sessions import session_key,unpack_refresh
from test_access_integration import lab
from test_pedagogy_unit import body,competency_payload

pytestmark=pytest.mark.integration

@pytest.fixture
def pedagogy(lab):
    with ExitStack() as stack:
        for name in ["curriculum","content"]:
            config=Settings(service_name=name+"-service",db_name=lab.engine.url.database,db_user="edu_"+name,
                db_password_file=Path("/run/secrets/db_"+name),redis_username="edu_"+name,redis_db=15,
                redis_password_file=Path("/run/secrets/redis_"+name))
            lab.clients[name]=stack.enter_context(TestClient(load_service(name+"-service").build_app(config)))
        lab.creator=lab.create("content_creator"); lab.teacher=lab.create("teacher"); lab.student=lab.create()
        lab.creator_token=lab.login(lab.creator["login"]); lab.teacher_token=lab.login(lab.teacher["login"])
        lab.student_token=lab.login(lab.student["login"])
        with lab.engine.begin() as c:
            c.execute(text("UPDATE user_roles SET role='sys_admin' WHERE user_id=:id"),{"id":lab.admin_id})
        lab.admin=lab.login("admin")
        cur=lab.clients["curriculum"]
        response=cur.get("/subjects",headers=lab.headers(lab.admin)); assert response.status_code==200,response.text
        lab.subject=next(s["id"] for s in response.json() if s["code"]=="mathematiques")
        response=cur.post("/domains",headers=lab.headers(lab.admin),json={"subject_id":lab.subject,"code":"test-"+uuid4().hex,"name":"Domaine synthétique"})
        assert response.status_code==201,response.text
        lab.domain=response.json()["id"]
        lab.competencies=[]
        for i in range(3):
            payload=competency_payload(); payload.update(subject_id=lab.subject,domain_id=lab.domain,
                curriculum_level_id="00000000-0000-0000-0000-000000000101",code="TEST-"+uuid4().hex)
            response=cur.post("/competencies",headers=lab.headers(lab.admin),json=payload)
            assert response.status_code==201,response.text
            lab.competencies.append(response.json()["id"])
        response=lab.clients["content"].post("/sources",headers=lab.headers(lab.creator_token),json={
            "title":"Source synthétique","url":"https://example.org/test","publisher":"Test","license":"Test",
            "checksum_sha256":uuid4().hex+uuid4().hex,"retrieved_at":(datetime.now(timezone.utc)-timedelta(days=1)).isoformat()})
        assert response.status_code==201,response.text
        lab.source=response.json()["id"]
        yield lab

def payload(p,kind="lesson"):
    b=body()
    if kind=="learning_sequence": b["steps"]=[dict(title="Lecture",objective="Comprendre",duration_minutes=20,blocks=body()["blocks"])]
    return dict(title="Contenu synthétique",slug="test-"+uuid4().hex,kind=kind,body=b,competency_ids=[p.competencies[0]],source_ids=[p.source])

def create(p,kind="lesson"):
    r=p.clients["content"].post("/contents",headers=p.headers(p.creator_token),json=payload(p,kind))
    assert r.status_code==201,r.text
    return r.json()

def submit(p,v):
    r=p.clients["content"].post(f"/contents/{v['lesson_id']}/versions/{v['version']}/submit",headers=p.headers(p.creator_token))
    assert r.status_code==200,r.text
    return r.json()

def review(p,v,decision="approved",token=None):
    return p.clients["content"].post(f"/contents/{v['lesson_id']}/versions/{v['version']}/reviews",headers=p.headers(token or p.teacher_token),
        json=dict(decision=decision,reason_code="TEST_CHECKED",confirmed_human_review=True))

def add_edge(p,a,b):
    return p.clients["curriculum"].post(f"/competencies/{a}/prerequisites",headers=p.headers(p.admin),json={"prerequisite_id":b})

def test_graph_traversal_levels_and_private_mastery(pedagogy):
    p=pedagogy; a,b,c=p.competencies
    assert add_edge(p,a,b).status_code==201
    assert add_edge(p,b,c).status_code==201
    cur=p.clients["curriculum"]; path=f"/competencies/{a}/graph"
    r=cur.get(path,headers=p.headers(p.student_token),params={"student_id":p.student["student_id"]})
    assert r.status_code==200,r.text
    assert [n["distance"] for n in r.json()["nodes"]]==[0,1,2]
    assert all(n["evaluation_level"]=="non_evalué" for n in r.json()["nodes"])
    with p.engine.begin() as con:
        con.execute(text("INSERT INTO mastery_records(tenant_id,student_id,competency_id,probability,evaluation_level,algorithm_version) VALUES (:school,:student,:competency,0.2,'fragile','test')"),
            dict(school=p.school,student=p.student["student_id"],competency=b))
    r=cur.get(path,headers=p.headers(p.student_token),params={"student_id":p.student["student_id"],"max_depth":1})
    assert r.json()["truncated"] is True
    assert r.json()["nodes"][1]["evaluation_level"]=="fragile"
    assert cur.get(path,headers=p.headers(p.creator_token),params={"student_id":p.student["student_id"]}).status_code==403
    other=p.create(); assert cur.get(path,headers=p.headers(p.student_token),params={"student_id":other["student_id"]}).status_code==404
    r=cur.get(f"/competencies/{c}/graph",headers=p.headers(p.admin),params={"direction":"downstream"})
    assert len(r.json()["nodes"])==3
    assert len(cur.get("/evaluation-levels",headers=p.headers(p.student_token)).json())==6

def test_graph_cycle_self_duplicate_and_concurrent_rejection(pedagogy):
    p=pedagogy; a,b,c=p.competencies
    assert add_edge(p,a,a).status_code==409
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda pair:add_edge(p,*pair),[(a,b),(b,a)]))
    assert sorted(x.status_code for x in results)==[201,409],[r.text for r in results]
    success=next(i for i,r in enumerate(results) if r.status_code==201)
    first,second=[(a,b),(b,a)][success]
    assert add_edge(p,first,second).status_code==409
    response=p.clients["curriculum"].delete(f"/competencies/{first}/prerequisites/{second}",headers=p.headers(p.admin))
    assert response.status_code==204,response.text
    assert add_edge(p,second,first).status_code==201

def test_catalogue_rbac_filters_and_domain_consistency(pedagogy):
    p=pedagogy; cur=p.clients["curriculum"]
    assert cur.get("/subjects").status_code==401
    assert cur.post("/domains",headers=p.headers(p.creator_token),json=dict(subject_id=p.subject,code="forbidden",name="Test")).status_code==403
    r=cur.get("/competencies",headers=p.headers(p.admin),params=dict(domain_id=p.domain,level="CM1",effective_on="2026-09-10"))
    assert r.status_code==200 and len(r.json())==3,r.text
    assert cur.get("/competencies",headers=p.headers(p.admin),params=dict(domain_id=p.domain,level="CM2")).json()==[]
    assert cur.get("/competencies",headers=p.headers(p.admin),params=dict(domain_id=p.domain,effective_on="2020-01-01")).json()==[]
    assert cur.get(f"/competencies/{uuid4()}/graph",headers=p.headers(p.admin)).status_code==404
    assert cur.get(f"/competencies/{p.competencies[0]}/graph?max_depth=1000",headers=p.headers(p.admin)).status_code==422
    q=competency_payload(); q.update(subject_id="00000000-0000-0000-0000-000000000201",domain_id=p.domain,curriculum_level_id="00000000-0000-0000-0000-000000000101")
    assert cur.post("/competencies",headers=p.headers(p.admin),json=q).status_code==422

@pytest.mark.parametrize("kind",["lesson","teaching_sheet","learning_sequence"])
def test_content_types_require_review_before_publication(pedagogy,kind):
    p=pedagogy; content=p.clients["content"]; v=create(p,kind); path=f"/contents/{v['lesson_id']}"
    assert v["status"]=="draft"
    assert content.get(path,headers=p.headers(p.student_token)).status_code==404
    assert content.get(path+"/versions/1",headers=p.headers(p.student_token)).status_code==404
    assert review(p,v).status_code==409
    v=submit(p,v); assert v["review_round"]==1
    assert review(p,v,token=p.creator_token).status_code==403
    assert review(p,v,token=p.admin).status_code==403
    r=review(p,v); assert r.status_code==201,r.text
    approved=content.get(path+"/versions/1",headers=p.headers(p.creator_token)).json()
    assert approved["status"]=="approved" and approved["published_at"]
    assert content.get(path,headers=p.headers(p.student_token)).status_code==(404 if kind=="teaching_sheet" else 200)
    assert review(p,v).status_code==409

def test_version_history_rejection_and_replacement(pedagogy):
    p=pedagogy; content=p.clients["content"]; v=create(p); path=f"/contents/{v['lesson_id']}"
    submit(p,v); assert review(p,v,"changes_requested").status_code==201
    assert content.get(path+"/versions/1",headers=p.headers(p.creator_token)).json()["status"]=="draft"
    submit(p,v); assert review(p,v).status_code==201
    data=payload(p); data.pop("slug"); data.pop("kind"); data.update(base_version=1,title="Révision deux")
    r=content.post(path+"/versions",headers=p.headers(p.creator_token),json=data)
    assert r.status_code==201,r.text
    v2=r.json(); assert v2["version"]==2 and v2["status"]=="draft"
    assert content.get(path,headers=p.headers(p.student_token)).json()["version"]==1
    assert content.post(path+"/versions",headers=p.headers(p.creator_token),json=data).status_code==409
    submit(p,v2); assert review(p,v2).status_code==201
    assert content.get(path,headers=p.headers(p.student_token)).json()["title"]=="Révision deux"
    history=content.get(path+"/versions",headers=p.headers(p.creator_token)).json()
    assert [x["status"] for x in history]==["approved","archived"]
    assert content.get(path+"/versions/1",headers=p.headers(p.student_token)).status_code==404
    assert content.get(path+"/versions",headers=p.headers(p.student_token)).status_code==403
    rs=content.get(path+"/versions/1/reviews",headers=p.headers(p.creator_token)).json()
    assert [r["review_round"] for r in rs]==[1,2]
    response=content.post(path+"/versions/2/archive",headers=p.headers(p.creator_token))
    assert response.status_code==200,response.text
    assert content.get(path,headers=p.headers(p.student_token)).status_code==404
    assert content.post(path+"/versions/2/submit",headers=p.headers(p.creator_token)).status_code==409

def test_concurrent_version_creation_and_review(pedagogy):
    p=pedagogy; content=p.clients["content"]; v=create(p); path=f"/contents/{v['lesson_id']}"
    data=payload(p); data.pop("slug"); data.pop("kind"); data["base_version"]=1
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:content.post(path+"/versions",headers=p.headers(p.creator_token),json=data),range(2)))
    assert sorted(r.status_code for r in results)==[201,409],[r.text for r in results]
    v2=next(r.json() for r in results if r.status_code==201); submit(p,v2)
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(lambda _:review(p,v2),range(2)))
    assert sorted(r.status_code for r in results)==[201,409],[r.text for r in results]

def test_school_isolation_and_editor_rbac(pedagogy):
    p=pedagogy; c=p.clients["content"]; v=create(p); path=f"/contents/{v['lesson_id']}"
    other=p.login("admin",p.other)
    for suffix in ["","/versions","/versions/1","/versions/1/reviews"]:
        assert c.get(path+suffix,headers=p.headers(other)).status_code==404
    assert c.get("/contents",headers=p.headers(other)).json()==[]
    assert c.post(path+"/versions/1/archive",headers=p.headers(other)).status_code==404
    assert c.post(path+"/versions/1/submit",headers=p.headers(p.teacher_token)).status_code==403
    assert c.post("/contents",headers=p.headers(p.student_token),json=payload(p)).status_code==403
    assert c.get("/contents?status=draft",headers=p.headers(p.student_token)).status_code==403
    data=payload(p); data["source_ids"]=[str(uuid4())]
    assert c.post("/contents",headers=p.headers(p.creator_token),json=data).status_code==422
    assert c.get("/sources",headers=p.headers(p.student_token)).status_code==403

def test_database_guards_and_redis_session_read_only(pedagogy):
    p=pedagogy; v=create(p)
    for statement in ["UPDATE lesson_versions SET status='approved' WHERE id=:id",
        "UPDATE lesson_versions SET title='Changed' WHERE id=:id",
        "UPDATE lesson_versions SET review_round=100 WHERE id=:id"]:
        with pytest.raises(DBAPIError) as caught:
            with p.engine.begin() as conn: conn.execute(text(statement),{"id":v["id"]})
        assert caught.value.orig.sqlstate=="23514"
    submit(p,v); assert review(p,v).status_code==201
    with pytest.raises(DBAPIError):
        with p.engine.begin() as conn: conn.execute(text("UPDATE content_reviews SET decision='rejected' WHERE lesson_version_id=:id"),{"id":v["id"]})
    for name in ["curriculum","content"]:
        cache=p.clients[name].app.state.cache; key=session_key(unpack_refresh(p.creator_token["refresh_token"]))
        assert cache.hgetall(key)
        with pytest.raises(NoPermissionError): cache.hset(key,"revoked","1")

def test_stale_pending_version_cannot_publish(pedagogy):
    p=pedagogy; v=create(p); submit(p,v)
    data=payload(p); data.pop("slug"); data.pop("kind"); data["base_version"]=1
    r=p.clients["content"].post(f"/contents/{v['lesson_id']}/versions",headers=p.headers(p.creator_token),json=data)
    assert r.status_code==201,r.text
    assert review(p,v).status_code==409
