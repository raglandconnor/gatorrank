from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    profile_picture_url: str | None = Field(default=None, max_length=2048)


class UserUpdate(UserBase):
    pass


class UserPublic(UserBase):
    id: UUID
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserPrivate(UserPublic):
    email: str
    updated_at: datetime
