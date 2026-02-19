from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectMemberInfo(BaseModel):
    user_id: UUID
    role: str
    full_name: str | None = None
    email: str | None = None
    profile_picture_url: str | None = None


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
