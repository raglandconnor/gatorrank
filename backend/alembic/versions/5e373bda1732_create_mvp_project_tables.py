"""create mvp project tables

Revision ID: 5e373bda1732
Revises: bcb007443cbb
Create Date: 2026-02-16 16:05:16.627113

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5e373bda1732"
down_revision: Union[str, Sequence[str], None] = "bcb007443cbb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("demo_url", sa.String(length=2048), nullable=True),
        sa.Column("github_url", sa.String(length=2048), nullable=True),
        sa.Column("video_url", sa.String(length=2048), nullable=True),
        sa.Column("vote_count", sa.Integer(), nullable=False),
        sa.Column("is_group_project", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_projects_created_by_id"), "projects", ["created_by_id"], unique=False
    )

    op.create_table(
        "project_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "user_id", name="uq_project_members_project_id_user_id"
        ),
    )
    op.create_index(
        op.f("ix_project_members_project_id"),
        "project_members",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_members_user_id"), "project_members", ["user_id"], unique=False
    )

    op.create_table(
        "votes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "project_id", name="uq_votes_user_id_project_id"
        ),
    )
    op.create_index(op.f("ix_votes_project_id"), "votes", ["project_id"], unique=False)
    op.create_index(op.f("ix_votes_user_id"), "votes", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_votes_user_id"), table_name="votes")
    op.drop_index(op.f("ix_votes_project_id"), table_name="votes")
    op.drop_table("votes")

    op.drop_index(op.f("ix_project_members_user_id"), table_name="project_members")
    op.drop_index(op.f("ix_project_members_project_id"), table_name="project_members")
    op.drop_table("project_members")

    op.drop_index(op.f("ix_projects_created_by_id"), table_name="projects")
    op.drop_table("projects")
