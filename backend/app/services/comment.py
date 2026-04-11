from datetime import datetime, timezone
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import aliased
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.comment import Comment
from app.models.comment_like import CommentLike
from app.models.project import Project
from app.schemas.comment import CommentCreateRequest, CommentResponse


class CommentServiceError(Exception):
    pass


class CommentNotFoundError(CommentServiceError):
    pass

class CommentProjectNotFoundError(CommentServiceError):
    pass


class CommentForbiddenError(CommentServiceError):
    pass


class CommentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_comments(
        self,
        *,
        project_id: UUID,
        viewer_id: UUID | None = None,
        sort_by: str = "most_liked",
    ) -> list[CommentResponse]:
        # Maximum hard cap defined by requirements
        limit = 100

        comment_cols = getattr(Comment, "__table__").c
        project_cols = getattr(Project, "__table__").c

        # Ensure project exists and is published
        prj_stmt = select(Project).where(
            project_cols.id == project_id,
            project_cols.deleted_at.is_(None),
            project_cols.is_published.is_(True)
        )
        prj = (await self.db.exec(prj_stmt)).first()
        if not prj:
            raise CommentProjectNotFoundError("Project not found")

        statement = (
            select(
                Comment,
                sa.func.count(CommentLike.id).label("like_count"),
                sa.func.bool_or(CommentLike.user_id == viewer_id)
                .label("viewer_has_liked")
                if viewer_id
                else sa.sql.expression.false().label("viewer_has_liked"),
            )
            .outerjoin(CommentLike, CommentLike.comment_id == Comment.id)
            .where(Comment.project_id == project_id)
            .group_by(Comment.id)
        )

        if sort_by == "newest":
            statement = statement.order_by(Comment.created_at.desc(), Comment.id.desc())
        elif sort_by == "oldest":
            statement = statement.order_by(Comment.created_at.asc(), Comment.id.asc())
        else:
            # Default most_liked
            statement = statement.order_by(
                sa.text("like_count DESC"), Comment.created_at.desc(), Comment.id.desc()
            )

        statement = statement.limit(limit)
        results = await self.db.exec(statement)

        responses = []
        for row in results.all():
            comment, like_count, viewer_has_liked = row
            responses.append(
                CommentResponse.from_model(
                    comment=comment,
                    like_count=like_count or 0,
                    viewer_has_liked=viewer_has_liked or False,
                )
            )

        return responses

    async def create_comment(
        self, *, project_id: UUID, author_id: UUID, data: CommentCreateRequest
    ) -> CommentResponse:
        project_cols = getattr(Project, "__table__").c
        prj_stmt = select(Project).where(
            project_cols.id == project_id,
            project_cols.deleted_at.is_(None),
            project_cols.is_published.is_(True)
        )
        prj = (await self.db.exec(prj_stmt)).first()
        if not prj:
            raise CommentProjectNotFoundError("Project not found")

        comment = Comment(
            project_id=project_id,
            author_id=author_id,
            body=data.body,
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)

        return CommentResponse.from_model(
            comment=comment, like_count=0, viewer_has_liked=False
        )

    async def delete_comment(self, *, comment_id: UUID, actor_id: UUID, is_admin: bool):
        comment = await self.db.get(Comment, comment_id)
        if not comment or comment.deleted_at is not None:
            raise CommentNotFoundError("Comment not found")

        if not is_admin and comment.author_id != actor_id:
            raise CommentForbiddenError("Cannot delete someone else's comment")

        comment.deleted_at = datetime.now(timezone.utc)
        self.db.add(comment)
        await self.db.commit()

    async def moderate_comment(self, *, comment_id: UUID, new_state: str):
        comment = await self.db.get(Comment, comment_id)
        if not comment:
            raise CommentNotFoundError("Comment not found")

        comment.moderation_state = new_state
        self.db.add(comment)
        await self.db.commit()
