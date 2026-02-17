"""drop redundant users email index

Revision ID: 66ccec161dbe
Revises: 205162b2f24f
Create Date: 2026-02-16 16:43:59.533921

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "66ccec161dbe"
down_revision: Union[str, Sequence[str], None] = "205162b2f24f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(op.f("ix_users_email"), table_name="users")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
