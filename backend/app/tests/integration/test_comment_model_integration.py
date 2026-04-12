"""Integration tests for the Comment model persistence contract."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import StatementError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.comment import (
    COMMENT_MODERATION_VISIBLE,
    CommentModerationState,
    Comment,
)
from app.models.project import Project
from app.models.user import User


async def _seed_user(db: AsyncSession) -> User:
    now = datetime.now(timezone.utc)
    user = User(
        email=f"comment_model_{uuid4().hex[:10]}@ufl.edu",
        username=f"cm_{uuid4().hex[:10]}",
        password_hash="integration-password-hash",
        full_name="Comment Model Tester",
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    await db.flush()
    return user


async def _seed_project(db: AsyncSession, owner_id) -> Project:
    now = datetime.now(timezone.utc)
    project = Project(
        created_by_id=owner_id,
        title=f"CM Project {uuid4().hex[:8]}",
        slug=f"cm-project-{uuid4().hex[:8]}",
        short_description="Comment model integration test project",
        is_published=True,
        published_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(project)
    await db.flush()
    return project


@pytest.mark.asyncio
async def test_comment_create_and_read_round_trip(db_session: AsyncSession):
    user = await _seed_user(db_session)
    project = await _seed_project(db_session, user.id)

    comment = Comment(  # pyright: ignore[reportCallIssue]
        project_id=project.id,
        author_id=user.id,
        body="Hello from integration test",
    )
    db_session.add(comment)
    await db_session.commit()

    fetched = await db_session.get(Comment, comment.id)
    assert fetched is not None
    assert fetched.body == "Hello from integration test"
    assert fetched.project_id == project.id
    assert fetched.author_id == user.id
    assert fetched.parent_comment_id is None
    assert fetched.moderation_state == COMMENT_MODERATION_VISIBLE
    assert fetched.deleted_at is None


@pytest.mark.asyncio
async def test_soft_delete_marker_persists(db_session: AsyncSession):
    user = await _seed_user(db_session)
    project = await _seed_project(db_session, user.id)

    comment = Comment(  # pyright: ignore[reportCallIssue]
        project_id=project.id,
        author_id=user.id,
        body="To be soft deleted",
    )
    db_session.add(comment)
    await db_session.commit()

    comment.deleted_at = datetime.now(timezone.utc)
    db_session.add(comment)
    await db_session.commit()

    fetched = await db_session.get(Comment, comment.id)
    assert fetched is not None
    assert fetched.deleted_at is not None
    assert fetched.body == "To be soft deleted"


@pytest.mark.asyncio
async def test_moderation_state_persists(db_session: AsyncSession):
    user = await _seed_user(db_session)
    project = await _seed_project(db_session, user.id)

    comment = Comment(  # pyright: ignore[reportCallIssue]
        project_id=project.id,
        author_id=user.id,
        body="Inappropriate content",
    )
    db_session.add(comment)
    await db_session.commit()

    comment.moderation_state = CommentModerationState.HIDDEN
    db_session.add(comment)
    await db_session.commit()

    fetched = await db_session.get(Comment, comment.id)
    assert fetched is not None
    assert fetched.moderation_state == CommentModerationState.HIDDEN


@pytest.mark.asyncio
async def test_parent_comment_reference_persists(db_session: AsyncSession):
    user = await _seed_user(db_session)
    project = await _seed_project(db_session, user.id)

    parent_comment = Comment(  # pyright: ignore[reportCallIssue]
        project_id=project.id,
        author_id=user.id,
        body="Parent comment",
    )
    db_session.add(parent_comment)
    await db_session.commit()

    child_comment = Comment(  # pyright: ignore[reportCallIssue]
        project_id=project.id,
        author_id=user.id,
        parent_comment_id=parent_comment.id,
        body="Child comment placeholder for future threads",
    )
    db_session.add(child_comment)
    await db_session.commit()

    fetched = await db_session.get(Comment, child_comment.id)
    assert fetched is not None
    assert fetched.parent_comment_id == parent_comment.id


@pytest.mark.asyncio
async def test_comment_requires_existing_project_and_author(db_session: AsyncSession):
    comment = Comment(  # pyright: ignore[reportCallIssue]
        project_id=uuid4(),
        author_id=uuid4(),
        body="This should fail",
    )
    db_session.add(comment)

    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_comments_can_be_filtered_by_project_id(db_session: AsyncSession):
    user = await _seed_user(db_session)
    project_a = await _seed_project(db_session, user.id)
    project_b = await _seed_project(db_session, user.id)

    comment_a = Comment(  # pyright: ignore[reportCallIssue]
        project_id=project_a.id,
        author_id=user.id,
        body="Project A",
    )
    comment_b = Comment(  # pyright: ignore[reportCallIssue]
        project_id=project_b.id,
        author_id=user.id,
        body="Project B",
    )
    db_session.add(comment_a)
    db_session.add(comment_b)
    await db_session.commit()

    result = await db_session.exec(
        select(Comment).where(Comment.project_id == project_a.id)
    )
    project_a_comments = result.all()

    ids = [comment.id for comment in project_a_comments]
    assert comment_a.id in ids
    assert comment_b.id not in ids


@pytest.mark.asyncio
async def test_comment_moderation_state_rejects_invalid_values(
    db_session: AsyncSession,
):
    user = await _seed_user(db_session)
    project = await _seed_project(db_session, user.id)

    comment = Comment(  # pyright: ignore[reportCallIssue]
        project_id=project.id,
        author_id=user.id,
        body="Invalid moderation state",
        moderation_state="shadow",  # pyright: ignore[reportArgumentType]
    )
    db_session.add(comment)

    with pytest.raises((ValueError, StatementError)):
        await db_session.commit()
    await db_session.rollback()
