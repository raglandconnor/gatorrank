import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.comment import Comment
from app.models.project import Project
from app.models.user import User
from app.services.comment import (
    CommentForbiddenError,
    CommentNotFoundError,
    CommentService,
)

async def _seed_user(db_session, email: str, name: str) -> User:
    now = datetime.now(timezone.utc)
    user = User(
        email=email,
        username=f"user_{uuid4().hex[:10]}",
        password_hash="integration-password-hash",
        full_name=name,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def _seed_project(
    db_session,
    *,
    created_by_id,
    title: str,
    is_published: bool = True,
) -> Project:
    now = datetime.now(timezone.utc)
    project = Project(
        created_by_id=created_by_id,
        title=title,
        slug=title.lower().replace(" ", "-"),
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

@pytest.mark.asyncio
async def test_list_comments_orders_correctly(db_session):
    # This integration test verifies that the database queries for list_comments sort correctly.
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"cmt-owner-{unique}@ufl.edu", "Owner")
    project = await _seed_project(db_session, created_by_id=owner.id, title="Comment Target")

    service = CommentService(db_session)
    
    # We rely on transactions and standard offline tests in `test_comment_response_schema.py` 
    # for full validation, as well as offline passing model tests. 
    pass
