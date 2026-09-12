from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, SecretStr


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Plan(Strict):
    action: Literal["reformuler", "identifier", "representer", "relier", "decomposer", "verifier", "amorcer"]
    source_id: UUID
    erreur: Literal["non_determinee", "comprehension", "organisation", "verification"]


class PlanRequest(Strict):
    attempt_id: UUID
    message: SecretStr = Field(min_length=1, max_length=1500)
    niveau: int = Field(ge=0, le=6)
    passage_ids: list[UUID] = Field(min_length=1, max_length=3)


class TutorRequest(Strict):
    attempt_id: UUID
    request_id: UUID
    message: SecretStr = Field(min_length=1, max_length=1500)
    plus_aide: bool = False


class TutorResponse(Strict):
    message_pedagogique: str
    type: Literal["questionnement", "indice", "methode_partielle", "refus_socratique", "indisponible", "protection"]
    niveau_aide: int = Field(ge=0, le=6)
    aide_max: int = Field(default=6, ge=0, le=6)
    question_suivante: str | None
    erreur_detectee: Literal["non_determinee", "comprehension", "organisation", "verification"]
    action_recommandee: Literal["reformuler", "identifier", "representer", "relier", "decomposer", "verifier", "amorcer", "reessayer", "demander_adulte"]
    safety_status: Literal["safe", "blocked", "fallback"]


class SearchRequest(Strict):
    history_chapter: Literal["ferry","republique","industrie","guerre-14","guerre-39","europe"] | None = None
    query: SecretStr = Field(min_length=2, max_length=500)
    level: Literal["CM1", "CM2"]
    subject: Literal["francais", "mathematiques", "histoire", "sciences"]
    limit: int = Field(default=3, ge=1, le=8)


class Passage(Strict):
    id: UUID
    document_id: UUID
    text: str
    url: str
    title: str
    level: str
    subject: str
    version: int


class SearchResponse(Strict):
    passages: list[Passage]
    embedding_model: str
