"""add project slug addressability

Revision ID: d76e8fdc877a
Revises: 377b094d6028
Create Date: 2026-04-06 11:42:46.203184

"""

import re
import unicodedata
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d76e8fdc877a"
down_revision: Union[str, Sequence[str], None] = "377b094d6028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _build_slug_base(title: str) -> str:
    transliterated = (
        unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    )
    lowered = transliterated.strip().lower()
    hyphenated = re.sub(r"[^a-z0-9]+", "-", lowered)
    collapsed = re.sub(r"-{2,}", "-", hyphenated).strip("-")
    return collapsed or "project"


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("projects", sa.Column("slug", sa.String(length=80), nullable=True))

    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, title FROM projects ORDER BY created_at ASC, id ASC")
    ).fetchall()

    used_slugs: set[str] = set()
    for row in rows:
        project_id = row.id
        title = row.title
        base_slug = _build_slug_base(title)
        slug = base_slug
        suffix = 2
        while slug in used_slugs:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        used_slugs.add(slug)
        bind.execute(
            sa.text("UPDATE projects SET slug = :slug WHERE id = :project_id"),
            {"slug": slug, "project_id": project_id},
        )

    op.alter_column(
        "projects", "slug", existing_type=sa.String(length=80), nullable=False
    )
    op.create_unique_constraint("uq_projects_slug", "projects", ["slug"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_projects_slug", "projects", type_="unique")
    op.drop_column("projects", "slug")
