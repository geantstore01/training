"""Executable pedagogy checks. These tests do not claim PostgreSQL integration."""
from copy import deepcopy
from fractions import Fraction
from uuid import uuid4
import pytest
from pydantic import ValidationError
from shared.exercises.cm2_pack import COURSES, bind_exercises, bind_lesson
from shared.exercises.coaching import correction, diagnose, display_number
from shared.exercises.adaptive import choose_next
from shared.exercises.correctors import calculate, grade
from shared.exercises.pipeline import validate
from shared.exercises.schemas import PublicPrompt
from shared.ai.cm2_policy import INSUFFICIENT_CONTEXT, CM2_TEACHER_PROMPT
from shared.ai.pedagogy import render
from shared.service_loader import load_service

load_service("content-service")
from edu_content_service.schemas import ContentInput


@pytest.mark.parametrize("entry",COURSES,ids=lambda entry:entry["code"])
def test_entire_pack_is_executable_and_never_exposes_solutions(entry):
    competency_id,source=uuid4(),uuid4()
    candidates=bind_exercises(entry,competency_id,[source])
    assert len(candidates)==3
    assert len({c.parts[0].question for c in candidates})==3
    for candidate in candidates:
        assert all(result.correct for result in grade(candidate,{"main":candidate.answers["main"].expected}))
        assert [hint.level for hint in candidate.hints]==[1,2]
        assert correction(candidate,set())==[]
        corrected=correction(candidate,{"main"})
        assert len(corrected)==1 and corrected[0]["answer"] is not None
        public=PublicPrompt(instruction=candidate.instruction,parts=candidate.parts).model_dump_json()
        for private in ("solution_steps","expected","misconceptions","verified_equalities"):
            assert private not in public
        rule=candidate.answers["main"]
        assert diagnose(rule,rule.expected) is None
        for mistake in rule.misconceptions:
            assert not grade(candidate,{"main":mistake.response})[0].correct
            assert diagnose(rule,mistake.response)["category"]==mistake.category
    context={"id":competency_id,"code":entry["code"],"objectives":[entry["catalogue_objective"]] if entry.get("catalogue_objective") else ["Objectif du contexte 0","Objectif du contexte 1"]}
    lesson=ContentInput.model_validate(bind_lesson(entry,context,[source],[uuid4() for _ in range(3)]))
    assert lesson.body.cm2.objective in context["objectives"]
    assert lesson.body.cm2.worked_example
    assert "solution_steps" not in lesson.model_dump_json()


def test_incoherent_arithmetic_is_rejected_in_examples_and_solutions():
    entry=deepcopy(COURSES[0]);entry["verified_equalities"]=["2+2=5"]
    payload=bind_lesson(entry,{"id":uuid4(),"code":entry["code"],"objectives":["a","b"]},[uuid4()],[uuid4() for _ in range(3)])
    with pytest.raises(ValidationError): ContentInput.model_validate(payload)
    candidate=bind_exercises(COURSES[0],uuid4(),[uuid4()])[0]
    candidate.answers["main"].verified_equalities=["2+2=5"]
    assert not validate(candidate,{candidate.parts[0].competency_id},set(candidate.source_ids)).passed


def test_context_required_and_duplicate_exercises_rejected():
    with pytest.raises(ValueError): bind_lesson(COURSES[0],{"code":"COLLEGE"},[],[])
    identifier=uuid4()
    payload=bind_lesson(COURSES[0],{"id":uuid4(),"code":COURSES[0]["code"],"objectives":["a","b"]},[uuid4()],[identifier]*3)
    with pytest.raises(ValidationError): ContentInput.model_validate(payload)
    assert render(0,unavailable=True).message_pedagogique==INSUFFICIENT_CONTEXT
    assert "15." in CM2_TEACHER_PROMPT


def test_adaptation_distinguishes_failure_help_and_transfer_without_repeats():
    bank=[{"id":str(i),"difficulty":i} for i in range(1,6)]
    assert choose_next(bank,{"3"},3,False)=={"exercise_version_id":"2","reason":"remediation"}
    assert choose_next(bank,{"2"},2,True)=={"exercise_version_id":"3","reason":"progression"}
    assert choose_next(bank,{"1"},2,True,True)=={"exercise_version_id":"2","reason":"consolidation"}
    assert choose_next(bank,{str(i) for i in range(1,6)},2,True)["exercise_version_id"] is None


def test_decimal_feedback_and_fraction_feedback_remain_exact():
    assert display_number(Fraction(61,10))=="6,1"
    assert display_number(Fraction(3,8),True)=="3/8"
    assert Fraction(display_number(Fraction(1,2**40)).replace(",","."))==Fraction(1,2**40)


def test_partial_attempt_only_reveals_attempted_part():
    candidate=bind_exercises(COURSES[0],uuid4(),[uuid4()])[0]
    other=deepcopy(candidate.parts[0]);other.id="other"
    candidate.parts.append(other);candidate.answers["other"]=deepcopy(candidate.answers["main"])
    assert [part["part_id"] for part in correction(candidate,{"main"})]==["main"]
