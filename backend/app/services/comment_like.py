from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.comment import Comment
from app.models.comment_like import CommentLike


class CommentNotFoundError(LookupError):
    """Raised when comment is missing."""


class CommentLikeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_like(self, *, comment_id: UUID, user_id: UUID) -> bool:
        """Add a like if absent. Returns True when a new like is created."""
        comment = await self._get_comment(comment_id)
        if comment is None:
            raise CommentNotFoundError("Comment not found")

        like_cols = getattr(CommentLike, "__table__").c
        insert_statement = (
            pg_insert(CommentLike)
            .values(user_id=user_id, comment_id=comment_id)
            .on_conflict_do_nothing(index_elements=["comment_id", "user_id"])
            .returning(like_cols.id)
        )
        try:
            inserted_like_id = (await self.db.exec(insert_statement)).one_or_none()
            if inserted_like_id is None:
                await self.db.commit()
                return False

            await self.db.commit()
            return True
        except Exception:
            await self.db.rollback()
            raise

    async def remove_like(self, *, comment_id: UUID, user_id: UUID) -> bool:
        """Remove a like if present. Returns True when an existing like is removed."""
        comment = await self._get_comment(comment_id)
        if comment is None:
            raise CommentNotFoundError("Comment not found")

        like_cols = getattr(CommentLike, "__table__").c
        delete_stmt = (
            delete(CommentLike)
            .where(
                like_cols.comment_id == comment_id,
                like_cols.user_id == user_id,
            )
            .returning(like_cols.id)
        )

        try:
            result = await self.db.exec(delete_stmt)
            removed_like_id = result.one_or_none()
            
            await self.db.commit()
            return removed_like_id is not None
        except Exception:
            await self.db.rollback()
            raise

    async def _get_comment(self, comment_id: UUID) -> Comment | None:
        comment_cols = getattr(Comment, "__table__").c
        statement = select(Comment).where(
            comment_cols.id == comment_id,
            comment_cols.deleted_at.is_(None)
        )
        result = await self.db.exec(statement)
        return result.first()
