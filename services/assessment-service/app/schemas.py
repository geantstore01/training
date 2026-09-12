from datetime import datetime
from typing import Annotated,Literal
from uuid import UUID
from pydantic import Field
from shared.exercises.schemas import Model,Responses,PublicPrompt
from shared.pedagogy import EvaluationLevel

class SessionView(Model):
    id:UUID
    started_at:datetime
    ended_at:datetime|None
    status:str

class AttemptInput(Model):
    session_id:UUID
    exercise_version_id:UUID
    idempotency_key:UUID

class Feedback(Model):
    part_id:str
    outcome:Literal["réussi","à_revoir","à_relire"]
    error_code:str|None
    message:str
    misconception: Literal["place_value", "operation", "unit", "procedure","accord","conjugaison","homophone","lexique","classe_fonction","orthographe_lexicale","vocabulaire","observation","hypothese","protocole","raisonnement","conclusion","confusion","date","chronologie","personnage","lieu","cause","consequence","document"] | None = None
    categories: list[Literal["accord","conjugaison","homophone","lexique","orthographe_lexicale"]] = []

class CorrectionPart(Model):
    part_id: str
    steps: list[str]
    answer: str | None
    is_example: bool = False

class CorrectionRequest(Model):
    explicit: Literal[True]

class NextExercise(Model):
    exercise_version_id: UUID | None
    reason: Literal["bank_exhausted", "remediation", "consolidation", "progression"]

class Progress(Model):
    competency_id:UUID
    level:EvaluationLevel
    next_review_at:datetime|None

class Result(Model):
    feedback:list[Feedback]
    progress:list[Progress]
    message:str

class AttemptView(Model):
    id:UUID
    session_id:UUID
    exercise_version_id:UUID
    started_at:datetime
    submitted_at:datetime|None
    result:Result|None

class AttemptDetail(AttemptView):
    prompt: PublicPrompt
    responses:dict[str,str|list[str]]
    reasoning:dict[str,str] = {}

class HintView(Model):
    level:int
    text:str

class ErrorPattern(Model):
    competency_id:UUID
    error_code:str
    recurring:bool
    message:str

class AdaptiveCourse(Model):
    title:str
    focus:str
    explanation:str
    method:list[str]
    worked_example:list[str]
    exercise_version_id:UUID

class CourseProgress(Model):
    lesson_id:UUID
    competency_id:UUID
    title:str
    subject:str
    completed_exercises:int
    total_exercises:int
    progress_percent:int
    status:Literal["non_commencé","en_cours","passed","à_revoir","à_relire"]
    note:float|None
    last_attempt_at:datetime|None
    help_used:bool
    adapted_course:AdaptiveCourse|None
