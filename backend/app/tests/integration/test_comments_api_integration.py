from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps.auth import get_current_user, get_current_user_optional
from app.db.database import get_db
from app.main import app
from app.models.comment import COMMENT_MODERATION_HIDDEN, Comment
from app.models.comment_like import CommentLike
from app.models.project import Project
from app.models.user import User


@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def _seed_user(db_session, email: str, name: str, role: str = "student") -> User:
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


def _override_get_db_factory(db_session):
    async def override_get_db():
        yield db_session

    return override_get_db


@pytest.mark.asyncio
async def test_list_comments_is_public_and_includes_viewer_state(
    api_client, db_session
):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"api-owner-{unique}@ufl.edu", "Owner")
    viewer = await _seed_user(db_session, f"api-viewer-{unique}@ufl.edu", "Viewer")
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="API Visible"
    )
    comment = await _seed_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="Great project",
    )
    await _seed_like(db_session, comment_id=comment.id, user_id=viewer.id)
    await db_session.commit()

    app.dependency_overrides[get_db] = _override_get_db_factory(db_session)
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
    owner = await _seed_user(db_session, f"api-create-{unique}@ufl.edu", "Owner")
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="API Create"
    )
    await db_session.commit()

    app.dependency_overrides[get_db] = _override_get_db_factory(db_session)
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
    owner = await _seed_user(db_session, f"api-sort-{unique}@ufl.edu", "Owner")
    liker = await _seed_user(db_session, f"api-sort-l-{unique}@ufl.edu", "Liker")
    project = await _seed_project(db_session, created_by_id=owner.id, title="API Sort")
    now = datetime.now(timezone.utc)
    hidden_comment = await _seed_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="hidden",
        created_at=now - timedelta(hours=2),
        moderation_state=COMMENT_MODERATION_HIDDEN,
    )
    deleted_comment = await _seed_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="deleted",
        created_at=now - timedelta(hours=1),
        deleted_at=now,
    )
    top_comment = await _seed_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="top comment",
        created_at=now - timedelta(minutes=30),
    )
    await _seed_like(db_session, comment_id=top_comment.id, user_id=owner.id)
    await _seed_like(db_session, comment_id=top_comment.id, user_id=liker.id)
    await db_session.commit()

    app.dependency_overrides[get_db] = _override_get_db_factory(db_session)
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
    owner = await _seed_user(db_session, f"api-del-owner-{unique}@ufl.edu", "Owner")
    other_user = await _seed_user(
        db_session, f"api-del-other-{unique}@ufl.edu", "Other User"
    )
    admin = await _seed_user(
        db_session, f"api-del-admin-{unique}@ufl.edu", "Admin", role="admin"
    )
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="API Delete"
    )
    own_comment = await _seed_comment(
        db_session,
        project_id=project.id,
        author_id=owner.id,
        body="delete me",
    )
    moderated_comment = await _seed_comment(
        db_session,
        project_id=project.id,
        author_id=other_user.id,
        body="moderate me",
    )
    await db_session.commit()

    app.dependency_overrides[get_db] = _override_get_db_factory(db_session)
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
    owner = await _seed_user(db_session, f"api-draft-{unique}@ufl.edu", "Owner")
    draft_project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="API Draft",
        is_published=False,
    )
    await db_session.commit()

    app.dependency_overrides[get_db] = _override_get_db_factory(db_session)
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get(f"/api/v1/projects/{draft_project.id}/comments")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
