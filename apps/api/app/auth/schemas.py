from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=8, max_length=256)
    accepted_terms: bool = True

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email address")
        return normalized


class LoginRequest(BaseModel):
    username: str
    password: str


class PasswordResetRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    password: str = Field(min_length=8, max_length=256)


class EmailVerificationRequest(BaseModel):
    email: str | None = Field(default=None, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email address")
        return normalized


class EmailVerificationConfirmRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str | None = None
    email_verified: bool = False
    is_admin: bool
    banned: bool


class AuthResponse(BaseModel):
    user: UserResponse
    csrf_token: str


class UserSessionResponse(BaseModel):
    id: int
    created_at: datetime
    last_seen_at: datetime | None = None
    revoked_at: datetime | None = None
    current: bool = False
    user_agent: str | None = None


class GenericOkResponse(BaseModel):
    ok: bool = True
