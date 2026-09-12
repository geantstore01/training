from copy import deepcopy
from datetime import date, datetime, timezone, timedelta
from uuid import uuid4
import pytest
from pydantic import ValidationError
from shared.service_loader import load_service
from shared.pedagogy import EvaluationLevel
import importlib

load_service("curriculum-service"); load_service("content-service")
curriculum=importlib.import_module("edu_curriculum_service.schemas")
content=importlib.import_module("edu_content_service.schemas")

def competency_payload():
    return dict(subject_id=uuid4(),domain_id=uuid4(),curriculum_level_id=uuid4(),code="TEST.1",
        label="Test synthétique",description="Objectif de test",objectives=["Comprendre"],common_errors=[],
        official_reference_url="https://www.education.gouv.fr/bo/2025",programme_version="TEST",
        effective_from="2026-09-01")

def body():
    return dict(summary="Résumé",objectives=["Comprendre"],blocks=[dict(kind="paragraph",text="Texte de test")])

def content_payload(kind="lesson"):
    return dict(title="Titre",body=body(),competency_ids=[str(uuid4())],source_ids=[str(uuid4())],slug="test-content",kind=kind)

@pytest.mark.parametrize("field,value",[
    ("objectives",[]),("code","invalid code"),("effective_until","2020-01-01"),
    ("official_reference_url","https://education.gouv.fr.evil.invalid/"),
    ("official_reference_url","http://education.gouv.fr/"),("tenant_id",str(uuid4()))])
def test_competency_validation(field,value):
    payload=competency_payload(); payload[field]=value
    with pytest.raises(ValidationError): curriculum.CompetencyInput.model_validate(payload)

def test_competency_dated_official_reference():
    item=curriculum.CompetencyInput.model_validate(competency_payload())
    assert item.effective_from==date(2026,9,1)
    assert str(item.official_reference_url).startswith("https://")

def test_six_exact_evaluation_levels():
    assert [x.value for x in EvaluationLevel]==["non_evalué","découverte","en_cours","fragile","maîtrisé","consolidé"]

@pytest.mark.parametrize("field,value",[("status","approved"),("editor_id",str(uuid4())),("published_at","2026-01-01"),("body",{"script":"alert(1)"}),("competency_ids",[]),("source_ids",[])])
def test_client_cannot_inject_state_or_unstructured_content(field,value):
    payload=content_payload(); payload[field]=value
    with pytest.raises(ValidationError): content.ContentInput.model_validate(payload)

def test_sequence_structure_and_duplicate_links():
    payload=content_payload("learning_sequence")
    with pytest.raises(ValidationError): content.ContentInput.model_validate(payload)
    payload["body"]["steps"]=[dict(title="Étape",objective="Lire",duration_minutes=15,blocks=body()["blocks"])]
    assert content.ContentInput.model_validate(payload).body.steps[0].duration_minutes==15
    payload["kind"]="lesson"
    with pytest.raises(ValidationError): content.ContentInput.model_validate(payload)
    payload=content_payload(); payload["source_ids"]*=2
    with pytest.raises(ValidationError): content.ContentInput.model_validate(payload)

@pytest.mark.parametrize("decision",["approved","rejected","changes_requested"])
def test_review_requires_explicit_human_confirmation(decision):
    data=dict(decision=decision,reason_code="PEDAGOGY_CHECKED",confirmed_human_review=True)
    assert content.ReviewInput.model_validate(data).decision==decision
    data["confirmed_human_review"]=False
    with pytest.raises(ValidationError): content.ReviewInput.model_validate(data)

def test_source_date_hash_and_https():
    data=dict(title="Source",url="https://example.org/",publisher="Test",license="Test",
        checksum_sha256="a"*64,retrieved_at=datetime.now(timezone.utc)-timedelta(days=1))
    content.SourceInput.model_validate(data)
    for field,value in [("checksum_sha256","bad"),("retrieved_at",datetime.now()),("url","http://example.org")]:
        with pytest.raises(ValidationError): content.SourceInput.model_validate({**data,field:value})
