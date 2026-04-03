from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _contains_control_chars(value: str) -> bool:
    return any(ord(char) < 32 or ord(char) == 127 for char in value)


class TaxonomyTermCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Display name for a taxonomy term.",
    )

    @field_validator("name", mode="before")
    @classmethod
    def _trim_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        if len(value) < 2 or len(value) > 64:
            raise ValueError("name must be between 2 and 64 characters")
        if _contains_control_chars(value):
            raise ValueError("name cannot include control characters")
        return value


class TaxonomyTermResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
