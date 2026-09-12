from copy import deepcopy
from pathlib import Path
from uuid import uuid4
import json
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from shared.science.catalogue import COURSES, validate_science_metadata
from shared.science.engine import ScienceInput, observe, CASES
from shared.science.integrations import classquiz_payload, offline_command
from shared.science.retrieval import retrieve
from shared.exercises.cm2_pack import bind_exercises, bind_lesson
from shared.exercises.correctors import correct
from shared.exercises.coaching import correction, diagnose
from shared.exercises.schemas import PublicPrompt
from shared.service_loader import load_service

load_service("content-service")
from edu_content_service.schemas import ContentInput

@pytest.mark.parametrize("entry",COURSES,ids=lambda e:e["code"])
def test_bound_lessons_and_scientific_errors(entry):
    comp={"id":uuid4(),"code":entry["code"],"objectives":[entry["catalogue_objective"]]}
    sources=[uuid4()]
    lesson=ContentInput.model_validate(bind_lesson(entry,comp,sources,[uuid4() for _ in range(3)]))
    assert lesson.body.cm2.subject=="sciences"
    assert lesson.body.cm2.science["experiment"]["mode"]=="virtual"
    candidates=bind_exercises(entry,comp["id"],sources)
    assert len(candidates)==3
    for c in candidates:
        rule=c.answers["main"]
        assert correct(rule,rule.expected)==((False,"HUMAN_REVIEW") if rule.mode=="open_writing" else (True,None))
        assert correction(c,set())==[]
        assert "solution_steps" not in PublicPrompt(instruction=c.instruction,parts=c.parts).model_dump_json()
        for mistake in rule.misconceptions:
            assert diagnose(rule,mistake.response)["category"]==mistake.category
    altered=deepcopy(lesson.model_dump(mode="json"));altered["body"]["cm2"]["science"]["experiment"]["steps"]=["Allumer une flamme"]
    with pytest.raises(ValidationError):ContentInput.model_validate(altered)
    altered=deepcopy(entry["science"]);altered["source"]["url"]="https://example.com/invented"
    with pytest.raises(ValueError):validate_science_metadata(altered)

@pytest.mark.parametrize("setting,expected",[("ferme","on"),("ouvert","off"),("debranche","off")])
def test_circuit_topology(setting,expected):
    result=observe(ScienceInput(chapter="circuits",setting=setting,hypothesis="Je prévois une lampe allumée."))
    assert result["after"]==expected

def test_change_of_state_reversible_and_gas_invisible():
    melted=observe(ScienceInput(chapter="matiere",setting="fondre",hypothesis="La glace fondra."))
    frozen=observe(ScienceInput(chapter="matiere",setting="geler",hypothesis="L’eau deviendra glace."))
    assert (melted["before"],melted["after"])==(frozen["after"],frozen["before"])
    assert "invisible" in observe(ScienceInput(chapter="matiere",setting="evaporer",hypothesis="L’eau va changer."))["observation"]

@pytest.mark.parametrize("payload",[
    {"chapter":"circuits","setting":"secteur","hypothesis":"Brancher la prise"},
    {"chapter":"matiere","setting":"fondre","hypothesis":"   "},
    {"chapter":"matiere","setting":"fondre","hypothesis":"Je pense que","protocol":"chauffer"},
    {"chapter":"unknown","setting":"x","hypothesis":"Je pense que"},
])
def test_no_arbitrary_protocol_or_empty_prediction(payload):
    with pytest.raises(ValidationError):ScienceInput.model_validate(payload)

def test_classquiz_exports_have_one_right_answer_and_no_free_text_autograding():
    for entry in COURSES:
        payload=classquiz_payload(entry["chapter"])
        assert payload["public"] is False and len(payload["questions"])==2
        for q in payload["questions"]:
            assert q["type"]=="ABCD" and q["hide_results"]
            assert sum(a["right"] for a in q["answers"])==1
    assert offline_command("folder with spaces")[-1]=="folder with spaces"

def test_local_retrieval_filters_scope_and_matches_words():
    common={"status":"approved","level":"CM2","subject":"sciences"}
    rows=[{**common,"id":"water","body":"L’eau liquide devient solide."},
        {**common,"id":"substring","body":"Le solideur imaginaire."},
        {**common,"id":"draft","body":"solide","status":"draft"},
        {**common,"id":"wrong","body":"solide","subject":"francais"}]
    assert [p["id"] for p in retrieve("solide",rows)]==["water"]
    assert retrieve("antimatière",rows)==[]

def test_migration_reproducible_and_erasure_supported():
    from scripts.build_science_catalogue import build_science
    sql=Path("migrations/sql/0015_cm2_science_labs.sql").read_text(encoding="utf-8")
    assert sql==build_science()
    assert "ON DELETE CASCADE" in sql and "FORCE ROW LEVEL SECURITY" in sql
    assert "notebook_ciphertext BYTEA" in sql and "GRANT SELECT,DELETE ON science_runs TO edu_notification" in sql

def test_actual_service_requires_authentication():
    from fastapi import FastAPI
    load_service("assessment-service")
    from edu_assessment_service.science import router
    app=FastAPI();app.include_router(router)
    client=TestClient(app)
    assert client.get("/science/catalogue").status_code==401
    assert client.get(f"/science/notebook/{uuid4()}").status_code==401

def test_preview_notebook_attempt_and_explicit_correction():
    import scripts.preview_cm2_training as preview
    client=TestClient(preview.app)
    assert len(client.get("/api/assessment/science/catalogue").json())==4
    bad=client.post("/api/assessment/science/runs",json={"chapter":"circuits","setting":"secteur","hypothesis":"Essai","request_id":str(uuid4())})
    assert bad.status_code==422
    payload={"chapter":"circuits","setting":"ferme","hypothesis":"La boucle allumera la lampe.","request_id":str(uuid4())}
    run=client.post("/api/assessment/science/runs",json=payload).json()
    assert run["result"]["after"]=="on" and run["completed_at"] is None
    assert client.post("/api/assessment/science/runs",json=payload).json()["id"]==run["id"]
    response=client.post(f"/api/assessment/science/runs/{run['id']}/conclusion",json={"text":"La lampe s’allume car la boucle est fermée."})
    assert response.status_code==200 and response.json()["review_status"]=="to_review"
    assert client.get(f"/api/assessment/science/notebook/{uuid4()}").status_code==404
    session=client.post("/api/assessment/sessions",json={}).json()
    exercise=preview.uid("CM2-SCI-LAB-CIRCUITS0")
    attempt=client.post("/api/assessment/attempts",json={"session_id":session["id"],"exercise_version_id":exercise,"idempotency_key":str(uuid4())}).json()
    path=f"/api/assessment/attempts/{attempt['id']}/correction"
    assert client.get(path).status_code==409
    assert client.post(path,json={"explicit":True}).status_code==200
    assert preview.attempts[attempt["id"]]["view"]["submitted_at"] is None

def test_model_draft_cannot_change_sources_protocol_or_numeric_claims():
    from shared.science.generation import prepare,validate_model_draft
    entry=COURSES[0]
    comp={"id":uuid4(),"code":entry["code"],"objectives":[entry["catalogue_objective"]]}
    original,_=prepare("matiere",comp,[uuid4()],[uuid4() for _ in range(3)])
    accepted=validate_model_draft(json.dumps(original),original)
    assert accepted["human_review_required"] and accepted["status"]=="draft"
    for path,value in [("explanation","Chauffe au four à 300 degrés."),("objective","Observer des atomes.")]:
        changed=deepcopy(original);changed["body"]["cm2"][path]=value
        with pytest.raises(ValueError):validate_model_draft(json.dumps(changed),original)
    changed=deepcopy(original);changed["source_ids"]=[str(uuid4())]
    with pytest.raises(ValueError):validate_model_draft(json.dumps(changed),original)

def test_science_feedback_contract_accepts_evidence_based_categories():
    load_service("assessment-service")
    from edu_assessment_service.schemas import Feedback
    f=Feedback(part_id="main",outcome="à_revoir",message="Relis le protocole.",error_code="CHOICE_ERROR",misconception="protocole")
    assert f.misconception=="protocole"

def test_scoped_pdf_extraction_excludes_sixth_grade(monkeypatch):
    import hashlib
    from types import SimpleNamespace
    from shared.science import source_extract
    data=b"synthetic layout fixture"
    monkeypatch.setattr(source_extract,"SHA256",hashlib.sha256(data).hexdigest())
    class Page:
        def extract_text(self,visitor_text):
            for x,y,value in [(79,565,"CM : distinguer les états solide, liquide et gazeux."),(79,527,"Observer les changements d’état."),(323,565,"SIXIEME : mesurer des paliers."),(79,700,"HORS CADRE")]:
                visitor_text(value,[],[1,0,0,1,x,y],{},10)
    result=source_extract.cm_extract(data,SimpleNamespace(pages=[None,None,None,Page()]),[4])
    assert "solide" in result and "SIXIEME" not in result and "HORS CADRE" not in result
    with pytest.raises(ValueError):source_extract.cm_extract(b"changed",None,[4])

def test_ollama_generation_transport_with_explicit_network_double(monkeypatch):
    import httpx
    from shared.science.generation import generate_with_ollama,prepare
    entry=COURSES[0];sid=uuid4()
    comp={"id":uuid4(),"code":entry["code"],"objectives":[entry["catalogue_objective"]]}
    exercises=[uuid4() for _ in range(3)]
    original,_=prepare("matiere",comp,[sid],exercises)
    def handler(request):
        body=json.loads(request.content)
        assert body["model"]=="fixture-model" and body["stream"] is False
        return httpx.Response(200,json={"message":{"content":json.dumps(original)}})
    client=httpx.Client
    monkeypatch.setattr(httpx,"Client",lambda **kwargs:client(transport=httpx.MockTransport(handler),**kwargs))
    result=generate_with_ollama("matiere",comp,[sid],exercises,[{"source_id":str(sid),"body":"Les états de l’eau.","status":"approved","level":"CM2","subject":"sciences"}],"fixture-model")
    assert result["status"]=="draft" and result["human_review_required"]
