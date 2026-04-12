from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.comment import COMMENT_MODERATION_HIDDEN, Comment
from app.models.comment_like import CommentLike
from app.models.project import Project
from app.models.user import User
from app.schemas.comment import CommentCreateRequest
from app.services.comment import (
    COMMENT_LIST_HARD_CAP,
    CommentForbiddenError,
    CommentProjectNotFoundError,
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


async def _seed_comment(
    db_session,
    *,
    project_id,
    author_id,
    body: str,
    created_at: datetime | None = None,
    moderation_state: str = "visible",
    deleted_at: datetime | None = None,
) -> Comment:
    now = created_at or datetime.now(timezone.utc)
    comment = Comment(
        project_id=project_id,
        author_id=author_id,
        body=body,
        moderation_state=moderation_state,
        deleted_at=deleted_at,
        created_at=now,
        updated_at=now,
    )
    db_session.add(comment)
    await db_session.flush()
    return comment


async def _seed_like(db_session, *, comment_id, user_id) -> CommentLike:
    like = CommentLike(
        comment_id=comment_id,
        user_id=user_id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(like)
    await db_session.flush()
    return like


@pytest.mark.asyncio
async def test_list_comments_supports_top_oldest_and_newest_sorting(
    db_session: AsyncSession,
):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"svc-owner-{unique}@ufl.edu", "Owner")
    liker = await _seed_user(db_session, f"svc-liker-{unique}@ufl.edu", "Liker")
    project = await _seed_project(db_session, created_by_id=owner.id, title="Svc Sort")

    now = datetime.now(timezone.utc)
    oldest = await _seed_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="oldest",
        created_at=now - timedelta(hours=3),
    )
    middle = await _seed_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="middle",
        created_at=now - timedelta(hours=2),
    )
    newest = await _seed_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="newest",
        created_at=now - timedelta(hours=1),
    )
    await _seed_like(db_session, comment_id=middle.id, user_id=liker.id)
    await _seed_like(db_session, comment_id=middle.id, user_id=owner.id)
    await _seed_like(db_session, comment_id=oldest.id, user_id=liker.id)
    await db_session.commit()

    service = CommentService(db_session)

    top_comments = await service.list_comments(
        project_id=project.id, viewer_id=liker.id, sort_by="top"
    )
    assert [comment.id for comment in top_comments] == [middle.id, oldest.id, newest.id]
    assert top_comments[0].like_count == 2
    assert top_comments[0].viewer_has_liked is True

    oldest_comments = await service.list_comments(
        project_id=project.id, viewer_id=liker.id, sort_by="oldest"
    )
    assert [comment.id for comment in oldest_comments] == [oldest.id, middle.id, newest.id]

    newest_comments = await service.list_comments(
        project_id=project.id, viewer_id=liker.id, sort_by="newest"
    )
    assert [comment.id for comment in newest_comments] == [newest.id, middle.id, oldest.id]


@pytest.mark.asyncio
async def test_list_comments_enforces_hard_cap(db_session: AsyncSession):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"svc-cap-{unique}@ufl.edu", "Owner")
    project = await _seed_project(db_session, created_by_id=owner.id, title="Svc Cap")

    base_time = datetime.now(timezone.utc) - timedelta(minutes=COMMENT_LIST_HARD_CAP + 5)
    for index in range(COMMENT_LIST_HARD_CAP + 5):
        await _seed_comment(
            db_session,
            project_id=project.id,
            author_id=owner.id,
            body=f"comment-{index}",
            created_at=base_time + timedelta(minutes=index),
        )
    await db_session.commit()

    service = CommentService(db_session)
    comments = await service.list_comments(project_id=project.id, sort_by="newest")

    assert len(comments) == COMMENT_LIST_HARD_CAP
    assert comments[0].body == f"comment-{COMMENT_LIST_HARD_CAP + 4}"
    assert comments[-1].body == "comment-5"


@pytest.mark.asyncio
async def test_create_comment_rejects_unpublished_project(db_session: AsyncSession):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"svc-draft-{unique}@ufl.edu", "Owner")
    draft_project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Svc Draft",
        is_published=False,
    )
    await db_session.commit()

    service = CommentService(db_session)
    with pytest.raises(CommentProjectNotFoundError, match="Project not found"):
        await service.create_comment(
            project_id=draft_project.id,
            author_id=owner.id,
            data=CommentCreateRequest(body="hello"),
        )


@pytest.mark.asyncio
async def test_delete_own_comment_forbids_non_author(db_session: AsyncSession):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"svc-owner-del-{unique}@ufl.edu", "Owner")
    other_user = await _seed_user(
        db_session, f"svc-other-del-{unique}@ufl.edu", "Other User"
    )
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="Svc Delete Permissions"
    )
    comment = await _seed_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="cannot delete me",
    )
    await db_session.commit()

    service = CommentService(db_session)
    with pytest.raises(CommentForbiddenError, match="Comment delete forbidden"):
        await service.delete_own_comment(comment_id=comment.id, actor_id=other_user.id)


@pytest.mark.asyncio
async def test_hidden_and_deleted_comments_remain_placeholder_ready(
    db_session: AsyncSession,
):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"svc-ph-{unique}@ufl.edu", "Owner")
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="Svc Placeholder"
    )
    hidden = await _seed_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="hidden body",
        moderation_state=COMMENT_MODERATION_HIDDEN,
    )
    deleted = await _seed_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="deleted body",
        deleted_at=datetime.now(timezone.utc),
    )
    await db_session.commit()

    service = CommentService(db_session)
    comments = await service.list_comments(project_id=project.id, sort_by="oldest")

    assert [comment.id for comment in comments] == [hidden.id, deleted.id]
    assert comments[0].is_hidden is True
    assert comments[1].is_deleted is True
