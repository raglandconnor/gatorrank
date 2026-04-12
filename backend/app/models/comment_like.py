from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class CommentLike(SQLModel, table=True):
    __tablename__ = "comment_likes"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        UniqueConstraint(
            "comment_id", "user_id", name="uq_comment_likes_comment_id_user_id"
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    comment_id: UUID = Field(foreign_key="comments.id", nullable=False, index=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    created_at: datetime = Field(
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        )
    )
