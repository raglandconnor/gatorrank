from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

COMMENT_MODERATION_ENUM_NAME = "comment_moderation_state"


class CommentModerationState(str, Enum):
    VISIBLE = "visible"
    HIDDEN = "hidden"


COMMENT_MODERATION_VISIBLE = CommentModerationState.VISIBLE.value
COMMENT_MODERATION_HIDDEN = CommentModerationState.HIDDEN.value
COMMENT_MODERATION_STATES = {
    COMMENT_MODERATION_VISIBLE,
    COMMENT_MODERATION_HIDDEN,
}


class Comment(SQLModel, table=True):
    __tablename__ = "comments"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        sa.Index("ix_comments_project_id_created_at", "project_id", "created_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    project_id: UUID = Field(foreign_key="projects.id", nullable=False, index=True)
    author_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    parent_comment_id: UUID | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.Uuid(),
            sa.ForeignKey("comments.id"),
            nullable=True,
        ),
    )
    body: str = Field(sa_column=sa.Column(sa.Text(), nullable=False))
    moderation_state: CommentModerationState = Field(
        default=CommentModerationState.VISIBLE,
        sa_column=sa.Column(
            sa.Enum(
                CommentModerationState,
                name=COMMENT_MODERATION_ENUM_NAME,
                native_enum=False,
                create_constraint=True,
                validate_strings=True,
                values_callable=lambda enum_cls: [member.value for member in enum_cls],
            ),
            nullable=False,
            server_default=COMMENT_MODERATION_VISIBLE,
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
