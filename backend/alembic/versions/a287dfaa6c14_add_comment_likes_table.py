"""Add Comment Likes table

Revision ID: a287dfaa6c14
Revises: f87f8bb2d427
Create Date: 2026-04-11 10:00:28.462221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a287dfaa6c14'
down_revision: Union[str, Sequence[str], None] = 'f87f8bb2d427'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'comment_likes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('comment_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('comment_id', 'user_id', name='uq_comment_likes_comment_id_user_id')
    )
    op.create_index(op.f('ix_comment_likes_comment_id'), 'comment_likes', ['comment_id'], unique=False)
    op.create_index(op.f('ix_comment_likes_user_id'), 'comment_likes', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_comment_likes_user_id'), table_name='comment_likes')
    op.drop_index(op.f('ix_comment_likes_comment_id'), table_name='comment_likes')
    op.drop_table('comment_likes')
