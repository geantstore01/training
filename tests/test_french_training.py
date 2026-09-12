from copy import deepcopy
from uuid import uuid4
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from shared.exercises.french_pack import COURSES
from shared.exercises.cm2_pack import bind_exercises,bind_lesson
from shared.exercises.schemas import PublicPrompt,AnswerRule
from shared.exercises.correctors import correct
from shared.exercises.pipeline import validate
from shared.exercises.coaching import correction,diagnose
from shared.exercises.french import conjugate,dictation_feedback
from shared.service_loader import load_service

load_service("content-service")
from edu_content_service.schemas import ContentInput

def bank(code):
    entry=next(e for e in COURSES if e["code"]=="CM2-FR-"+code)
    return bind_exercises(entry,uuid4(),[uuid4()])

@pytest.mark.parametrize("entry",COURSES,ids=lambda e:e["code"])
def test_french_lessons_have_bound_context_and_private_answers(entry):
    comp={"id":uuid4(),"code":entry["code"],"objectives":[entry["catalogue_objective"]]}
    candidates=bind_exercises(entry,comp["id"],[uuid4()])
    lesson=ContentInput.model_validate(bind_lesson(entry,comp,[uuid4()],[uuid4() for _ in range(3)]))
    assert lesson.body.cm2.subject=="francais"
    assert len(candidates)==3 and len({c.instruction for c in candidates})==3
    for c in candidates:
        assert len(c.parts)==1
        assert len(c.hints)==2
        rule=c.answers["main"]
        assert correct(rule,rule.expected)==((False,"HUMAN_REVIEW") if rule.mode=="open_writing" else (True,None))
        assert correction(c,set())==[]
        assert correction(c,{"main"})[0]["is_example"]==(rule.mode=="open_writing")
        payload=PublicPrompt(instruction=c.instruction,parts=c.parts).model_dump_json()
        assert all(key not in payload for key in ("expected","solution_steps","conjugation_key","dictation_targets"))
    with pytest.raises(ValueError):
        bind_lesson(entry,{**comp,"objectives":["Notion absente"]},[uuid4()],[uuid4() for _ in range(3)])

def test_checked_import_records_disagreements_and_preserves_accents():
    data=json.loads(Path("shared/exercises/data/french_verbs.json").read_text(encoding="utf-8"))
    assert len(data["forms"])==47
    assert len(data["excluded_disagreements"])==25
    rule=bank("PRESENT")[2].answers["main"]
    assert rule.expected=="êtes"
    assert correct(rule,"etes")== (False,"ACCENT_ERROR")
    assert correct(rule,"ÊTES")== (True,None)
    assert correct(rule,"sont")== (False,"CONJUGATION_ERROR")
    with pytest.raises(ValueError):conjugate("chanter|subjonctif|present|0")
    c=bank("PASSE-COMPOSE")[0];c.answers["main"].expected="a chanté"
    assert not validate(c,{c.parts[0].competency_id},set(c.source_ids)).passed

def test_dictation_categories_and_uncertain_alignment():
    rule=bank("DICTEE-RELECTURE")[2].answers["main"]
    result=dictation_feedback(rule,"Les enfants chante dans le jardain.")
    assert result["categories"]==["conjugaison","orthographe_lexicale"]
    assert correct(rule,"Les enfants chante dans le jardain.")== (False,"DICTATION_ERROR")
    assert correct(rule,"Les petits enfants chantent dans le jardin.")== (False,"HUMAN_REVIEW")
    assert correct(rule,["bad"] )== (False,"INVALID_FORMAT")
    assert correct(rule,"les enfants chantent dans le jardin")== (True,None)
    # Categories are editorial metadata, not an invented diagnosis from arbitrary words.
    categories=["accord","conjugaison","homophone","lexique","orthographe_lexicale"]
    five=AnswerRule(mode="dictation",expected="un deux trois quatre cinq",dictation_targets=[{"position":i,"category":c,"hint":"Relis ce mot."} for i,c in enumerate(categories)])
    assert dictation_feedback(five,"a b c d e")["categories"]==categories

def test_class_function_and_homophones_have_authored_clues():
    assert diagnose(bank("NATURES")[0].answers["main"],"o1")["category"]=="classe_fonction"
    assert diagnose(bank("HOMOPHONES")[0].answers["main"],"à")["category"]=="homophone"

def test_preview_correction_requires_attempt_or_explicit_french_request():
    from scripts.preview_cm2_training import app,uid,attempts,sessions
    attempts.clear();sessions.clear()
    with TestClient(app) as client:
        sid=client.post("/api/assessment/sessions",json={}).json()["id"]
        def start(code):return client.post("/api/assessment/attempts",json={"session_id":sid,"exercise_version_id":uid(code+"0"),"idempotency_key":str(uuid4())}).json()["id"]
        aid=start("CM2-FR-PRESENT");url=f"/api/assessment/attempts/{aid}/correction"
        assert client.get(url).status_code==409
        assert client.post(url,json={}).status_code==409
        assert client.post(url,json={"explicit":True}).json()[0]["answer"]=="suis"
        assert attempts[aid]["level"]>=1
        mid=start("CM2-MATH-DECIMAUX")
        assert client.post(f"/api/assessment/attempts/{mid}/correction",json={"explicit":True}).status_code==409
        wid=start("CM2-FR-ECRIT-REDIGER")
        reply=client.post(f"/api/assessment/attempts/{wid}/submit",json={"answers":{"main":"Sami pousse la porte de la bibliothèque."},"reasoning":{"main":"Je présente Sami et le lieu."}})
        assert reply.json()["result"]["feedback"][0]["outcome"]=="à_relire"
        assert client.get(f"/api/assessment/attempts/{wid}/correction").json()[0]["is_example"]

def test_single_migration_head_and_reproducible_seed():
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from scripts.build_french_catalogue import build
    assert ScriptDirectory.from_config(Config("alembic.ini")).get_heads()==["0018_course_progress_read"]
    assert Path("migrations/sql/0012_cm2_french_training.sql").read_text(encoding="utf-8")==build()
    assert Path("migrations/sql/0013_cm2_french_workshops.sql").read_text(encoding="utf-8")==build(COURSES[18:])

@pytest.mark.parametrize("contexts,allowed",[([("francais","CM2")],True),([("mathematiques","CM2")],True),([("francais","CM1")],False),([("mathematiques","CM1")],False),([],False),([("francais","CM2"),("mathematiques","CM2")],True)])
def test_service_explicit_correction_checks_curriculum(monkeypatch,contexts,allowed):
    from contextlib import contextmanager
    from types import SimpleNamespace as NS
    from fastapi import HTTPException
    from shared.service_loader import load_service
    load_service("assessment-service")
    from edu_assessment_service import routes
    from edu_assessment_service.schemas import CorrectionRequest
    c=bank("PRESENT")[0]
    a=NS(id=uuid4(),exercise_version_id=uuid4(),submitted_at=None,max_hint_level=0)
    fake=NS(execute=lambda q:NS(all=lambda:contexts),get=lambda *args:None)
    @contextmanager
    def scope(*args):yield fake
    monkeypatch.setattr(routes,"tenant_session",scope)
    monkeypatch.setattr(routes,"attempt_for_write",lambda *args:(None,a))
    monkeypatch.setattr(routes,"candidate",lambda *args:c)
    monkeypatch.setattr(routes,"audit",lambda *args:None)
    monkeypatch.setattr(routes,"enforce_rate",lambda *args:None)
    principal=NS(user_id=uuid4(),school_id=uuid4())
    request=NS(app=NS(state=NS(engine=None)))
    if allowed:
        assert routes.requested_correction(a.id,CorrectionRequest(explicit=True),request,principal)[0]["answer"]=="suis"
        assert a.max_hint_level==1
        # A submitted attempt stays immutable even when its correction is requested again.
        a.submitted_at="already submitted";a.max_hint_level=0
        routes.requested_correction(a.id,CorrectionRequest(explicit=True),request,principal)
        assert a.max_hint_level==0
    else:
        with pytest.raises(HTTPException) as exc:routes.requested_correction(a.id,CorrectionRequest(explicit=True),request,principal)
        assert exc.value.status_code==409 and a.max_hint_level==0

def test_human_review_preserves_mastery_and_existing_review_schedule():
    from types import SimpleNamespace as NS
    from datetime import datetime,timedelta,timezone
    from decimal import Decimal
    from shared.exercises.correctors import grade
    load_service("assessment-service")
    from edu_assessment_service.routes import update_mastery
    now=datetime.now(timezone.utc)
    old=NS(probability=Decimal("0.7"),last_assessed_at=now-timedelta(days=1),evidence_count=7,evaluation_level="en_apprentissage")
    item=NS(due_at=now+timedelta(days=8),interval_days=8,ease_factor=2.5,repetitions=3)
    returned=iter([old,None,item]);added=[]
    session=NS(scalar=lambda q:next(returned),add=added.append)
    c=bank("ECRIT-REDIGER")[0]
    student=NS(id=uuid4(),tenant_id=uuid4())
    a=NS(id=uuid4(),exercise_version_id=uuid4(),max_hint_level=0)
    update_mastery(session,student,a,c,grade(c,{"main":"Un texte personnel qui répond à la consigne."}),now)
    assert old.probability==Decimal("0.7") and old.evidence_count==7
    assert item.due_at==now+timedelta(days=8) and item.repetitions==3 and item.ease_factor==2.5
    assert added[-1].reason=="unrecognized" and not added[-1].applied
