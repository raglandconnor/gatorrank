from datetime import date, datetime
import unicodedata
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.models.project_roles import ProjectMemberRole, ProjectMemberWritableRole
from app.schemas.taxonomy import TaxonomyTermResponse


def _normalize_optional_url_value(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    return value


def _validate_http_url_value(value: str | None) -> str | None:
    if value is None:
        return None

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Must be a valid http(s) URL")
    return value


def _normalize_taxonomy_term_value(value: str) -> str:
    return value.strip().lower()


def _contains_control_chars(value: str) -> bool:
    return any(unicodedata.category(char) == "Cc" for char in value)


def _validate_taxonomy_terms(
    values: list[str],
    *,
    max_terms: int,
    field_name: str,
) -> list[str]:
    if len(values) > max_terms:
        raise ValueError(f"{field_name} cannot contain more than {max_terms} terms")

    normalized_seen: set[str] = set()
    validated: list[str] = []
    for raw_value in values:
        term = raw_value.strip()
        if len(term) < 2 or len(term) > 64:
            raise ValueError(f"{field_name} terms must be between 2 and 64 characters")
        if _contains_control_chars(term):
            raise ValueError(f"{field_name} terms cannot include control characters")
        normalized = _normalize_taxonomy_term_value(term)
        if normalized in normalized_seen:
            raise ValueError(
                f"Duplicate taxonomy terms are not allowed in {field_name}"
            )
        normalized_seen.add(normalized)
        validated.append(term)
    return validated


class ProjectMemberInfo(BaseModel):
    user_id: UUID
    role: ProjectMemberRole
    full_name: str | None = None
    profile_picture_url: str | None = None


class ProjectCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        min_length=1,
        max_length=50,
        description="Project title. Leading/trailing whitespace is trimmed.",
    )
    short_description: str = Field(
        min_length=1,
        max_length=280,
        description=(
            "Short project summary. Required for draft creation and trimmed before validation."
        ),
    )
    long_description: str | None = Field(
        default=None,
        max_length=5000,
        description=(
            "Optional long project description. Leading/trailing whitespace is trimmed."
        ),
    )
    demo_url: str | None = Field(
        default=None,
        max_length=2048,
        description=(
            "Optional demo URL (`http` or `https`). At least one of demo_url, "
            "github_url, or video_url must be provided."
        ),
    )
    github_url: str | None = Field(
        default=None,
        max_length=2048,
        description=(
            "Optional repository URL (`http` or `https`). At least one of demo_url, "
            "github_url, or video_url must be provided."
        ),
    )
    video_url: str | None = Field(
        default=None,
        max_length=2048,
        description=(
            "Optional video URL (`http` or `https`). At least one of demo_url, "
            "github_url, or video_url must be provided."
        ),
    )
    timeline_start_date: date | None = Field(
        default=None,
        description=(
            "Optional project timeline start date (`YYYY-MM-DD`). Required when "
            "`timeline_end_date` is provided."
        ),
    )
    timeline_end_date: date | None = Field(
        default=None,
        description=(
            "Optional project timeline end date (`YYYY-MM-DD`). Use `null` for in-progress "
            "timelines."
        ),
    )
    categories: list[str] = Field(
        default_factory=list,
        description=(
            "Optional category term names. Missing/empty means no categories. "
            "Submitted order is preserved."
        ),
    )
    tags: list[str] = Field(
        default_factory=list,
        description=(
            "Optional tag term names. Missing/empty means no tags. "
            "Submitted order is preserved."
        ),
    )
    tech_stack: list[str] = Field(
        default_factory=list,
        description=(
            "Optional tech stack term names. Missing/empty means no tech stack terms. "
            "Submitted order is preserved."
        ),
    )

    @field_validator("title", "short_description", "long_description", mode="before")
    @classmethod
    def _trim_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("demo_url", "github_url", "video_url", mode="before")
    @classmethod
    def _normalize_optional_url(cls, value: object) -> object:
        return _normalize_optional_url_value(value)

    @field_validator("demo_url", "github_url", "video_url")
    @classmethod
    def _validate_http_url(cls, value: str | None) -> str | None:
        return _validate_http_url_value(value)

    @field_validator("categories")
    @classmethod
    def _validate_categories(cls, value: list[str]) -> list[str]:
        return _validate_taxonomy_terms(value, max_terms=3, field_name="categories")

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, value: list[str]) -> list[str]:
        return _validate_taxonomy_terms(value, max_terms=10, field_name="tags")

    @field_validator("tech_stack")
    @classmethod
    def _validate_tech_stack(cls, value: list[str]) -> list[str]:
        return _validate_taxonomy_terms(value, max_terms=15, field_name="tech_stack")

    @model_validator(mode="after")
    def _require_at_least_one_project_url(self) -> "ProjectCreateRequest":
        if any([self.demo_url, self.github_url, self.video_url]):
            return self
        raise ValueError("Provide at least one of demo_url, github_url, or video_url.")

    @model_validator(mode="after")
    def _validate_timeline_dates(self) -> "ProjectCreateRequest":
        if self.timeline_end_date is not None and self.timeline_start_date is None:
            raise ValueError("timeline_end_date requires timeline_start_date.")
        if (
            self.timeline_start_date is not None
            and self.timeline_end_date is not None
            and self.timeline_start_date > self.timeline_end_date
        ):
            raise ValueError(
                "timeline_start_date must be on or before timeline_end_date."
            )
        return self


class ProjectUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Updated project title. Leading/trailing whitespace is trimmed.",
    )
    short_description: str | None = Field(
        default=None,
        min_length=1,
        max_length=280,
        description="Updated short project summary. Leading/trailing whitespace is trimmed.",
    )
    long_description: str | None = Field(
        default=None,
        max_length=5000,
        description="Updated long project description. Leading/trailing whitespace is trimmed.",
    )
    demo_url: str | None = Field(
        default=None,
        max_length=2048,
        description="Updated demo URL (`http` or `https`), or `null` to clear it.",
    )
    github_url: str | None = Field(
        default=None,
        max_length=2048,
        description="Updated repository URL (`http` or `https`), or `null` to clear it.",
    )
    video_url: str | None = Field(
        default=None,
        max_length=2048,
        description="Updated video URL (`http` or `https`), or `null` to clear it.",
    )
    timeline_start_date: date | None = Field(
        default=None,
        description=(
            "Updated timeline start date (`YYYY-MM-DD`), or `null` to clear timeline start."
        ),
    )
    timeline_end_date: date | None = Field(
        default=None,
        description=(
            "Updated timeline end date (`YYYY-MM-DD`), or `null` to indicate in-progress."
        ),
    )
    categories: list[str] | None = Field(
        default=None,
        description=(
            "Updated category term names. Omit to leave unchanged, provide empty array to clear."
        ),
    )
    tags: list[str] | None = Field(
        default=None,
        description="Updated tag term names. Omit to leave unchanged, provide empty array to clear.",
    )
    tech_stack: list[str] | None = Field(
        default=None,
        description=(
            "Updated tech stack term names. Omit to leave unchanged, provide empty array to clear."
        ),
    )

    @field_validator("title", "short_description", "long_description", mode="before")
    @classmethod
    def _trim_optional_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("demo_url", "github_url", "video_url", mode="before")
    @classmethod
    def _normalize_optional_url(cls, value: object) -> object:
        return _normalize_optional_url_value(value)

    @field_validator("demo_url", "github_url", "video_url")
    @classmethod
    def _validate_http_url(cls, value: str | None) -> str | None:
        return _validate_http_url_value(value)

    @field_validator("categories")
    @classmethod
    def _validate_categories(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        return _validate_taxonomy_terms(value, max_terms=3, field_name="categories")

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        return _validate_taxonomy_terms(value, max_terms=10, field_name="tags")

    @field_validator("tech_stack")
    @classmethod
    def _validate_tech_stack(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        return _validate_taxonomy_terms(value, max_terms=15, field_name="tech_stack")

    @model_validator(mode="after")
    def _validate_update_payload(self) -> "ProjectUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("At least one editable field must be provided")
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("title cannot be null")
        if (
            "short_description" in self.model_fields_set
            and self.short_description is None
        ):
            raise ValueError("short_description cannot be null")
        if "categories" in self.model_fields_set and self.categories is None:
            raise ValueError("categories cannot be null")
        if "tags" in self.model_fields_set and self.tags is None:
            raise ValueError("tags cannot be null")
        if "tech_stack" in self.model_fields_set and self.tech_stack is None:
            raise ValueError("tech_stack cannot be null")
        return self


class ProjectMemberCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(
        min_length=3,
        max_length=320,
        description="Email address of the user to add as a project member.",
    )
    role: ProjectMemberWritableRole = Field(
        default="contributor",
        description="Role for the new member (`maintainer` or `contributor`).",
    )

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class ProjectMemberUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: ProjectMemberWritableRole = Field(
        description="Updated role (`maintainer` or `contributor`)."
    )


class ProjectBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by_id: UUID
    title: str
    short_description: str
    long_description: str | None = None
    demo_url: str | None = None
    github_url: str | None = None
    video_url: str | None = None
    timeline_start_date: date | None = None
    timeline_end_date: date | None = None
    vote_count: int
    team_size: int = Field(
        ge=0,
        description="Computed count of active project members.",
    )
    is_group_project: bool
    is_published: bool
    viewer_has_voted: bool = False
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    categories: list[TaxonomyTermResponse] = Field(default_factory=list)
    tags: list[TaxonomyTermResponse] = Field(default_factory=list)
    tech_stack: list[TaxonomyTermResponse] = Field(default_factory=list)


class ProjectDetailResponse(ProjectBaseResponse):
    members: list[ProjectMemberInfo] = Field(default_factory=list)


class ProjectListItemResponse(ProjectBaseResponse):
    members: list[ProjectMemberInfo] = Field(default_factory=list)


class ProjectListResponse(BaseModel):
    items: list[ProjectListItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None
