from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator


class UserBase(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    profile_picture_url: AnyHttpUrl | None = Field(default=None, max_length=2048)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    profile_picture_url: AnyHttpUrl | None = Field(default=None, max_length=2048)

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "UserUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if "full_name" in self.model_fields_set and self.full_name is None:
            raise ValueError("full_name cannot be null")
        return self


class UserPublic(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    role: str
    created_at: datetime


class UserPrivate(UserPublic):
    email: str
    updated_at: datetime
