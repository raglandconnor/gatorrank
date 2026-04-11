from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Comment(SQLModel, table=True):
    __tablename__ = "comments"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        sa.Index("ix_comments_project_id_created_at", "project_id", "created_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    project_id: UUID = Field(foreign_key="projects.id", nullable=False, index=True)
    author_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    body: str = Field(sa_column=sa.Column(sa.Text(), nullable=False))
    moderation_state: str = Field(
        default="visible",
        sa_column=sa.Column(
            sa.String(length=32), nullable=False, server_default="visible"
        ),
    )
    deleted_at: datetime | None = Field(
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
