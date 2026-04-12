from datetime import datetime, timezone
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.comment import Comment
from app.models.comment_like import CommentLike
from app.models.project import Project
from app.models.user import User
from app.policy.roles import PolicyDeniedError, require_comment_moderation
from app.schemas.comment import CommentCreateRequest, CommentResponse

COMMENT_LIST_HARD_CAP = 100


class CommentServiceError(Exception):
    """Base class for comment service failures."""


class CommentNotFoundError(CommentServiceError):
    """Raised when the requested comment does not exist."""


class CommentProjectNotFoundError(CommentServiceError):
    """Raised when the requested project cannot accept or expose comments."""


class CommentForbiddenError(CommentServiceError):
    """Raised when the actor cannot perform the requested comment action."""


class CommentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_comments(
        self,
        *,
        project_id: UUID,
        viewer_id: UUID | None = None,
        sort_by: str = "top",
    ) -> list[CommentResponse]:
        await self._require_public_comment_project(project_id)

        comment_cols = getattr(Comment, "__table__").c
        like_cols = getattr(CommentLike, "__table__").c
        user_cols = getattr(User, "__table__").c

        like_count_expr = sa.func.count(like_cols.id)
        if viewer_id is None:
            viewer_liked_expr = sa.false()
        else:
            viewer_liked_expr = sa.func.coalesce(
                sa.func.bool_or(like_cols.user_id == viewer_id),
                sa.false(),
            )

        statement = (
            (
                select(  # pyright: ignore[reportCallIssue]
                    Comment,
                    user_cols.username,
                    user_cols.full_name,
                    user_cols.profile_picture_url,
                    like_count_expr.label("like_count"),
                    viewer_liked_expr.label("viewer_has_liked"),
                )
            )
            .join(User, user_cols.id == comment_cols.author_id)
            .outerjoin(CommentLike, like_cols.comment_id == comment_cols.id)
            .where(comment_cols.project_id == project_id)
            .group_by(
                comment_cols.id,
                user_cols.id,
                user_cols.username,
                user_cols.full_name,
                user_cols.profile_picture_url,
            )
        )

        if sort_by == "oldest":
            statement = statement.order_by(
                comment_cols.created_at.asc(), comment_cols.id.asc()
            )
        elif sort_by == "newest":
            statement = statement.order_by(
                comment_cols.created_at.desc(), comment_cols.id.desc()
            )
        else:
            statement = statement.order_by(
                like_count_expr.desc(),
                comment_cols.created_at.desc(),
                comment_cols.id.desc(),
            )

        statement = statement.limit(COMMENT_LIST_HARD_CAP)
        results = (await self.db.exec(statement)).all()

        return [
            CommentResponse.from_record(
                comment=comment,
                username=username,
                full_name=full_name,
                profile_picture_url=profile_picture_url,
                like_count=like_count or 0,
                viewer_has_liked=bool(viewer_has_liked),
            )
            for (
                comment,
                username,
                full_name,
                profile_picture_url,
                like_count,
                viewer_has_liked,
            ) in results
        ]

    async def create_comment(
        self,
        *,
        project_id: UUID,
        author_id: UUID,
        data: CommentCreateRequest,
    ) -> CommentResponse:
        await self._require_public_comment_project(project_id)

        comment = Comment(  # pyright: ignore[reportCallIssue]
            project_id=project_id,
            author_id=author_id,
            body=data.body,
        )
        try:
            self.db.add(comment)
            await self.db.commit()
            await self.db.refresh(comment)
        except Exception:
            await self.db.rollback()
            raise

        author = await self.db.get(User, author_id)
        username = author.username if author else None
        full_name = author.full_name if author else None
        profile_picture_url = author.profile_picture_url if author else None

        return CommentResponse.from_record(
            comment=comment,
            username=username,
            full_name=full_name,
            profile_picture_url=profile_picture_url,
            like_count=0,
            viewer_has_liked=False,
        )

    async def delete_own_comment(self, *, comment_id: UUID, actor_id: UUID) -> None:
        comment = await get_public_comment_for_mutation(
            self.db,
            comment_id=comment_id,
            require_not_deleted=True,
        )
        if comment.author_id != actor_id:
            raise CommentForbiddenError("Comment delete forbidden")

        comment.deleted_at = datetime.now(timezone.utc)
        try:
            self.db.add(comment)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def moderate_comment(
        self,
        *,
        comment_id: UUID,
        moderation_state: str,
        principal: User | None,
    ) -> None:
        self._require_moderation_principal(principal)
        comment = await get_public_comment_for_mutation(
            self.db,
            comment_id=comment_id,
            require_not_deleted=True,
        )

        comment.moderation_state = moderation_state
        try:
            self.db.add(comment)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def moderator_delete_comment(
        self,
        *,
        comment_id: UUID,
        principal: User | None,
    ) -> None:
        self._require_moderation_principal(principal)
        comment = await get_public_comment_for_mutation(
            self.db,
            comment_id=comment_id,
            require_not_deleted=False,
        )
        if comment.deleted_at is not None:
            return

        comment.deleted_at = datetime.now(timezone.utc)
        try:
            self.db.add(comment)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def _require_public_comment_project(self, project_id: UUID) -> None:
        project_cols = getattr(Project, "__table__").c
        statement = select(Project.id).where(
            project_cols.id == project_id,
            project_cols.deleted_at.is_(None),
            project_cols.is_published.is_(True),
        )
        result = await self.db.exec(statement)
        if result.one_or_none() is None:
            raise CommentProjectNotFoundError("Project not found")

    @staticmethod
    def _require_moderation_principal(principal: User | None) -> None:
        try:
            require_comment_moderation(principal)
        except PolicyDeniedError as exc:
            raise CommentForbiddenError("Comment moderation forbidden") from exc


async def get_public_comment_for_mutation(
    db: AsyncSession,
    *,
    comment_id: UUID,
    require_not_deleted: bool,
) -> Comment:
    """Return a comment only when both the comment and its parent project are visible."""
    comment_cols = getattr(Comment, "__table__").c
    project_cols = getattr(Project, "__table__").c

    conditions = [
        comment_cols.id == comment_id,
        project_cols.id == comment_cols.project_id,
        project_cols.deleted_at.is_(None),
        project_cols.is_published.is_(True),
    ]
    if require_not_deleted:
        conditions.append(comment_cols.deleted_at.is_(None))

    statement = (
        select(Comment)
        .join(Project, project_cols.id == comment_cols.project_id)
        .where(*conditions)
    )
    result = await db.exec(statement)
    comment = result.first()
    if comment is None:
        raise CommentNotFoundError("Comment not found")
    return comment
