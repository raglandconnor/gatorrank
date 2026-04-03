from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    __tablename__ = "categories"  # pyright: ignore[reportAssignmentType]

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    name: str = Field(sa_column=sa.Column(sa.String(length=64), nullable=False))
    normalized_name: str = Field(
        sa_column=sa.Column(
            sa.String(length=64), nullable=False, unique=True, index=True
        )
    )
    created_at: datetime = Field(
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        )
    )


class Tag(SQLModel, table=True):
    __tablename__ = "tags"  # pyright: ignore[reportAssignmentType]

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    name: str = Field(sa_column=sa.Column(sa.String(length=64), nullable=False))
    normalized_name: str = Field(
        sa_column=sa.Column(
            sa.String(length=64), nullable=False, unique=True, index=True
        )
    )
    created_at: datetime = Field(
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        )
    )


class TechStack(SQLModel, table=True):
    __tablename__ = "tech_stacks"  # pyright: ignore[reportAssignmentType]

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    name: str = Field(sa_column=sa.Column(sa.String(length=64), nullable=False))
    normalized_name: str = Field(
        sa_column=sa.Column(
            sa.String(length=64), nullable=False, unique=True, index=True
        )
    )
    created_at: datetime = Field(
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        )
    )


class ProjectCategory(SQLModel, table=True):
    __tablename__ = "project_categories"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "category_id",
            name="uq_project_categories_project_id_category_id",
        ),
        UniqueConstraint(
            "project_id", "position", name="uq_project_categories_project_id_position"
        ),
        Index(
            "ix_project_categories_category_id_project_id",
            "category_id",
            "project_id",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    project_id: UUID = Field(foreign_key="projects.id", nullable=False, index=True)
    category_id: UUID = Field(foreign_key="categories.id", nullable=False, index=True)
    position: int = Field(nullable=False, ge=0)
    created_at: datetime = Field(
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        )
    )


class ProjectTag(SQLModel, table=True):
    __tablename__ = "project_tags"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        UniqueConstraint(
            "project_id", "tag_id", name="uq_project_tags_project_id_tag_id"
        ),
        UniqueConstraint(
            "project_id", "position", name="uq_project_tags_project_id_position"
        ),
        Index(
            "ix_project_tags_tag_id_project_id",
            "tag_id",
            "project_id",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    project_id: UUID = Field(foreign_key="projects.id", nullable=False, index=True)
    tag_id: UUID = Field(foreign_key="tags.id", nullable=False, index=True)
    position: int = Field(nullable=False, ge=0)
    created_at: datetime = Field(
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        )
    )


class ProjectTechStack(SQLModel, table=True):
    __tablename__ = "project_tech_stacks"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "tech_stack_id",
            name="uq_project_tech_stacks_project_id_tech_stack_id",
        ),
        UniqueConstraint(
            "project_id", "position", name="uq_project_tech_stacks_project_id_position"
        ),
        Index(
            "ix_project_tech_stacks_tech_stack_id_project_id",
            "tech_stack_id",
            "project_id",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    project_id: UUID = Field(foreign_key="projects.id", nullable=False, index=True)
    tech_stack_id: UUID = Field(
        foreign_key="tech_stacks.id", nullable=False, index=True
    )
    position: int = Field(nullable=False, ge=0)
    created_at: datetime = Field(
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        )
    )
