from datetime import date, datetime
from typing import Literal
from uuid import UUID
from pydantic import Field, field_validator, model_validator
from shared.ai.contracts import Strict
from .ingestion import official_url

class Ingest(Strict):
    url: str = Field(max_length=2000)
    title: str = Field(min_length=3, max_length=240)
    level: Literal["CM1", "CM2"]
    subject: Literal["francais", "mathematiques", "histoire", "sciences"]
    history_chapter: Literal["ferry","republique","industrie","guerre-14","guerre-39","europe"] | None = None
    programme_version: str = Field(min_length=1, max_length=80)
    effective_from: date
    effective_until: date | None = None
    page_selection: list[int] = Field(default_factory=list, max_length=30)
    @field_validator("page_selection")
    @classmethod
    def pages(cls, value):
        if value != sorted(set(value)) or any(x < 1 or x > 100 for x in value):
            raise ValueError("Pages uniques croissantes entre 1 et 100 requises")
        return value
    @field_validator("url")
    @classmethod
    def official(cls, value):
        official_url(value)
        return value
    @model_validator(mode="after")
    def dates(self):
        if self.history_chapter and (self.subject!="histoire" or self.level!="CM2"):
            raise ValueError("Chapitre réservé à l’histoire CM2")
        if self.effective_until and self.effective_until < self.effective_from:
            raise ValueError("dates")
        return self

class Review(Strict):
    confirmed_human_review: Literal[True]
    decision: Literal["approved", "rejected"]
    reason_code: Literal["programme_verified", "wrong_scope", "obsolete", "extraction_issue", "unsafe_content"]

class Document(Strict):
    history_chapter: str | None = None
    page_selection: list[int]
    id: UUID
    url: str
    title: str
    checksum: str
    version: int
    level: str
    subject: str
    programme_version: str
    effective_from: date
    effective_until: date | None
    status: str
    created_by: UUID
    approved_by: UUID | None
    approved_at: datetime | None
