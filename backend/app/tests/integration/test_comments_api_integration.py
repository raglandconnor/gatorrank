from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import select

from app.api.deps.auth import get_current_user, get_current_user_optional
from app.db.database import get_db
from app.main import app
from app.models.comment import COMMENT_MODERATION_HIDDEN
from app.models.comment_like import CommentLike
from app.tests.integration.comment_test_helpers import (
    override_get_db_factory,
    seed_comment_like,
    seed_comment_project,
    seed_comment_user,
    seed_project_comment,
)


@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_list_comments_is_public_and_includes_viewer_state(
    api_client, db_session
):
    unique = uuid4().hex[:8]
    owner = await seed_comment_user(
        db_session, email=f"api-owner-{unique}@ufl.edu", name="Owner"
    )
    viewer = await seed_comment_user(
        db_session, email=f"api-viewer-{unique}@ufl.edu", name="Viewer"
    )
    project = await seed_comment_project(
        db_session, created_by_id=owner.id, title="API Visible"
    )
    comment = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="Great project",
    )
    await seed_comment_like(db_session, comment_id=comment.id, user_id=viewer.id)
    await db_session.commit()

    app.dependency_overrides[get_db] = override_get_db_factory(db_session)
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        anonymous_response = await api_client.get(
            f"/api/v1/projects/{project.id}/comments"
        )
        app.dependency_overrides[get_current_user_optional] = lambda: viewer
        viewer_response = await api_client.get(
            f"/api/v1/projects/{project.id}/comments"
        )
    finally:
        app.dependency_overrides.clear()

    assert anonymous_response.status_code == 200
    anonymous_payload = anonymous_response.json()
    assert anonymous_payload[0]["like_count"] == 1
    assert anonymous_payload[0]["viewer_has_liked"] is False

    assert viewer_response.status_code == 200
    viewer_payload = viewer_response.json()
    assert viewer_payload[0]["viewer_has_liked"] is True
    assert viewer_payload[0]["author"]["user_id"] == str(owner.id)


@pytest.mark.asyncio
async def test_create_comment_requires_auth_and_returns_created_payload(
    api_client, db_session
):
    unique = uuid4().hex[:8]
    owner = await seed_comment_user(
        db_session, email=f"api-create-{unique}@ufl.edu", name="Owner"
    )
    project = await seed_comment_project(
        db_session, created_by_id=owner.id, title="API Create"
    )
    await db_session.commit()

    app.dependency_overrides[get_db] = override_get_db_factory(db_session)
    try:
        unauthenticated_response = await api_client.post(
            f"/api/v1/projects/{project.id}/comments",
            json={"body": "Hello world"},
        )
        app.dependency_overrides[get_current_user] = lambda: owner
        created_response = await api_client.post(
            f"/api/v1/projects/{project.id}/comments",
            json={"body": "  Hello world  "},
        )
    finally:
        app.dependency_overrides.clear()

    assert unauthenticated_response.status_code == 401
    assert created_response.status_code == 201
    payload = created_response.json()
    assert payload["body"] == "Hello world"
    assert payload["author"]["user_id"] == str(owner.id)
    assert payload["like_count"] == 0
    assert payload["viewer_has_liked"] is False


@pytest.mark.asyncio
async def test_list_comments_honors_sorting_and_placeholder_behavior(
    api_client, db_session
):
    unique = uuid4().hex[:8]
    owner = await seed_comment_user(
        db_session, email=f"api-sort-{unique}@ufl.edu", name="Owner"
    )
    liker = await seed_comment_user(
        db_session, email=f"api-sort-l-{unique}@ufl.edu", name="Liker"
    )
    project = await seed_comment_project(
        db_session, created_by_id=owner.id, title="API Sort"
    )
    now = datetime.now(timezone.utc)
    hidden_comment = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="hidden",
        created_at=now - timedelta(hours=2),
        moderation_state=COMMENT_MODERATION_HIDDEN,
    )
    deleted_comment = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="deleted",
        created_at=now - timedelta(hours=1),
        deleted_at=now,
    )
    top_comment = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="top comment",
        created_at=now - timedelta(minutes=30),
    )
    await seed_comment_like(db_session, comment_id=top_comment.id, user_id=owner.id)
    await seed_comment_like(db_session, comment_id=top_comment.id, user_id=liker.id)
    await db_session.commit()

    app.dependency_overrides[get_db] = override_get_db_factory(db_session)
    app.dependency_overrides[get_current_user_optional] = lambda: liker
    try:
        top_response = await api_client.get(f"/api/v1/projects/{project.id}/comments")
        oldest_response = await api_client.get(
            f"/api/v1/projects/{project.id}/comments",
            params={"sort": "oldest"},
        )
    finally:
        app.dependency_overrides.clear()

    assert top_response.status_code == 200
    top_payload = top_response.json()
    assert [item["id"] for item in top_payload] == [
        str(top_comment.id),
        str(deleted_comment.id),
        str(hidden_comment.id),
    ]
    assert top_payload[1]["is_deleted"] is True
    assert top_payload[1]["author"]["user_id"] is None
    assert top_payload[2]["is_hidden"] is True
    assert top_payload[2]["author"]["user_id"] is None

    assert oldest_response.status_code == 200
    oldest_payload = oldest_response.json()
    assert [item["id"] for item in oldest_payload] == [
        str(hidden_comment.id),
        str(deleted_comment.id),
        str(top_comment.id),
    ]


@pytest.mark.asyncio
async def test_delete_comment_and_admin_moderation_endpoints(api_client, db_session):
    unique = uuid4().hex[:8]
    owner = await seed_comment_user(
        db_session, email=f"api-del-owner-{unique}@ufl.edu", name="Owner"
    )
    other_user = await seed_comment_user(
        db_session, email=f"api-del-other-{unique}@ufl.edu", name="Other User"
    )
    admin = await seed_comment_user(
        db_session,
        email=f"api-del-admin-{unique}@ufl.edu",
        name="Admin",
        role="admin",
    )
    project = await seed_comment_project(
        db_session, created_by_id=owner.id, title="API Delete"
    )
    own_comment = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="delete me",
    )
    moderated_comment = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=other_user.id,
        body="moderate me",
    )
    await db_session.commit()

    app.dependency_overrides[get_db] = override_get_db_factory(db_session)
    try:
        app.dependency_overrides[get_current_user] = lambda: other_user
        forbidden_delete = await api_client.delete(f"/api/v1/comments/{own_comment.id}")

        app.dependency_overrides[get_current_user] = lambda: owner
        own_delete = await api_client.delete(f"/api/v1/comments/{own_comment.id}")

        app.dependency_overrides[get_current_user] = lambda: other_user
        forbidden_moderation = await api_client.patch(
            f"/api/v1/comments/{moderated_comment.id}/moderation",
            json={"moderation_state": "hidden"},
        )

        app.dependency_overrides[get_current_user] = lambda: admin
        hidden_response = await api_client.patch(
            f"/api/v1/comments/{moderated_comment.id}/moderation",
            json={"moderation_state": "hidden"},
        )
        moderator_delete = await api_client.delete(
            f"/api/v1/comments/{moderated_comment.id}/moderation"
        )
    finally:
        app.dependency_overrides.clear()

    assert forbidden_delete.status_code == 403
    assert own_delete.status_code == 204
    assert forbidden_moderation.status_code == 403
    assert hidden_response.status_code == 204
    assert moderator_delete.status_code == 204


@pytest.mark.asyncio
async def test_list_comments_rejects_unpublished_project(api_client, db_session):
    unique = uuid4().hex[:8]
    owner = await seed_comment_user(
        db_session, email=f"api-draft-{unique}@ufl.edu", name="Owner"
    )
    draft_project = await seed_comment_project(
        db_session,
        created_by_id=owner.id,
        title="API Draft",
        is_published=False,
    )
    await db_session.commit()

    app.dependency_overrides[get_db] = override_get_db_factory(db_session)
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get(f"/api/v1/projects/{draft_project.id}/comments")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mutation_endpoints_return_404_for_unpublished_project_comments(
    api_client, db_session
):
    unique = uuid4().hex[:8]
    owner = await seed_comment_user(
        db_session, email=f"api-mut-owner-{unique}@ufl.edu", name="Owner"
    )
    liker = await seed_comment_user(
        db_session, email=f"api-mut-liker-{unique}@ufl.edu", name="Liker"
    )
    admin = await seed_comment_user(
        db_session,
        email=f"api-mut-admin-{unique}@ufl.edu",
        name="Admin",
        role="admin",
    )
    project = await seed_comment_project(
        db_session,
        created_by_id=owner.id,
        title="API Hidden Mutations",
        is_published=False,
    )
    comment = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="cannot mutate me",
    )
    await db_session.commit()

    app.dependency_overrides[get_db] = override_get_db_factory(db_session)
    try:
        app.dependency_overrides[get_current_user] = lambda: liker
        like_response = await api_client.post(f"/api/v1/comments/{comment.id}/like")
        unlike_response = await api_client.delete(f"/api/v1/comments/{comment.id}/like")

        app.dependency_overrides[get_current_user] = lambda: owner
        delete_response = await api_client.delete(f"/api/v1/comments/{comment.id}")

        app.dependency_overrides[get_current_user] = lambda: admin
        moderation_response = await api_client.patch(
            f"/api/v1/comments/{comment.id}/moderation",
            json={"moderation_state": "hidden"},
        )
        moderator_delete_response = await api_client.delete(
            f"/api/v1/comments/{comment.id}/moderation"
        )
    finally:
        app.dependency_overrides.clear()

    assert like_response.status_code == 404
    assert unlike_response.status_code == 404
    assert delete_response.status_code == 404
    assert moderation_response.status_code == 404
    assert moderator_delete_response.status_code == 404


@pytest.mark.asyncio
async def test_like_endpoint_does_not_create_like_for_deleted_project_comment(
    api_client, db_session
):
    unique = uuid4().hex[:8]
    owner = await seed_comment_user(
        db_session, email=f"api-like-owner-{unique}@ufl.edu", name="Owner"
    )
    liker = await seed_comment_user(
        db_session, email=f"api-like-liker-{unique}@ufl.edu", name="Liker"
    )
    project = await seed_comment_project(
        db_session, created_by_id=owner.id, title="API Deleted Like Project"
    )
    comment = await seed_project_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="should not gain likes",
    )
    project.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    app.dependency_overrides[get_db] = override_get_db_factory(db_session)
    app.dependency_overrides[get_current_user] = lambda: liker
    try:
        response = await api_client.post(f"/api/v1/comments/{comment.id}/like")
    finally:
        app.dependency_overrides.clear()

    likes_result = await db_session.exec(
        select(CommentLike).where(CommentLike.comment_id == comment.id)
    )

    assert response.status_code == 404
    assert likes_result.all() == []
