"""merge soft-delete and taxonomy heads

Revision ID: 377b094d6028
Revises: 43d6b84cf473, 867e13020b84
Create Date: 2026-04-03 17:27:15.805264

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "377b094d6028"
down_revision: Union[str, Sequence[str], None] = ("43d6b84cf473", "867e13020b84")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
