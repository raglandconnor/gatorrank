from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"  # pyright: ignore[reportAssignmentType]

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False, max_length=320)
    role: str = Field(default="student", nullable=False, max_length=32)
    full_name: str | None = Field(default=None, max_length=255)
    profile_picture_url: str | None = Field(default=None, max_length=2048)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
