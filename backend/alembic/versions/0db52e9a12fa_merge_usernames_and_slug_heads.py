"""merge usernames and slug heads

Revision ID: 0db52e9a12fa
Revises: b21b928ae116, d76e8fdc877a
Create Date: 2026-04-06 13:07:39.781299

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "0db52e9a12fa"
down_revision: Union[str, Sequence[str], None] = ("b21b928ae116", "d76e8fdc877a")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
