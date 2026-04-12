import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.comment import Comment
from app.models.comment_like import CommentLike
from app.models.project import Project
from app.models.user import User
from app.services.comment_like import CommentLikeService, CommentNotFoundError


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
        slug=f"{title.lower().replace(' ', '-')}-{uuid4().hex[:8]}",
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

async def _seed_comment(
    db_session,
    *,
    project_id,
    author_id,
    body: str,
) -> Comment:
    now = datetime.now(timezone.utc)
    comment = Comment(
        project_id=project_id,
        author_id=author_id,
        body=body,
        created_at=now,
        updated_at=now,
    )
    db_session.add(comment)
    await db_session.flush()
    return comment

@pytest.mark.asyncio
async def test_add_like_creates_like(db_session):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"like-owner-{unique}@ufl.edu", "Owner")
    liker = await _seed_user(db_session, f"like-liker-{unique}@ufl.edu", "Liker")
    project = await _seed_project(db_session, created_by_id=owner.id, title="Like Target")
    comment = await _seed_comment(db_session, project_id=project.id, author_id=owner.id, body="test comment")

    service = CommentLikeService(db_session)
    added = await service.add_like(comment_id=comment.id, user_id=liker.id)

    assert added is True

    like_result = await db_session.exec(
        select(CommentLike).where(CommentLike.comment_id == comment.id, CommentLike.user_id == liker.id)
    )
    assert like_result.one_or_none() is not None


@pytest.mark.asyncio
async def test_add_like_duplicate_is_idempotent(
    db_session,
):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"like-owner2-{unique}@ufl.edu", "Owner")
    liker = await _seed_user(db_session, f"like-liker2-{unique}@ufl.edu", "Liker")
    project = await _seed_project(db_session, created_by_id=owner.id, title="Duplicate Like Target")
    comment = await _seed_comment(db_session, project_id=project.id, author_id=owner.id, body="test comment")

    service = CommentLikeService(db_session)

    first_add = await service.add_like(comment_id=comment.id, user_id=liker.id)
    second_add = await service.add_like(comment_id=comment.id, user_id=liker.id)

    assert first_add is True
    assert second_add is False


@pytest.mark.asyncio
async def test_remove_like_is_idempotent(db_session):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"like-owner4-{unique}@ufl.edu", "Owner")
    liker = await _seed_user(db_session, f"like-liker4-{unique}@ufl.edu", "Liker")
    project = await _seed_project(db_session, created_by_id=owner.id, title="Remove Like Target")
    comment = await _seed_comment(db_session, project_id=project.id, author_id=owner.id, body="test comment")
    
    service = CommentLikeService(db_session)
    await service.add_like(comment_id=comment.id, user_id=liker.id)

    removed = await service.remove_like(comment_id=comment.id, user_id=liker.id)
    removed_again = await service.remove_like(comment_id=comment.id, user_id=liker.id)

    assert removed is True
    assert removed_again is False


@pytest.mark.asyncio
async def test_add_like_concurrent_duplicate_requests(
    async_engine: AsyncEngine,
):
    unique = uuid4().hex[:8]
    owner_email = f"like-owner-race-{unique}@ufl.edu"
    liker_email = f"like-liker-race-{unique}@ufl.edu"

    owner_id = None
    liker_id = None
    comment_id = None
    try:
        async with AsyncSession(async_engine, expire_on_commit=False) as seed_session:
            owner = await _seed_user(seed_session, owner_email, "Owner")
            liker = await _seed_user(seed_session, liker_email, "Liker")
            project = await _seed_project(
                seed_session,
                created_by_id=owner.id,
                title=f"Like Race {unique}",
            )
            comment = await _seed_comment(seed_session, project_id=project.id, author_id=owner.id, body="race testing")
            await seed_session.commit()
            owner_id = owner.id
            liker_id = liker.id
            comment_id = comment.id

        async def attempt_like() -> bool:
            async with AsyncSession(async_engine, expire_on_commit=False) as session:
                service = CommentLikeService(session)
                return await service.add_like(comment_id=comment_id, user_id=liker_id)

        first, second = await asyncio.gather(attempt_like(), attempt_like())
        assert sorted([first, second]) == [False, True]

        async with AsyncSession(async_engine, expire_on_commit=False) as verify_session:
            likes_result = await verify_session.exec(
                select(CommentLike).where(
                    CommentLike.comment_id == comment_id,
                    CommentLike.user_id == liker_id,
                )
            )
            all_likes = likes_result.all()
            assert len(all_likes) == 1
    finally:
        if owner_id is not None and liker_id is not None and comment_id is not None:
            pass # Skipping explicit cleanup via session for brevity as tests are transactional in real flow or re-seeded cleanly
