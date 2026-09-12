from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

Text = Annotated[str, Field(min_length=1, max_length=4000)]
Short = Annotated[str, Field(min_length=1, max_length=240)]
Kind = Literal["lesson", "teaching_sheet", "learning_sequence"]
Status = Literal["draft", "pending_review", "approved", "archived"]

class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True, str_strip_whitespace=True)

class Block(Model):
    kind: Literal["paragraph", "example", "activity", "question"]
    text: Text

class SequenceStep(Model):
    title: Short
    objective: Short
    duration_minutes: Annotated[int, Field(ge=1, le=180)]
    blocks: Annotated[list[Block], Field(min_length=1, max_length=20)]

class CM2Lesson(Model):
    subject: Literal["mathematiques","francais","sciences","histoire"] = "mathematiques"
    science: dict | None = None
    history: dict | None = None
    objective: Short
    prerequisites: Annotated[list[Short], Field(min_length=1, max_length=8)]
    discovery: Text
    explanation: Text
    method: Annotated[list[Short], Field(min_length=1, max_length=8)]
    worked_example: Annotated[list[Text], Field(min_length=1, max_length=8)]
    verified_equalities: Annotated[list[Short], Field(max_length=12)] = []
    common_errors: Annotated[list[Short], Field(min_length=1, max_length=8)]
    # The mini-question and both practice exercises have their own server-side attempts.
    check_exercise_id: UUID
    practice_exercise_ids: Annotated[list[UUID], Field(min_length=2, max_length=2)]

    @model_validator(mode="after")
    def checked(self):
        if self.subject=="sciences":
            from shared.science.catalogue import validate_science_metadata, BY_CHAPTER
            validate_science_metadata(self.science or {})
            if self.objective != BY_CHAPTER[self.science["chapter"]]["catalogue_objective"]:
                raise ValueError("Objectif scientifique incompatible")
        elif self.science is not None:
            raise ValueError("Métadonnées scientifiques incompatibles avec la matière")
        if self.subject=="histoire":
            from shared.history.catalogue import validate_history_metadata, BY_CHAPTER
            validate_history_metadata(self.history or {})
            if self.objective != BY_CHAPTER[self.history["chapter"]]["catalogue_objective"]:
                raise ValueError("Objectif historique incompatible")
        elif self.history is not None:
            raise ValueError("Métadonnées historiques incompatibles avec la matière")
        from shared.exercises.correctors import calculate
        if len(set([self.check_exercise_id, *self.practice_exercise_ids])) != 3:
            raise ValueError("Trois exercices distincts sont requis")
        for equality in self.verified_equalities:
            sides = equality.split("=")
            if len(sides) != 2 or calculate(sides[0]) != calculate(sides[1]):
                raise ValueError("Calcul de l'exemple incohérent")
        return self

class ContentBody(Model):
    # Plain text only: API never interprets markup or executes code.
    summary: Short
    objectives: Annotated[list[Short], Field(min_length=1, max_length=20)]
    blocks: Annotated[list[Block], Field(min_length=1, max_length=50)]
    steps: Annotated[list[SequenceStep], Field(max_length=20)] = []
    cm2: CM2Lesson | None = None

class VersionInput(Model):
    title: Short
    body: ContentBody
    competency_ids: Annotated[list[UUID], Field(min_length=1, max_length=20)]
    source_ids: Annotated[list[UUID], Field(min_length=1, max_length=20)]

    @model_validator(mode="after")
    def unique_links(self):
        if len(set(self.competency_ids)) != len(self.competency_ids) or len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("Références dupliquées")
        return self

class ContentInput(VersionInput):
    slug: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{1,159}$")]
    kind: Kind

    @model_validator(mode="after")
    def kind_body(self):
        check_structure(self.kind,self.body)
        return self

class NextVersionInput(VersionInput):
    base_version: Annotated[int, Field(ge=1)]

class VersionView(Model):
    id: UUID
    lesson_id: UUID
    version: int
    title: str
    body: dict
    status: Status
    kind: Kind
    editor_id: UUID | None
    review_round: int
    published_at: datetime | None
    created_at: datetime
    competency_ids: list[UUID]
    source_ids: list[UUID]

class ContentView(Model):
    id: UUID
    slug: str
    kind: Kind
    author_id: UUID
    version: int
    version_id: UUID
    title: str
    status: Status

class ReviewInput(Model):
    decision: Literal["approved", "rejected", "changes_requested"]
    reason_code: Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]{2,79}$")]
    confirmed_human_review: Literal[True]

class ReviewView(Model):
    id: UUID
    lesson_version_id: UUID
    reviewer_id: UUID
    decision: str
    reason_code: str
    review_round: int | None
    reviewed_at: datetime

class SourceInput(Model):
    title: Short
    url: HttpUrl
    publisher: Annotated[str, Field(min_length=1, max_length=200)]
    license: Annotated[str, Field(min_length=1, max_length=500)]
    checksum_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    retrieved_at: datetime

    @model_validator(mode="after")
    def aware_date(self):
        if self.retrieved_at.tzinfo is None or self.retrieved_at > datetime.now(self.retrieved_at.tzinfo):
            raise ValueError("Date de consultation passée et avec fuseau requise")
        if self.url.scheme != "https": raise ValueError("Source HTTPS requise")
        return self

class SourceView(Model):
    id: UUID
    title: str
    url: str
    publisher: str
    license: str
    checksum_sha256: str
    retrieved_at: datetime

def check_structure(kind,body):
    if (kind=="learning_sequence") != bool(body.steps):
        raise ValueError("Les étapes sont obligatoires uniquement pour une séquence")
