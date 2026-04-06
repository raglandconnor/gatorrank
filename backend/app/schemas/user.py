from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator

from app.models.user_roles import UserRole
from app.utils.username import USERNAME_MAX_LENGTH, USERNAME_MIN_LENGTH


class UserBase(BaseModel):
    username: str = Field(
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        description=(
            "Canonical lowercase username for profile addressability. "
            "Contains only `a-z`, `0-9`, `_`, `-`."
        ),
    )
    full_name: str | None = Field(default=None, max_length=255)
    profile_picture_url: AnyHttpUrl | None = Field(default=None, max_length=2048)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    role: UserRole = Field(
        description="System role for authorization (`student`, `faculty`, or `admin`)."
    )
    created_at: datetime


class UserPrivate(UserPublic):
    email: str
    updated_at: datetime
