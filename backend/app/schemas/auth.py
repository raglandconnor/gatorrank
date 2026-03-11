from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AuthUserResponse(BaseModel):
    """Public user fields returned in auth token bootstrap responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: str
    full_name: str | None = None
    profile_picture_url: str | None = None


class AuthTokenResponse(BaseModel):
    """Canonical token payload returned by signup/login/refresh endpoints."""

    access_token: str
    token_type: str = Field(default="bearer")
    expires_in: int
    refresh_token: str
    refresh_token_expires_in: int
    user: AuthUserResponse


class AuthSignupRequest(BaseModel):
    """Request body for first-party user signup."""

    email: EmailStr
    password: str
    full_name: str | None = Field(default=None, max_length=255)
    remember_me: bool = False

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("password")
    @classmethod
    def validate_password_policy(cls, value: str) -> str:
        if value.strip() == "":
            raise ValueError("Password cannot be whitespace only")
        if len(value) < 12:
            raise ValueError("Password must be at least 12 characters")
        if len(value) > 128:
            raise ValueError("Password must be at most 128 characters")
        return value

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value


class AuthLoginRequest(BaseModel):
    """Request body for first-party user login."""

    email: EmailStr
    password: str
    remember_me: bool = False

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class AuthRefreshRequest(BaseModel):
    """Request body for refresh token rotation."""

    refresh_token: str = Field(min_length=1)


class AuthLogoutRequest(BaseModel):
    """Request body for refresh-session revocation."""

    refresh_token: str = Field(min_length=1)


class AuthMeResponse(BaseModel):
    """Authenticated user profile response for `/auth/me`."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: str
    full_name: str | None = None
    profile_picture_url: str | None = None
    created_at: datetime
    updated_at: datetime
