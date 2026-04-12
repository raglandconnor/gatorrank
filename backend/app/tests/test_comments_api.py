from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_user
from app.db.database import get_db
from app.main import app
from app.models.user import User
from app.services.comment_domain import CommentNotFoundError

client = TestClient(app)


async def _override_get_db():
    class MockSession:
        pass

    yield MockSession()


def _build_user() -> User:
    now = datetime.now(UTC)
    return User(  # pyright: ignore[reportCallIssue]
        id=uuid4(),
        email="comments-api@ufl.edu",
        username="comments_api_user",
        password_hash="test-password-hash",
        role="student",
        full_name="Comments User",
        created_at=now,
        updated_at=now,
    )


def test_like_comment_requires_authentication():
    response = client.post(f"/api/v1/comments/{uuid4()}/like")
    assert response.status_code == 401


def test_like_comment_returns_204_for_authenticated_user():
    user = _build_user()
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with patch(
            "app.api.v1.comments.CommentLikeService.add_like",
            new=AsyncMock(return_value=True),
        ):
            response = client.post(f"/api/v1/comments/{uuid4()}/like")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""


def test_like_comment_returns_404_when_comment_missing():
    user = _build_user()
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with patch(
            "app.api.v1.comments.CommentLikeService.add_like",
            new=AsyncMock(side_effect=CommentNotFoundError("Comment not found")),
        ):
            response = client.post(f"/api/v1/comments/{uuid4()}/like")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Comment not found"


def test_unlike_comment_returns_204_for_authenticated_user():
    user = _build_user()
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with patch(
            "app.api.v1.comments.CommentLikeService.remove_like",
            new=AsyncMock(return_value=False),
        ):
            response = client.delete(f"/api/v1/comments/{uuid4()}/like")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""


def test_comments_like_openapi_metadata_is_present():
    openapi = app.openapi()
    paths = openapi["paths"]

    like_operation = paths["/api/v1/comments/{comment_id}/like"]["post"]
    assert like_operation["summary"] == "Like a comment"
    assert like_operation["description"]
    assert {"204", "401", "404"}.issubset(like_operation["responses"].keys())

    unlike_operation = paths["/api/v1/comments/{comment_id}/like"]["delete"]
    assert unlike_operation["summary"] == "Unlike a comment"
    assert unlike_operation["description"]
    assert {"204", "401", "404"}.issubset(unlike_operation["responses"].keys())

    list_operation = paths["/api/v1/projects/{project_id}/comments"]["get"]
    assert list_operation["summary"] == "List project comments"
    assert list_operation["description"]
    assert "404" in list_operation["responses"]

    create_operation = paths["/api/v1/projects/{project_id}/comments"]["post"]
    assert create_operation["summary"] == "Create project comment"
    assert create_operation["description"]
    assert {"201", "401", "404", "422"}.issubset(create_operation["responses"].keys())

    delete_operation = paths["/api/v1/comments/{comment_id}"]["delete"]
    assert delete_operation["summary"] == "Delete own comment"
    assert delete_operation["description"]
    assert {"204", "401", "403", "404"}.issubset(delete_operation["responses"].keys())

    moderate_operation = paths["/api/v1/comments/{comment_id}/moderation"]["patch"]
    assert moderate_operation["summary"] == "Update comment moderation state"
    assert moderate_operation["description"]
    assert {"204", "401", "403", "404", "422"}.issubset(
        moderate_operation["responses"].keys()
    )
