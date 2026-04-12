from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.comment import (
    COMMENT_MODERATION_HIDDEN,
    Comment,
    CommentModerationState,
)
from app.schemas.comment import CommentCreateRequest
from app.services.comment import (
    COMMENT_LIST_HARD_CAP,
    CommentForbiddenError,
    CommentNotFoundError,
    CommentProjectNotFoundError,
    CommentService,
)
from app.tests.integration.comment_test_helpers import (
    seed_comment_like,
    seed_comment_project,
    seed_comment_user,
    seed_project_comment,
)


@pytest.mark.asyncio
async def test_list_comments_supports_top_oldest_and_newest_sorting(
    db_session: AsyncSession,
):
    unique = uuid4().hex[:8]
    owner = await seed_comment_user(
        db_session, email=f"svc-owner-{unique}@ufl.edu", name="Owner"
    )
    liker = await seed_comment_user(
        db_session, email=f"svc-liker-{unique}@ufl.edu", name="Liker"
    )
    project = await seed_comment_project(
        db_session, created_by_id=owner.id, title="Svc Sort"
    )

    now = datetime.now(timezone.utc)
    oldest = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="oldest",
        created_at=now - timedelta(hours=3),
    )
    middle = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="middle",
        created_at=now - timedelta(hours=2),
    )
    newest = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="newest",
        created_at=now - timedelta(hours=1),
    )
    await seed_comment_like(db_session, comment_id=middle.id, user_id=liker.id)
    await seed_comment_like(db_session, comment_id=middle.id, user_id=owner.id)
    await seed_comment_like(db_session, comment_id=oldest.id, user_id=liker.id)
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
    assert [comment.id for comment in oldest_comments] == [
        oldest.id,
        middle.id,
        newest.id,
    ]

    newest_comments = await service.list_comments(
        project_id=project.id, viewer_id=liker.id, sort_by="newest"
    )
    assert [comment.id for comment in newest_comments] == [
        newest.id,
        middle.id,
        oldest.id,
    ]


@pytest.mark.asyncio
async def test_list_comments_enforces_hard_cap(db_session: AsyncSession):
    unique = uuid4().hex[:8]
    owner = await seed_comment_user(
        db_session, email=f"svc-cap-{unique}@ufl.edu", name="Owner"
    )
    project = await seed_comment_project(
        db_session, created_by_id=owner.id, title="Svc Cap"
    )

    base_time = datetime.now(timezone.utc) - timedelta(
        minutes=COMMENT_LIST_HARD_CAP + 5
    )
    for index in range(COMMENT_LIST_HARD_CAP + 5):
        await seed_project_comment(
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
    owner = await seed_comment_user(
        db_session, email=f"svc-draft-{unique}@ufl.edu", name="Owner"
    )
    draft_project = await seed_comment_project(
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
    owner = await seed_comment_user(
        db_session, email=f"svc-owner-del-{unique}@ufl.edu", name="Owner"
    )
    other_user = await seed_comment_user(
        db_session, email=f"svc-other-del-{unique}@ufl.edu", name="Other User"
    )
    project = await seed_comment_project(
        db_session, created_by_id=owner.id, title="Svc Delete Permissions"
    )
    comment = await seed_project_comment(
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
async def test_comment_mutations_reject_unpublished_project_comments(
    db_session: AsyncSession,
):
    unique = uuid4().hex[:8]
    owner = await seed_comment_user(
        db_session, email=f"svc-hidden-{unique}@ufl.edu", name="Owner"
    )
    project = await seed_comment_project(
        db_session,
        created_by_id=owner.id,
        title="Svc Hidden Mutations",
        is_published=False,
    )
    comment = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="hidden mutations",
    )
    await db_session.commit()

    service = CommentService(db_session)

    with pytest.raises(CommentNotFoundError, match="Comment not found"):
        await service.delete_own_comment(comment_id=comment.id, actor_id=owner.id)

    with pytest.raises(CommentNotFoundError, match="Comment not found"):
        await service.moderate_comment(
            comment_id=comment.id,
            moderation_state=CommentModerationState.HIDDEN,
            principal=owner,
        )

    with pytest.raises(CommentNotFoundError, match="Comment not found"):
        await service.moderator_delete_comment(comment_id=comment.id, principal=owner)


@pytest.mark.asyncio
async def test_comment_mutations_reject_deleted_project_comments(
    db_session: AsyncSession,
):
    unique = uuid4().hex[:8]
    owner = await seed_comment_user(
        db_session, email=f"svc-deleted-{unique}@ufl.edu", name="Owner"
    )
    project = await seed_comment_project(
        db_session, created_by_id=owner.id, title="Svc Deleted Mutations"
    )
    comment = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="deleted mutations",
    )
    project.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    service = CommentService(db_session)

    with pytest.raises(CommentNotFoundError, match="Comment not found"):
        await service.delete_own_comment(comment_id=comment.id, actor_id=owner.id)

    with pytest.raises(CommentNotFoundError, match="Comment not found"):
        await service.moderate_comment(
            comment_id=comment.id,
            moderation_state=CommentModerationState.HIDDEN,
            principal=owner,
        )

    with pytest.raises(CommentNotFoundError, match="Comment not found"):
        await service.moderator_delete_comment(comment_id=comment.id, principal=owner)


@pytest.mark.asyncio
async def test_service_level_moderation_requires_admin_principal(
    db_session: AsyncSession,
):
    unique = uuid4().hex[:8]
    owner = await seed_comment_user(
        db_session, email=f"svc-mod-owner-{unique}@ufl.edu", name="Owner"
    )
    student = await seed_comment_user(
        db_session, email=f"svc-mod-student-{unique}@ufl.edu", name="Student"
    )
    admin = await seed_comment_user(
        db_session,
        email=f"svc-mod-admin-{unique}@ufl.edu",
        name="Admin",
        role="admin",
    )
    project = await seed_comment_project(
        db_session, created_by_id=owner.id, title="Svc Moderation Policy"
    )
    comment = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="moderate me",
    )
    await db_session.commit()

    service = CommentService(db_session)

    with pytest.raises(CommentForbiddenError, match="Comment moderation forbidden"):
        await service.moderate_comment(
            comment_id=comment.id,
            moderation_state=CommentModerationState.HIDDEN,
            principal=student,
        )

    await service.moderate_comment(
        comment_id=comment.id,
        moderation_state=CommentModerationState.HIDDEN,
        principal=admin,
    )
    await service.moderator_delete_comment(comment_id=comment.id, principal=admin)

    refreshed_comment = await db_session.get(Comment, comment.id)
    assert refreshed_comment is not None
    assert refreshed_comment.moderation_state == CommentModerationState.HIDDEN
    assert refreshed_comment.deleted_at is not None


@pytest.mark.asyncio
async def test_hidden_and_deleted_comments_remain_placeholder_ready(
    db_session: AsyncSession,
):
    unique = uuid4().hex[:8]
    owner = await seed_comment_user(
        db_session, email=f"svc-ph-{unique}@ufl.edu", name="Owner"
    )
    project = await seed_comment_project(
        db_session, created_by_id=owner.id, title="Svc Placeholder"
    )
    hidden = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="hidden body",
        moderation_state=COMMENT_MODERATION_HIDDEN,
    )
    deleted = await seed_project_comment(
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
