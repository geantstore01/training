from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok", "unavailable"]
    service: str
    module: Literal["infrastructure"] = "infrastructure"


class ReadinessResponse(HealthResponse):
    postgres: bool
    redis: bool
