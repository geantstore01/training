from pathlib import Path
from uuid import uuid4
import pytest
from pydantic import ValidationError
from shared.exercises.cm2_pack import COURSES,bind_exercises
from shared.exercises.schemas import FractionVisual,GridVisual,PublicPrompt
from shared.exercises.correctors import correct
from shared.exercises.pipeline import validate

def bank(code):return bind_exercises(next(c for c in COURSES if c["code"]=="CM2-MATH-"+code),uuid4(),[uuid4()])

def test_diagram_and_expected_answer_must_agree():
    c=bank("FRACTIONS-DECIMALES")[0]
    assert correct(c.answers["main"],"0,3")== (True,None)
    assert correct(c.answers["main"],"3/10")== (False,"INVALID_NUMBER")
    assert correct(c.answers["main"],"0,03")== (False,"CALCULATION_ERROR")
    c.parts[0].visual.selected=4
    assert not validate(c,{c.parts[0].competency_id},set(c.source_ids)).passed
    g=bank("RECTANGLES-COMPARER")[0]
    assert correct(g.answers["main"],"12")== (True,None)
    g.parts[0].visual.columns=5
    assert not validate(g,{g.parts[0].competency_id},set(g.source_ids)).passed

def test_public_diagrams_do_not_publish_private_measure_or_answer():
    c=bank("RECTANGLES-COMPARER")[1]
    public=PublicPrompt(instruction=c.instruction,parts=c.parts).model_dump_json()
    assert '"rows":2' in public and '"columns":5' in public
    assert "expected" not in public and "diagram_measure" not in public
    with pytest.raises(ValidationError):FractionVisual(kind="fraction",parts=4,selected=5)
    with pytest.raises(ValidationError):GridVisual(kind="grid",rows=1000,columns=4)

def test_ordered_decimals_and_generated_migration():
    c=bank("RANGER-DECIMAUX")[1]
    assert correct(c.answers["main"],["n0","n1","n2"])==(True,None)
    assert correct(c.answers["main"],["n1","n0","n2"])==(False,"ORDER_ERROR")
    from scripts.build_math_workshops import build_math
    assert Path("migrations/sql/0014_cm2_math_workshops.sql").read_text(encoding="utf-8")==build_math()
