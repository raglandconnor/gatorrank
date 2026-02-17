"""set timestamp defaults

Revision ID: 205162b2f24f
Revises: 5e373bda1732
Create Date: 2026-02-16 16:32:40.692710

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "205162b2f24f"
down_revision: Union[str, Sequence[str], None] = "5e373bda1732"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    now = sa.text("now()")

    op.alter_column("users", "created_at", server_default=now)
    op.alter_column("users", "updated_at", server_default=now)

    op.alter_column("projects", "created_at", server_default=now)
    op.alter_column("projects", "updated_at", server_default=now)

    op.alter_column("project_members", "added_at", server_default=now)
    op.alter_column("votes", "created_at", server_default=now)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("votes", "created_at", server_default=None)
    op.alter_column("project_members", "added_at", server_default=None)

    op.alter_column("projects", "updated_at", server_default=None)
    op.alter_column("projects", "created_at", server_default=None)

    op.alter_column("users", "updated_at", server_default=None)
    op.alter_column("users", "created_at", server_default=None)
