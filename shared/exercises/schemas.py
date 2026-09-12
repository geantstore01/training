from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

Key = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,39}$")]
Short = Annotated[str, Field(min_length=1,max_length=240)]
Text = Annotated[str, Field(min_length=1,max_length=1500)]
Kind = Literal["multiple_choice","fill_blanks","short_text","step_problem","ordering","timeline"]
class Model(BaseModel):
    model_config=ConfigDict(extra="forbid",from_attributes=True,str_strip_whitespace=True)

class Option(Model):
    id: Key
    label: Short

class FractionVisual(Model):
    kind: Literal["fraction"]
    parts: Annotated[int,Field(ge=2,le=12)]
    selected: Annotated[int,Field(ge=0,le=12)]
    @model_validator(mode="after")
    def check(self):
        if self.selected>self.parts:raise ValueError("Trop de parts colorées")
        return self

class GridVisual(Model):
    kind: Literal["grid"]
    rows: Annotated[int,Field(ge=1,le=12)]
    columns: Annotated[int,Field(ge=1,le=12)]

class Part(Model):
    id: Key
    question: Text
    competency_id: UUID
    response_type: Literal["number","text","choice","ordering"]
    options: Annotated[list[Option],Field(max_length=12)] = []
    visual: Annotated[FractionVisual|GridVisual,Field(discriminator="kind")] | None = None

class AnswerRule(Model):
    mode: Literal["number","spelling","grammar","formulation","choice","ordering","open_writing","dictation"]
    decimal_only: bool = False
    diagram_measure: Literal["fraction","area","perimeter"] | None = None
    expected: Annotated[str,Field(min_length=1,max_length=240)] | Annotated[list[Key],Field(min_length=2,max_length=12)]
    variants: Annotated[list[Short],Field(max_length=10)] = []
    known_errors: dict[Short,Literal["SPELLING_ERROR","ACCENT_ERROR","AGREEMENT_ERROR","CONJUGATION_ERROR","CALCULATION_ERROR","ORDER_ERROR"]] = {}
    # Private editorial material, never included in PublicPrompt.
    solution_steps: Annotated[list[Text],Field(max_length=12)] = []
    verified_equalities: Annotated[list[Short],Field(max_length=12)] = []
    misconceptions: Annotated[list["Misconception"],Field(max_length=12)] = []
    conjugation_key: Short | None = None
    dictation_targets: Annotated[list["DictationTarget"],Field(max_length=40)] = []

class DictationTarget(Model):
    position: Annotated[int,Field(ge=0,le=39)]
    category: Literal["accord","conjugaison","homophone","lexique","orthographe_lexicale"]
    hint: Text

class Misconception(Model):
    response: Short
    category: Literal["place_value", "operation", "unit", "procedure","accord","conjugaison","homophone","lexique","classe_fonction","orthographe_lexicale","vocabulaire","observation","hypothese","protocole","raisonnement","conclusion","confusion","date","chronologie","personnage","lieu","cause","consequence","document"]
    hint: Text

class HintInput(Model):
    level: Annotated[int,Field(ge=1,le=6)]
    text: Text

class Candidate(Model):
    kind: Kind
    instruction: Text
    parts: Annotated[list[Part],Field(min_length=1,max_length=12)]
    answers: dict[Key,AnswerRule]
    source_ids: Annotated[list[UUID],Field(min_length=1,max_length=12)]
    difficulty: Annotated[int,Field(ge=1,le=5)] = 1
    hints: Annotated[list[HintInput],Field(max_length=6)] = []

class PublicPrompt(Model):
    instruction: str
    parts: list[Part]

class Check(Model):
    step: int
    name: str
    passed: bool

class PipelineReport(Model):
    version: Literal["controlled-v1"] = "controlled-v1"
    passed: bool
    checks: list[Check]

class Responses(Model):
    answers: dict[Key, Annotated[str,Field(max_length=512)] | Annotated[list[Key],Field(max_length=12)]]
    reasoning: dict[Key, Annotated[str,Field(max_length=1000)]] = {}

class PartResult(Model):
    part_id: str
    correct: bool
    error_code: str | None
