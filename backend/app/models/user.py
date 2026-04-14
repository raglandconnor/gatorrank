from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.models.user_roles import USER_ROLE_STUDENT


class User(SQLModel, table=True):
    __tablename__ = "users"  # pyright: ignore[reportAssignmentType]

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    auth_user_id: UUID = Field(
        default_factory=uuid4,
        sa_column=sa.Column(sa.Uuid, nullable=False, unique=True, index=True),
    )
    email: str = Field(unique=True, nullable=False, max_length=320)
    username: str = Field(
        sa_column=sa.Column(
            sa.String(length=32), nullable=False, unique=True, index=True
        )
    )
    role: str = Field(default=USER_ROLE_STUDENT, nullable=False, max_length=32)
    full_name: str | None = Field(default=None, max_length=255)
    profile_picture_url: str | None = Field(default=None, max_length=2048)
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
