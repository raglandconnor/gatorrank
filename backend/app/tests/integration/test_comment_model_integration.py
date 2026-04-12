"""Integration tests for the Comment model (BE3-010A).

Covers:
- create/read round-trip
- soft-delete marker (deleted_at) persists through a separate read
- moderation_state persists through a separate read
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.comment import Comment
from app.models.project import Project
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
    await db.commit()
    await db.refresh(user)
    return user


async def _seed_project(db: AsyncSession, owner_id) -> Project:
    now = datetime.now(timezone.utc)
    project = Project(
        created_by_id=owner_id,
        title=f"CM Project {uuid4().hex[:8]}",
        slug=f"cm-project-{uuid4().hex[:8]}",
        short_description="Comment model integration test project",
        is_published=True,
        created_at=now,
        updated_at=now,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_comment_create_and_read_round_trip(db_session: AsyncSession):
    """A created comment can be read back with all fields intact."""
    user = await _seed_user(db_session)
    project = await _seed_project(db_session, user.id)

    comment = Comment(
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
    assert fetched.moderation_state == "visible"
    assert fetched.deleted_at is None


@pytest.mark.asyncio
async def test_soft_delete_marker_persists(db_session: AsyncSession):
    """Setting deleted_at on a comment persists to the database."""
    user = await _seed_user(db_session)
    project = await _seed_project(db_session, user.id)

    comment = Comment(
        project_id=project.id,
        author_id=user.id,
        body="To be soft deleted",
    )
    db_session.add(comment)
    await db_session.commit()

    # Apply soft delete
    now = datetime.now(timezone.utc)
    comment.deleted_at = now
    db_session.add(comment)
    await db_session.commit()

    fetched = await db_session.get(Comment, comment.id)
    assert fetched is not None, "Row should still exist after soft delete"
    assert fetched.deleted_at is not None, "deleted_at should be set"
    assert fetched.body == "To be soft deleted", "Body should remain unchanged"


@pytest.mark.asyncio
async def test_moderation_state_persists(db_session: AsyncSession):
    """Changing moderation_state to 'hidden' persists to the database."""
    user = await _seed_user(db_session)
    project = await _seed_project(db_session, user.id)

    comment = Comment(
        project_id=project.id,
        author_id=user.id,
        body="Inappropriate content",
    )
    db_session.add(comment)
    await db_session.commit()

    assert comment.moderation_state == "visible"

    comment.moderation_state = "hidden"
    db_session.add(comment)
    await db_session.commit()

    fetched = await db_session.get(Comment, comment.id)
    assert fetched is not None
    assert fetched.moderation_state == "hidden"


@pytest.mark.asyncio
async def test_project_id_index_allows_selective_query(db_session: AsyncSession):
    """Comments can be filtered by project_id (index is in use)."""
    user = await _seed_user(db_session)
    project_a = await _seed_project(db_session, user.id)
    project_b = await _seed_project(db_session, user.id)

    comment_a = Comment(project_id=project_a.id, author_id=user.id, body="Project A comment")
    comment_b = Comment(project_id=project_b.id, author_id=user.id, body="Project B comment")
    db_session.add(comment_a)
    db_session.add(comment_b)
    await db_session.commit()

    result = await db_session.exec(
        select(Comment).where(Comment.project_id == project_a.id)
    )
    project_a_comments = result.all()

    ids = [c.id for c in project_a_comments]
    assert comment_a.id in ids
    assert comment_b.id not in ids
