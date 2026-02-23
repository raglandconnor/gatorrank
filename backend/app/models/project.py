from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    __tablename__ = "projects"  # pyright: ignore[reportAssignmentType]

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    created_by_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    title: str = Field(nullable=False, max_length=255)
    description: str | None = Field(
        default=None, sa_column=sa.Column(sa.Text(), nullable=True)
    )
    demo_url: str | None = Field(default=None, max_length=2048)
    github_url: str | None = Field(default=None, max_length=2048)
    video_url: str | None = Field(default=None, max_length=2048)
    vote_count: int = Field(default=0, nullable=False)
    is_group_project: bool = Field(default=False, nullable=False)
    is_published: bool = Field(
        default=False,
        sa_column=sa.Column(sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    published_at: datetime | None = Field(
        default=None, sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        )
    )
    updated_at: datetime = Field(
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        )
    )


class ProjectMember(SQLModel, table=True):
    __tablename__ = "project_members"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        UniqueConstraint(
            "project_id", "user_id", name="uq_project_members_project_id_user_id"
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    project_id: UUID = Field(foreign_key="projects.id", nullable=False, index=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    role: str = Field(default="contributor", nullable=False, max_length=32)
    added_at: datetime = Field(
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        )
    )


class Vote(SQLModel, table=True):
    __tablename__ = "votes"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_votes_user_id_project_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    project_id: UUID = Field(foreign_key="projects.id", nullable=False, index=True)
    created_at: datetime = Field(
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        )
    )
