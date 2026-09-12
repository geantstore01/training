from uuid import UUID
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    school_id: UUID
    login: str = Field(min_length=3, max_length=64, pattern=r"^[a-z0-9][a-z0-9._-]+$")
    password: SecretStr = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: SecretStr = Field(min_length=1, max_length=180)


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: SecretStr = Field(min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=12, max_length=128)


class TokenPair(BaseModel):
    access_token: str = Field(repr=False)
    refresh_token: str = Field(repr=False)
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class SessionIdentity(BaseModel):
    user_id: UUID
    school_id: UUID
    roles: list[str]
    session_id: UUID


class PublicKey(BaseModel):
    kty: Literal["RSA"]
    kid: str
    alg: Literal["RS256"]
    use: Literal["sig"]
    n: str
    e: str


class PublicKeys(BaseModel):
    keys: list[PublicKey]
