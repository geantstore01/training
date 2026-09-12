from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class Source(Model):
    title: str = Field(min_length=3, max_length=240)
    url: HttpUrl
    page: int | None = Field(default=None, ge=1)
    section: str = Field(min_length=3, max_length=240)

class Event(Model):
    id: str
    year: int = Field(ge=1700, le=2027)
    date: str
    title: str
    explanation: str
    source: Source

class Figure(Model):
    name: str
    born: int
    died: int
    role: str
    remember: str
    confusion: str
    event_ids: list[str]
    source: Source

class Place(Model):
    name: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    importance: str
    source: Source

class Document(Model):
    type: Literal["texte de loi", "synthèse pédagogique institutionnelle"]
    title: str
    date: str
    origin: str
    context: str
    content: str
    presentation: Literal["court extrait", "reformulation"]
    shows: str
    limits: str
    questions: list[str] = Field(min_length=3, max_length=3)
    source: Source

class Vocabulary(Model):
    word: str
    definition: str

class HistoryMetadata(Model):
    chapter: str
    theme: Literal["republique", "industrie", "guerres-europe"]
    period: str
    programme_version: Literal["histoire-2020-cm2-2026"]
    sensitive: bool
    essential_question: str
    timeline: list[Event] = Field(min_length=2, max_length=10)
    figures: list[Figure] = Field(max_length=6)
    places: list[Place] = Field(min_length=1, max_length=8)
    causes: list[str]
    consequences: list[str]
    vocabulary: list[Vocabulary] = Field(min_length=2, max_length=10)
    document: Document
    sources: list[Source] = Field(min_length=1, max_length=10)
    success_criteria: list[str]
    remediation: list[str]

    @model_validator(mode="after")
    def chronological(self):
        years = [e.year for e in self.timeline]
        if years != sorted(years) or len({e.id for e in self.timeline}) != len(years):
            raise ValueError("Frise non chronologique ou événements dupliqués")
        events = {e.id: e for e in self.timeline}
        for figure in self.figures:
            if figure.born >= figure.died:
                raise ValueError("Période du personnage incohérente")
            for key in figure.event_ids:
                if key not in events or not figure.born <= events[key].year <= figure.died:
                    raise ValueError("Personnage associé à un événement hors de sa vie")
        allowed = {str(s.url) for s in self.sources}
        for item in [*self.timeline, *self.figures, *self.places, self.document]:
            if str(item.source.url) not in allowed:
                raise ValueError("Référence absente des sources du chapitre")
        return self
