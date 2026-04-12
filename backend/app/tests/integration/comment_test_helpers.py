from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import delete
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.comment import Comment, CommentModerationState
from app.models.comment_like import CommentLike
from app.models.project import Project
from app.models.user import User


async def seed_comment_user(
    db_session: AsyncSession,
    *,
    email: str,
    name: str,
    role: str = "student",
) -> User:
    now = datetime.now(timezone.utc)
    user = User(
        email=email,
        username=f"user_{uuid4().hex[:10]}",
        password_hash="integration-password-hash",
        role=role,
        full_name=name,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def seed_comment_project(
    db_session: AsyncSession,
    *,
    created_by_id,
    title: str,
    is_published: bool = True,
) -> Project:
    now = datetime.now(timezone.utc)
    project = Project(
        created_by_id=created_by_id,
        title=title,
        slug=f"{title.lower().replace(' ', '-')}-{uuid4().hex[:6]}",
        short_description=f"{title} description",
        is_group_project=False,
        is_published=is_published,
        published_at=now if is_published else None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(project)
    await db_session.flush()
    return project


async def seed_project_comment(
    db_session: AsyncSession,
    *,
    project_id,
    author_id,
    body: str,
    created_at: datetime | None = None,
    moderation_state: str | CommentModerationState = CommentModerationState.VISIBLE,
    deleted_at: datetime | None = None,
) -> Comment:
    now = created_at or datetime.now(timezone.utc)
    normalized_moderation_state = (
        moderation_state
        if isinstance(moderation_state, CommentModerationState)
        else CommentModerationState(moderation_state)
    )
    comment = Comment(
        project_id=project_id,
        author_id=author_id,
        body=body,
        moderation_state=normalized_moderation_state,
        deleted_at=deleted_at,
        created_at=now,
        updated_at=now,
    )
    db_session.add(comment)
    await db_session.flush()
    return comment


async def seed_comment_like(
    db_session: AsyncSession,
    *,
    comment_id,
    user_id,
) -> CommentLike:
    like = CommentLike(
        comment_id=comment_id,
        user_id=user_id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(like)
    await db_session.flush()
    return like


def override_get_db_factory(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    return override_get_db


async def cleanup_committed_comment_graph(
    async_engine: AsyncEngine,
    *,
    comment_id,
    project_id,
    user_ids: list,
) -> None:
    async with AsyncSession(async_engine, expire_on_commit=False) as cleanup:
        comment_like_cols = getattr(CommentLike, "__table__").c
        comment_cols = getattr(Comment, "__table__").c
        project_cols = getattr(Project, "__table__").c
        user_cols = getattr(User, "__table__").c
        await cleanup.exec(
            delete(CommentLike).where(comment_like_cols.comment_id == comment_id)
        )
        await cleanup.exec(delete(Comment).where(comment_cols.id == comment_id))
        await cleanup.exec(delete(Project).where(project_cols.id == project_id))
        await cleanup.exec(delete(User).where(user_cols.id.in_(user_ids)))
        await cleanup.commit()
