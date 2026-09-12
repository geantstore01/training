from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: SecretStr = Field(min_length=1, max_length=6000)
    student_id: UUID | None = None
    destination: Literal["local", "cloud"] = "local"


class LayerResult(BaseModel):
    layer: int = Field(ge=1, le=10)
    name: str
    status: Literal["pass", "block", "redact", "not_run"]
    codes: list[str]


class AnalyzeResponse(BaseModel):
    request_id: UUID
    decision: Literal["allow", "redact", "block"]
    sanitized_text: str | None = Field(default=None, repr=False)
    layers: list[LayerResult]
    redactions: dict[str, int]
    requires_adult_support: bool = False
    message: str | None = None
    policy_version: str = "safety-2.0"
