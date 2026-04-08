from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.project import ProjectListItemResponse

SearchSort = Literal["top", "new"]


def _contains_control_chars(value: str) -> bool:
    return any(ord(char) < 32 for char in value)


def _normalize_term_list(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        term = raw_value.strip()
        if not term:
            continue
        if _contains_control_chars(term):
            raise ValueError("Taxonomy filter terms cannot include control characters")
        lowered = term.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(term)
    return normalized


class ProjectSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    q: str | None = Field(
        default=None,
        description=(
            "Optional keyword query. Matching is case-insensitive against project title "
            "and short_description. Whitespace-only input is treated as omitted."
        ),
    )
    categories: list[str] = Field(
        default_factory=list,
        description="Optional category filters. Repeated query params are supported.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Optional tag filters. Repeated query params are supported.",
    )
    tech_stack: list[str] = Field(
        default_factory=list,
        description="Optional tech-stack filters. Repeated query params are supported.",
    )
    limit: int = Field(
        default=20,
        ge=1,
        description="Page size before service clamping.",
    )
    cursor: str | None = Field(
        default=None,
        description="Opaque cursor returned by a previous page response.",
    )
    sort: SearchSort = Field(
        default="top",
        description="Sort mode (`top` or `new`). Defaults to `top`.",
    )
    published_from: date | None = Field(
        default=None,
        description=(
            "Start date (inclusive) for `sort=top` published-date window in `YYYY-MM-DD`."
        ),
    )
    published_to: date | None = Field(
        default=None,
        description=(
            "End date (inclusive) for `sort=top` published-date window in `YYYY-MM-DD`."
        ),
    )

    @field_validator("q", mode="before")
    @classmethod
    def _normalize_query(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        return normalized or None

    @field_validator("cursor", mode="before")
    @classmethod
    def _normalize_cursor(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        return normalized or None

    @field_validator("categories", "tags", "tech_stack")
    @classmethod
    def _normalize_terms(cls, value: list[str]) -> list[str]:
        return _normalize_term_list(value)


class ProjectSearchResponse(BaseModel):
    items: list[ProjectListItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None
