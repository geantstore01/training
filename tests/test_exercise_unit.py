from copy import deepcopy
from datetime import datetime,timedelta,timezone
from decimal import Decimal
from fractions import Fraction
from uuid import uuid4
import importlib
import pytest
from pydantic import ValidationError
from shared.exercises.correctors import calculate,correct,grade,InvalidExpression
from shared.exercises.schemas import AnswerRule,Candidate,Responses
from shared.exercises.generation import GenerationInput,generate
from shared.exercises.pipeline import validate,STEPS
from shared.service_loader import load_service
load_service("assessment-service")
alg=importlib.import_module("edu_assessment_service.algorithms")

def generated(kind="short_text",template="arithmetic"):
    data=dict(template=template,kind=kind,competency_id=uuid4(),source_ids=[uuid4()],seed=42)
    if template=="chronology": data["events"]=[dict(label="Événement synthétique B",date="2001-01-01"),dict(label="Événement synthétique A",date="2000-01-01")]
    return generate(GenerationInput(**data))

@pytest.mark.parametrize("expression,expected",[("1/2",Fraction(1,2)),("0,5",Fraction(1,2)),("0.1+0.2",Fraction(3,10)),("(2+3)*4",20),("-3 × 2",-6),("12 ÷ 4",3),(".25",Fraction(1,4)),("1--2",3),("0007",7),(".05",Fraction(1,20)),("000.05",Fraction(1,20))])
def test_exact_arithmetic(expression,expected):
    assert calculate(expression)==expected

@pytest.mark.parametrize("expression",["__import__('os').system('id')","1/0","2**100000000","[1]","x+1","1e9","float('inf')","NaN","1//2","9"*200,"("*20+"1"+")"*20,"1<<8","True","0xFF","2%1"])
def test_math_parser_rejects_unsafe_or_unbounded_input(expression):
    with pytest.raises(InvalidExpression): calculate(expression)

@pytest.mark.parametrize("kind,template",[("multiple_choice","arithmetic"),("short_text","arithmetic"),("fill_blanks","arithmetic"),("step_problem","arithmetic"),("ordering","arithmetic"),("timeline","chronology"),("fill_blanks","agreement"),("multiple_choice","agreement")])
def test_generated_exercises_pass_ten_real_checks_and_self_correction(kind,template):
    c=generated(kind,template)
    report=validate(c,{p.competency_id for p in c.parts},set(c.source_ids))
    assert report.passed and len(report.checks)==10
    assert [x.name for x in report.checks]==STEPS
    assert all(r.correct for r in grade(c,{k:v.expected for k,v in c.answers.items()}))

def test_reproducible_generation_and_opaque_choice_keys():
    d=GenerationInput(template="arithmetic",kind="multiple_choice",competency_id=uuid4(),source_ids=[uuid4()],seed=123)
    a,b=generate(d),generate(d)
    assert a==b
    assert a.answers["main"].expected.startswith("o") and len(a.answers["main"].expected)==17
    assert a.parts[0].options[0].id in {x.id for x in a.parts[0].options}

def test_pipeline_rejects_missing_refs_wrong_keys_duplicate_options_and_invalid_math():
    c=generated("multiple_choice")
    assert not validate(c,set(),set()).passed
    c.parts[0].options[1].id=c.parts[0].options[0].id
    assert not validate(c,{p.competency_id for p in c.parts},set(c.source_ids)).passed
    c=generated();c.answers["main"].expected="1/0"
    report=validate(c,{p.competency_id for p in c.parts},set(c.source_ids))
    assert not report.passed and not report.checks[6].passed
    c=generated();c.answers={}
    assert not validate(c,{p.competency_id for p in c.parts},set(c.source_ids)).passed

def test_linguistic_rules_do_not_accept_orthographic_errors():
    spelling=AnswerRule(mode="spelling",expected="école")
    assert correct(spelling,"école")== (True,None)
    assert correct(spelling,"ecole")== (False,"ACCENT_ERROR")
    assert correct(spelling,"écolle")== (False,"SPELLING_ERROR")
    grammar=AnswerRule(mode="grammar",expected="petits",known_errors={"petit":"AGREEMENT_ERROR"})
    assert correct(grammar,"petit")== (False,"AGREEMENT_ERROR")
    assert correct(grammar,"petits")== (True,None)
    formulation=AnswerRule(mode="formulation",expected="La Terre tourne",variants=["Elle tourne"])
    assert correct(formulation,"  LA TERRE tourne ! ")== (True,None)
    assert correct(formulation,"Elle est immobile")== (False,"FORMULATION_NOT_RECOGNIZED")

def test_partial_missing_answers_unknown_keys_and_wrong_order():
    c=generated("step_problem")
    results=grade(c,{"subtotal":c.answers["subtotal"].expected})
    assert results[0].correct and results[1].error_code=="MISSING_ANSWER"
    with pytest.raises(ValueError): grade(c,{"not_a_part":"test"})
    c=generated("timeline","chronology")
    assert grade(c,{"main":list(reversed(c.answers["main"].expected))})[0].error_code=="ORDER_ERROR"

def test_responses_reject_client_scores_and_hint_counts():
    for key in ["score","max_hint_level","student_id","correct"]:
        with pytest.raises(ValidationError): Responses.model_validate({"answers":{},key:0})

def test_bkt_bayesian_values_forgetting_and_bounds():
    assert alg.bkt(0.2,True)==pytest.approx(0.57647,abs=0.00001)
    assert alg.bkt(0.2,False)==pytest.approx(0.12727,abs=0.00001)
    assert alg.bkt(0.9,True,90)<alg.bkt(0.9,True,0)
    for p in [0,0.1,0.5,0.9,1]:
        assert 0<alg.bkt(p,True)<1
        assert 0<alg.bkt(p,False)<1
    for p in [-1,2,float("nan")]:
        with pytest.raises(ValueError): alg.bkt(p,True)

def test_spacing_does_not_reward_early_repetition_and_resets_after_error():
    now=datetime(2026,1,1,tzinfo=timezone.utc)
    first=alg.schedule(now,True)
    assert first.interval_days==1
    assert alg.schedule(now+timedelta(hours=1),True,first)==first
    second=alg.schedule(first.due_at,True,first); assert second.interval_days==6
    third=alg.schedule(second.due_at,True,second); assert third.interval_days>6
    reset=alg.schedule(third.due_at,False,third)
    assert reset.interval_days==1 and reset.repetitions==0 and reset.ease_factor>=Decimal("1.3")

def test_mastery_levels_require_multiple_independent_observations():
    assert alg.mastery_level(.99,0,0).value=="non_evalué"
    assert alg.mastery_level(.99,1,0).value=="découverte"
    assert alg.mastery_level(.3,2,0).value=="fragile"
    assert alg.mastery_level(.7,4,1).value=="en_cours"
    assert alg.mastery_level(.9,5,2).value=="maîtrisé"
    assert alg.mastery_level(.97,8,3).value=="consolidé"
