from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    profile_picture_url: str | None = Field(default=None, max_length=2048)


class UserUpdate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    profile_picture_url: str | None = Field(default=None, max_length=2048)


class UserPublic(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    role: str
    created_at: datetime


class UserPrivate(UserPublic):
    email: str
    updated_at: datetime
