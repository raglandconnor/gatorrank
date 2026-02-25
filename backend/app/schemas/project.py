from datetime import datetime
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProjectMemberInfo(BaseModel):
    user_id: UUID
    role: str
    full_name: str | None = None
    profile_picture_url: str | None = None


class ProjectCreateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
        description="Project title. Leading/trailing whitespace is trimmed.",
    )
    description: str = Field(
        min_length=1,
        max_length=5000,
        description=(
            "Project description. Required for draft creation and trimmed before validation."
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
    is_group_project: bool = Field(
        default=False,
        description="Whether this is a group project. Defaults to false.",
    )

    @field_validator("title", "description", mode="before")
    @classmethod
    def _trim_required_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("demo_url", "github_url", "video_url", mode="before")
    @classmethod
    def _normalize_optional_url(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @field_validator("demo_url", "github_url", "video_url")
    @classmethod
    def _validate_http_url(cls, value: str | None) -> str | None:
        if value is None:
            return None

        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Must be a valid http(s) URL")
        return value

    @model_validator(mode="after")
    def _require_at_least_one_project_url(self) -> "ProjectCreateRequest":
        if any([self.demo_url, self.github_url, self.video_url]):
            return self
        raise ValueError("Provide at least one of demo_url, github_url, or video_url.")


class ProjectBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by_id: UUID
    title: str
    description: str | None = None
    demo_url: str | None = None
    github_url: str | None = None
    video_url: str | None = None
    vote_count: int
    is_group_project: bool
    is_published: bool
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(ProjectBaseResponse):
    members: list[ProjectMemberInfo] = Field(default_factory=list)


class ProjectListItemResponse(ProjectBaseResponse):
    members: list[ProjectMemberInfo] = Field(default_factory=list)


class ProjectListResponse(BaseModel):
    items: list[ProjectListItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None
