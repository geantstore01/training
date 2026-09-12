from datetime import date
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator
from shared.pedagogy import EvaluationLevel

Text = Annotated[str, Field(min_length=1, max_length=2000)]
Code = Annotated[str, Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{1,79}$")]

class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True, str_strip_whitespace=True)

class SubjectView(Model):
    id: UUID
    code: str
    name: str

class LevelView(Model):
    id: UUID
    code: Literal["CM1", "CM2"]
    cycle: Literal[3]

class DomainInput(Model):
    subject_id: UUID
    code: Code
    name: Annotated[str, Field(min_length=1, max_length=200)]

class DomainView(DomainInput):
    id: UUID

class CompetencyInput(Model):
    subject_id: UUID
    domain_id: UUID
    curriculum_level_id: UUID
    code: Code
    label: Annotated[str, Field(min_length=1, max_length=240)]
    description: Text
    objectives: Annotated[list[Text], Field(min_length=1, max_length=20)]
    common_errors: Annotated[list[Text], Field(max_length=20)] = []
    official_reference_url: HttpUrl
    programme_version: Annotated[str, Field(min_length=1, max_length=80)]
    effective_from: date
    effective_until: date | None = None

    @field_validator("official_reference_url")
    @classmethod
    def official_source(cls, value):
        if value.scheme != "https" or not any(value.host == domain or value.host.endswith("."+domain)
                for domain in ("education.gouv.fr", "legifrance.gouv.fr")):
            raise ValueError("Une référence officielle HTTPS est requise")
        return value

    @model_validator(mode="after")
    def dates(self):
        if self.effective_until is not None and self.effective_until < self.effective_from:
            raise ValueError("Période invalide")
        return self

class CompetencyView(Model):
    id: UUID
    subject_id: UUID
    domain_id: UUID | None
    curriculum_level_id: UUID
    code: str
    label: str
    description: str
    objectives: list[str]
    common_errors: list[str]
    official_reference_url: str
    programme_version: str
    effective_from: date
    effective_until: date | None

class EdgeInput(Model):
    prerequisite_id: UUID

class EdgeView(Model):
    competency_id: UUID
    prerequisite_id: UUID

class GraphNode(Model):
    competency: CompetencyView
    distance: int
    evaluation_level: EvaluationLevel | None = None

class GraphView(Model):
    root_id: UUID
    direction: Literal["upstream", "downstream"]
    max_depth: int
    truncated: bool
    nodes: list[GraphNode]
    edges: list[EdgeView]

class EvaluationView(Model):
    code: EvaluationLevel
    label: str
