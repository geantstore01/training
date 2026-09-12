from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, model_validator

Role = Literal["student", "parent", "teacher", "school_admin", "content_creator", "sys_admin"]
Purpose = Literal["ai_local", "ai_cloud", "voice"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class Identity(StrictModel):
    first_name: str = Field(min_length=1, max_length=80, repr=False, pattern=r"^[^\W\d_]+(?:[ '’-][^\W\d_]+)*$")
    last_name: str = Field(min_length=1, max_length=80, repr=False, pattern=r"^[^\W\d_]+(?:[ '’-][^\W\d_]+)*$")


class StudentInput(Identity):
    pseudonym: str = Field(min_length=2, max_length=80)
    level: Literal["CM1", "CM2"]


class AccountInput(StrictModel):
    login: str = Field(min_length=3, max_length=64, pattern=r"^[a-z0-9][a-z0-9._-]+$")
    password: SecretStr = Field(min_length=12, max_length=128)
    role: Role
    email: EmailStr | None = Field(default=None, repr=False)
    student: StudentInput | None = None
    display_name: str | None = Field(default=None, min_length=2, max_length=120)

    @model_validator(mode="after")
    def profile_matches_role(self):
        if (self.role == "student") != (self.student is not None):
            raise ValueError("Student profile must match role")
        if self.role == "teacher" and not self.display_name:
            raise ValueError("Teacher display name required")
        return self


class AccountView(StrictModel):
    id: UUID
    school_id: UUID
    login: str
    status: str
    roles: list[Role]
    student_id: UUID | None = None
    guardian_id: UUID | None = None
    teacher_id: UUID | None = None


class AccountUpdate(StrictModel):
    status: Literal["active", "locked"] | None = None
    password: SecretStr | None = Field(default=None, min_length=12, max_length=128)


class SchoolInput(StrictModel):
    name: str = Field(min_length=2, max_length=200)
    admin: AccountInput

    @model_validator(mode="after")
    def admin_role(self):
        if self.admin.role != "school_admin":
            raise ValueError("A school administrator is required")
        return self


class SchoolView(StrictModel):
    school_id: UUID
    name: str
    administrator: AccountView


class StudentView(StrictModel):
    id: UUID
    user_id: UUID
    school_id: UUID
    pseudonym: str
    level: Literal["CM1", "CM2"]
    accessibility_preferences: dict


class Preferences(StrictModel):
    text_size: Literal["normal", "large"] = "normal"
    dyslexic_font: bool = False
    voice_instructions: bool = False


class StudentUpdate(StrictModel):
    pseudonym: str | None = Field(default=None, min_length=2, max_length=80)
    level: Literal["CM1", "CM2"] | None = None
    identity: Identity | None = None


class GuardianLinkInput(StrictModel):
    guardian_id: UUID
    student_id: UUID
    relationship: Literal["parent", "legal_guardian"]
    verification_reference: SecretStr = Field(min_length=8, max_length=500)


class GuardianLinkView(StrictModel):
    id: UUID
    guardian_id: UUID
    student_id: UUID
    authority_verified_at: datetime | None
    revoked_at: datetime | None


class ConsentInput(StrictModel):
    purpose: Purpose
    policy_version: str = Field(min_length=1, max_length=40)
    granted: bool
    understood: bool

    @model_validator(mode="after")
    def affirmative_understanding(self):
        if self.granted and not self.understood:
            raise ValueError("Understanding required for a grant")
        return self


class WithdrawalInput(StrictModel):
    purpose: Purpose
    policy_version: str = Field(min_length=1, max_length=40)


class ConsentView(StrictModel):
    id: UUID
    student_id: UUID
    guardian_id: UUID
    purpose: str
    policy_version: str
    event_type: str
    granted: bool
    revision: int
    supersedes_id: UUID | None
    recorded_at: datetime


class AssentInput(StrictModel):
    purpose: Purpose
    policy_version: str = Field(min_length=1, max_length=40)
    agreed: bool


class AssentView(StrictModel):
    id: UUID
    purpose: str
    policy_version: str
    agreed: bool
    recorded_at: datetime


class ConsentPolicy(StrictModel):
    version: str
    purposes: dict[Purpose, str]
    child_notice: str
    withdrawal: str
