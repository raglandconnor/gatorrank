from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class AuthLoginRequest(BaseModel):
    """Request body for first-party user login."""

    email: EmailStr
    password: str
    remember_me: bool = False


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
