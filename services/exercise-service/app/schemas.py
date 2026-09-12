from datetime import datetime
from typing import Annotated,Literal
from uuid import UUID
from pydantic import Field
from shared.exercises.schemas import Candidate,Model,PipelineReport,PublicPrompt,Responses
from shared.exercises.generation import GenerationInput

class CreateInput(Model):
    slug: Annotated[str,Field(pattern=r"^[a-z0-9][a-z0-9-]{1,159}$")]
    candidate: Candidate

class GenerateInput(Model):
    slug: Annotated[str,Field(pattern=r"^[a-z0-9][a-z0-9-]{1,159}$")]
    generation: GenerationInput

class VersionInput(Model):
    base_version: Annotated[int,Field(ge=1)]
    candidate: Candidate

class ExerciseView(Model):
    id: UUID
    exercise_id: UUID
    version: int
    kind: str
    prompt: PublicPrompt
    difficulty: int
    status: str
    published_at: datetime|None

class EditorialView(ExerciseView):
    candidate: Candidate
    pipeline: PipelineReport

class ReviewInput(Model):
    decision: Literal["approved","rejected","changes_requested"]
    reason_code: Annotated[str,Field(pattern=r"^[A-Z][A-Z0-9_]{2,79}$")]
    confirmed_human_review: Literal[True]
