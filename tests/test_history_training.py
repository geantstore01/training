import csv
from copy import deepcopy
import io
import json
from pathlib import Path
from uuid import uuid4
import pytest
from shared.history.catalogue import COURSES, BY_CHAPTER, public_catalogue, validate_history_metadata
from shared.history.schemas import HistoryMetadata
from shared.history.generation import prepare, validate_model_draft
from shared.history.ingestion import history_chunks, extract_entities
from shared.history.integrations import classquiz_payload, interactive_quiz_payload, quizli_csv
from shared.exercises.cm2_pack import bind_exercises
from shared.exercises.schemas import PublicPrompt
from shared.exercises.correctors import grade

@pytest.mark.parametrize("entry",COURSES,ids=lambda e:e["chapter"])
def test_course_bound_to_context_and_private_solutions(entry):
    comp=dict(id=str(uuid4()),code=entry["code"],objectives=[entry["catalogue_objective"]])
    result=prepare(entry["chapter"],comp,[uuid4()],[uuid4(),uuid4(),uuid4()])
    assert result["status"]=="draft" and result["human_review_required"]
    for c in bind_exercises(entry,comp["id"],[uuid4()]):
        public=PublicPrompt(instruction=c.instruction,parts=c.parts).model_dump_json()
        assert all(k not in public for k in ("expected","solution_steps","misconceptions"))
        response=grade(c,{"main":c.answers["main"].expected})[0]
        if c.answers["main"].mode=="open_writing":assert response.error_code=="HUMAN_REVIEW"
        else:assert response.correct
    with pytest.raises(ValueError):prepare(entry["chapter"],{**comp,"objectives":["Inventer une autre notion"]},[uuid4()],[uuid4(),uuid4(),uuid4()])

@pytest.mark.parametrize("mutation",["date","source","figure","order","document"])
def test_no_anachronism_or_fake_document(mutation):
    meta=deepcopy(BY_CHAPTER["ferry"]["history"])
    if mutation=="date":meta["timeline"][0]["year"]=1905
    if mutation=="source":meta["sources"][0]["url"]="https://example.invalid"
    if mutation=="figure":meta["figures"][0]["died"]=1870
    if mutation=="order":meta["timeline"].reverse()
    if mutation=="document":meta["document"]["content"]="Une fausse citation."
    with pytest.raises(ValueError):validate_history_metadata(meta)

def test_outline_has_no_unreviewed_history_or_answer_key():
    data=public_catalogue()
    assert len(data["themes"])==3 and len(data["chapters"])==6
    assert "expected" not in json.dumps(data) and "document" not in json.dumps(data)
    assert BY_CHAPTER["guerre-39"]["history"]["sensitive"]

def test_deeptutor_chunking_has_bounded_coverage_and_provenance():
    raw=("En 1882, Jules Ferry porte une loi. Ã€ Paris, des textes sont discutÃ©s.\n\n"*90)
    parts=history_chunks(raw)
    assert len(parts)>1 and all(0<len(p)<=1600 for p in parts)
    assert parts[0].startswith(raw[:50]) and parts[-1].endswith(raw[-50:])
    entities=extract_entities(raw,"ferry")
    assert entities["figures"]==["Jules Ferry"] and entities["places"]==["Paris"]
    assert not entities["event_candidates"]  # a year alone proves no event
    assert all(raw[d["start"]:d["end"]]==d["value"] for d in entities["dates"])

@pytest.mark.parametrize("entry",COURSES,ids=lambda e:e["chapter"])
def test_real_interoperability_contracts(entry):
    key=entry["chapter"]
    assert classquiz_payload(key)["public"] is False
    quiz=interactive_quiz_payload(key)
    assert all(q["correct_answer"] in q["options"] for q in quiz["questions"])
    assert len(list(csv.reader(io.StringIO(quizli_csv(key)))))==len(quiz["questions"])

def test_model_cannot_change_dates_or_metadata():
    entry=BY_CHAPTER["ferry"]
    original=prepare("ferry",dict(id=str(uuid4()),code=entry["code"],objectives=[entry["catalogue_objective"]]),[uuid4()],[uuid4(),uuid4(),uuid4()])["lesson"]
    assert validate_model_draft(json.dumps(original),original)["human_review_required"]
    edited=deepcopy(original);edited["body"]["cm2"]["explanation"]+=" En 1914, tout change."
    with pytest.raises(ValueError):validate_model_draft(json.dumps(edited),original)

def test_reproducible_migration_and_version_scope():
    from scripts.build_history_catalogue import build_history
    assert Path("migrations/sql/0016_cm2_history_workshops.sql").read_text(encoding="utf-8")==build_history()
    assert "2027-08-31" in build_history()

def test_history_catalogue_requires_authentication():
    from shared.service_loader import load_service
    load_service("assessment-service")
    from edu_assessment_service.main import build_app
    from fastapi.testclient import TestClient
    assert TestClient(build_app()).get("/history/catalogue").status_code==401


def test_wrong_history_choice_has_serializable_diagnostic():
    from shared.service_loader import load_service
    load_service("assessment-service")
    from edu_assessment_service.schemas import Feedback
    from shared.exercises.coaching import diagnose
    for entry in COURSES:
        for c in bind_exercises(entry,uuid4(),[uuid4()]):
            rule=c.answers["main"]
            if rule.mode=="choice":
                wrong=next(o.id for o in c.parts[0].options if o.id!=rule.expected)
                diagnostic=diagnose(rule,wrong)
                assert diagnostic
                Feedback(part_id="main",outcome="à_revoir",error_code="CHOICE_ERROR",message=diagnostic["message"],misconception=diagnostic["category"])
