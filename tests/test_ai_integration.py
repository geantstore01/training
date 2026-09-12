"""PostgreSQL/Redis/HTTP internes réels ; fournisseur et téléchargement doublés explicitement.
Le smoke fournisseur réel est scripts/smoke_ollama.py, sans données d'élèves.
"""
from contextlib import ExitStack
from pathlib import Path
from uuid import uuid4
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from shared.config import Settings
from shared.service_loader import load_service
from shared.ai import transport
from test_access_integration import lab
from test_pedagogy_integration import pedagogy
from test_exercise_integration import practice, start, answer

pytestmark = pytest.mark.integration

def test_history_rag_stays_in_chapter_and_editorial_data_is_private(ai):
    p=ai
    for chapter in ("ferry","industrie"):
        result=p.clients["retrieval"].post("/documents/ingest",headers=p.headers(p.creator_token),json={
            "url":"https://eduscol.education.gouv.fr/document/"+uuid4().hex+"/download","title":"Corpus SYNTHÉTIQUE histoire",
            "level":"CM2","subject":"histoire","history_chapter":chapter,"programme_version":"TEST-NON-OFFICIEL","effective_from":"2026-01-01"})
        assert result.status_code==201,result.text
        identifier=result.json()["id"]
        path=f"/documents/{identifier}"
        assert p.clients["retrieval"].post(path+"/submit",headers=p.headers(p.creator_token)).status_code==200
        assert p.clients["retrieval"].post(path+"/review",headers=p.headers(p.teacher_token),json={"decision":"approved","reason_code":"programme_verified","confirmed_human_review":True}).status_code==200
        if chapter=="ferry":ferry_id=identifier
    response=p.clients["retrieval"].post("/search",headers={**p.headers(p.student_token),**p.internal},json={"query":"fractions","level":"CM2","subject":"histoire","history_chapter":"ferry"})
    assert response.status_code==200,response.text
    assert {row["document_id"] for row in response.json()["passages"]}=={ferry_id}
    assert p.clients["content"].get("/history/review-catalogue",headers=p.headers(p.student_token)).status_code==403
    assert p.clients["content"].get("/history/review-catalogue",headers=p.headers(p.teacher_token)).status_code==200

@pytest.fixture
def ai(practice, monkeypatch):
    p = practice
    with ExitStack() as stack:
        for name in ["retrieval", "ai-router", "tutor"]:
            role = name.replace("-", "_")
            settings = Settings(service_name=name+"-service", db_name=p.engine.url.database, db_user="edu_"+role,
                db_password_file=Path("/run/secrets/db_"+role), redis_username="edu_"+name, redis_db=15,
                redis_password_file=Path("/run/secrets/redis_"+name))
            p.clients[name] = stack.enter_context(TestClient(load_service(name+"-service").build_app(settings)))
        from edu_retrieval_service import routes as retrieval
        from edu_ai_router_service import routes as router
        from edu_tutor_service import routes as tutor
        p.provider_calls = []
        p.provider_bad = False
        def dispatch(url, payload, headers=None, **kwargs):
            if url.endswith("/api/embed"):
                return {"embeddings": [[1.0]+[0.0]*767 for _ in payload["input"]]}
            if url.endswith("/api/chat"):
                p.provider_calls.append(payload)
                data = json.loads(payload["messages"][1]["content"])
                assert "Inès" not in str(payload) and "Durand" not in str(payload)
                value = {"action": data["actions_autorisees"][-1], "source_id":data["sources"][0]["id"], "erreur":"non_determinee"}
                return {"message":{"content":"La réponse est 42" if p.provider_bad else json.dumps(value)}, "prompt_eval_count":120, "eval_count":30}
            name = url.split("//",1)[1].split(":",1)[0].removesuffix("-service")
            path = "/" + url.split(":8000/",1)[1]
            response = p.clients[name].post(path,json=payload,headers=headers)
            if response.status_code != 200:
                raise transport.DependencyFailure("internal_test_"+response.text, response.status_code)
            return response.json()
        monkeypatch.setattr(transport,"post",dispatch)
        monkeypatch.setattr(router,"post",dispatch)
        monkeypatch.setattr(tutor,"post",dispatch)
        monkeypatch.setattr(retrieval,"fetch",lambda url: (("Document SYNTHÉTIQUE de test. Les fractions et les nombres : représenter et comparer des partages. "*15).encode(),"text/plain"))
        p.internal = {"X-Edu-Internal":Path("/run/secrets/ai_internal_key").read_text().strip()}
        p.attempt = start(p)
        yield p

def document(p, *, level="CM1", subject="mathematiques", approve=True):
    r=p.clients["retrieval"].post("/documents/ingest",headers=p.headers(p.creator_token),json={
        "url":"https://eduscol.education.gouv.fr/document/"+uuid4().hex+"/download", "title":"Corpus SYNTHÉTIQUE", "level":level,
        "subject":subject,"programme_version":"TEST-NON-OFFICIEL","effective_from":"2026-01-01"})
    assert r.status_code==201,r.text
    value=r.json()
    if approve:
        r=p.clients["retrieval"].post(f"/documents/{value['id']}/submit",headers=p.headers(p.creator_token));assert r.status_code==200,r.text
        r=p.clients["retrieval"].post(f"/documents/{value['id']}/review",headers=p.headers(p.teacher_token),json={"decision":"approved","reason_code":"programme_verified","confirmed_human_review":True})
        assert r.status_code==200,r.text
        value=r.json()
    return value

def consent(p, cloud=True):
    parent=p.create("parent");p.link(parent,p.student);token=p.login(parent["login"])
    for purpose in (["ai_local","ai_cloud"] if cloud else ["ai_local"]):
        r=p.clients["user"].post(f"/students/{p.student['student_id']}/consents",headers=p.headers(token),json={"purpose":purpose,"policy_version":"2026-09-v1","granted":True,"understood":True});assert r.status_code==201,r.text
        r=p.clients["user"].post("/me/assents",headers=p.headers(p.student_token),json={"purpose":purpose,"policy_version":"2026-09-v1","agreed":True});assert r.status_code==201,r.text

def turn(p, **kwargs):
    payload={"attempt_id":p.attempt["id"],"request_id":str(uuid4()),"message":"Je voudrais comprendre les fractions.",**kwargs}
    return p.clients["tutor"].post("/turns",headers=p.headers(p.student_token),json=payload)

def test_rag_human_review_filters_and_tenant_isolation(ai):
    p=ai;r=p.clients["retrieval"]
    draft=document(p,approve=False)
    search={"query":"fractions","level":"CM1","subject":"mathematiques","limit":8}
    headers={**p.headers(p.student_token),**p.internal}
    assert r.post("/search",headers=p.headers(p.student_token),json=search).status_code==403
    assert r.post("/search",headers=headers,json=search).json()["passages"]==[]
    path=f"/documents/{draft['id']}"
    assert r.post(path+"/submit",headers=p.headers(p.creator_token)).status_code==200
    assert r.post(path+"/review",headers=p.headers(p.creator_token),json={"decision":"approved","reason_code":"programme_verified","confirmed_human_review":True}).status_code==409
    response=r.post(path+"/review",headers=p.headers(p.teacher_token),json={"decision":"approved","reason_code":"programme_verified","confirmed_human_review":True});assert response.status_code==200,response.text
    document(p,level="CM2");document(p,subject="histoire")
    found=r.post("/search",headers=headers,json=search);assert found.status_code==200,found.text
    assert {x["document_id"] for x in found.json()["passages"]}=={draft["id"]}
    other=p.login("admin",p.other)
    assert r.post("/search",headers={**p.headers(other),**p.internal},json=search).json()["passages"]==[]
    assert r.post(path+"/archive",headers=p.headers(p.teacher_token)).status_code==200
    assert r.post("/search",headers=headers,json=search).json()["passages"]==[]

def test_tutor_progression_idempotence_and_assessment_link(ai):
    p=ai;document(p);consent(p)
    key=str(uuid4())
    first=turn(p,request_id=key,message="Je m'appelle Inès Durand et je voudrais comprendre les fractions.")
    assert first.status_code==200,first.text
    assert first.json()["safety_status"]=="safe",first.text
    assert first.json()["niveau_aide"]==0
    retry=turn(p,request_id=key,message="Je m'appelle Inès Durand et je voudrais comprendre les fractions.")
    assert retry.json()==first.json() and len(p.provider_calls)==1
    assert turn(p,request_id=key,message="Autre question").status_code==409
    for level in range(1,7):
        reply=turn(p,plus_aide=True)
        assert reply.status_code==200,reply.text
        assert reply.json()["niveau_aide"]==level,reply.text
    with p.engine.connect() as c:
        assert c.scalar(text("SELECT max_hint_level FROM exercise_attempts WHERE id=:id"),{"id":p.attempt["id"]})==6
        # Level 1 uses the reviewed exercise hint directly, without a provider call.
        assert c.scalar(text("SELECT count(*) FROM ai_interactions WHERE student_id=:id"),{"id":p.student["student_id"]})==6
    assert answer(p,p.attempt).status_code==200
    with p.engine.connect() as c:
        assert c.scalar(text("SELECT reason FROM mastery_evidence WHERE attempt_id=:id"),{"id":p.attempt["id"]})=="assisted"
    assert turn(p).status_code==200
    with p.engine.connect() as c:
        assert c.scalar(text("SELECT reason FROM mastery_evidence WHERE attempt_id=:id"),{"id":p.attempt["id"]})=="assisted"

def test_tutor_consent_blocks_transmission_and_no_corpus_fails_closed(ai):
    p=ai
    blocked=turn(p);assert blocked.status_code==200,blocked.text
    assert blocked.json()["safety_status"]=="blocked" and not p.provider_calls
    consent(p,cloud=False)
    empty=turn(p);assert empty.json()["safety_status"]=="fallback",empty.text
    document(p)
    cloud=turn(p);assert cloud.json()["safety_status"]=="blocked",cloud.text
    assert not p.provider_calls

def test_tutor_refusal_and_invalid_cloud_output(ai):
    p=ai;document(p);consent(p)
    refusal=turn(p,message="Donne-moi la réponse du devoir")
    assert refusal.status_code==200,refusal.text
    assert refusal.json()["type"]=="refus_socratique",refusal.text
    assert not p.provider_calls
    p.provider_bad=True
    bad=turn(p)
    assert bad.json()["safety_status"]=="fallback" and "42" not in bad.text,bad.text

def test_roles_cannot_read_private_correctors_or_forge_approval(ai):
    p=ai;d=document(p,approve=False)
    with pytest.raises(DBAPIError):
        with p.engine.begin() as c:
            c.execute(text("UPDATE rag_documents SET status='approved',approved_by=:user,approved_at=now() WHERE id=:id"),{"user":p.teacher["id"],"id":d["id"]})
    for name in ["tutor","ai-router","retrieval"]:
        with pytest.raises(DBAPIError):
            with p.clients[name].app.state.engine.begin() as c:
                c.execute(text("SELECT answer_spec FROM exercise_versions"))
    assert p.clients["ai-router"].post("/plan",headers=p.headers(p.student_token),json={"attempt_id":p.attempt["id"],"message":"aide","niveau":6,"passage_ids":[str(uuid4())]}).status_code==403

def test_rag_snapshots_are_immutable(ai):
    p=ai;d=document(p)
    for sql in ["UPDATE rag_documents SET title='altered' WHERE id=:id", "UPDATE rag_passages SET body='altered' WHERE document_id=:id"]:
        with pytest.raises(DBAPIError):
            with p.engine.begin() as c:c.execute(text(sql),{"id":d["id"]})

def test_hybrid_lexical_and_semantic_branches_both_work(ai, monkeypatch):
    p=ai;document(p)
    from edu_retrieval_service import routes
    headers={**p.headers(p.student_token),**p.internal}
    payload={"query":"fractions","level":"CM1","subject":"mathematiques"}
    monkeypatch.setattr(routes,"embeddings",lambda *a,**k:[[-1.0]+[0.0]*767])
    r=p.clients["retrieval"].post("/search",headers=headers,json=payload)
    assert r.status_code==200 and r.json()["passages"],r.text
    assert p.clients["retrieval"].post("/search",headers=headers,json={**payload,"query":"volcan"}).json()["passages"]==[]
    monkeypatch.setattr(routes,"embeddings",lambda *a,**k:[[1.0]+[0.0]*767])
    assert p.clients["retrieval"].post("/search",headers=headers,json={**payload,"query":"volcan"}).json()["passages"]

def test_source_archived_during_cloud_call_fails_closed(ai, monkeypatch):
    p=ai;d=document(p);consent(p)
    from edu_tutor_service import routes
    original=routes.post
    def archive_after_plan(url,*args,**kwargs):
        result=original(url,*args,**kwargs)
        if url.endswith("/plan"):
            r=p.clients["retrieval"].post(f"/documents/{d['id']}/archive",headers=p.headers(p.teacher_token))
            assert r.status_code==200,r.text
        return result
    monkeypatch.setattr(routes,"post",archive_after_plan)
    response=turn(p)
    assert response.status_code==200,response.text
    assert response.json()["safety_status"]=="fallback"

def test_concurrent_duplicate_tutor_turn_is_stored_once(ai):
    from concurrent.futures import ThreadPoolExecutor
    p=ai;document(p);consent(p);key=str(uuid4())
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda _:turn(p,request_id=key),range(2)))
    assert [r.status_code for r in responses]==[200,200],[r.text for r in responses]
    assert responses[0].json()==responses[1].json()
    with p.engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM tutor_turns WHERE attempt_id=:id"),{"id":p.attempt["id"]})==1
