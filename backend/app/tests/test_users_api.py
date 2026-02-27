from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_user
from app.db.database import get_db
from app.main import app
from app.models.user import User
from app.schemas.project import ProjectListResponse

client = TestClient(app)


async def _override_get_db():
    class MockSession:
        pass

    yield MockSession()


def _override_current_user(user_id: UUID, email: str = "test@example.com"):
    # Return a mock User-like object
    class MockUser:
        def __init__(self, id, email, full_name=None, profile_picture_url=None):
            self.id = id
            self.email = email
            self.role = "student"
            self.full_name = full_name
            self.profile_picture_url = profile_picture_url

            from datetime import datetime, timezone

            self.created_at = datetime.now(timezone.utc)
            self.updated_at = datetime.now(timezone.utc)

    return lambda: MockUser(user_id, email, "Test User", "http://example.com/pic.jpg")


def test_get_current_user_profile():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        response = client.get("/api/v1/users/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(user_id)
    assert payload["email"] == "test@example.com"
    assert payload["full_name"] == "Test User"
    assert "updated_at" in payload


def test_update_current_user_profile():
    user_id = uuid4()

    # We mock UserService.update_user
    # returning a UserPrivate matched shape
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    updated_user = User(
        id=user_id,
        email="test@example.com",
        full_name="New Name",
        profile_picture_url="http://new.pic",
        role="student",
        created_at=now,
        updated_at=now,
    )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.users.UserService.update_user",
            new=AsyncMock(return_value=updated_user),
        ) as mock_update:
            response = client.patch(
                "/api/v1/users/me",
                json={"full_name": "New Name", "profile_picture_url": "http://new.pic"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["full_name"] == "New Name"
    assert payload["profile_picture_url"] == "http://new.pic"
    assert mock_update.await_count == 1


def test_update_current_user_requires_full_name():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        response = client.patch(
            "/api/v1/users/me", json={"profile_picture_url": "http://new.pic"}
        )
    finally:
        app.dependency_overrides.clear()

    # Pydantic returns 422 if full_name is missing
    assert response.status_code == 422


def test_get_user_profile():
    target_user_id = uuid4()

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    target_user = User(
        id=target_user_id,
        email="hidden@example.com",
        full_name="Target User",
        profile_picture_url=None,
        role="student",
        created_at=now,
        updated_at=now,
    )

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with patch(
            "app.api.v1.users.UserService.get_user_by_id",
            new=AsyncMock(return_value=target_user),
        ):
            response = client.get(f"/api/v1/users/{target_user_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(target_user_id)
    assert payload["full_name"] == "Target User"
    assert "email" not in payload
    assert "updated_at" not in payload


def test_get_user_profile_not_found():
    target_user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with patch(
            "app.api.v1.users.UserService.get_user_by_id",
            new=AsyncMock(return_value=None),
        ):
            response = client.get(f"/api/v1/users/{target_user_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_list_user_projects():
    target_user_id = uuid4()

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    target_user = User(
        id=target_user_id,
        email="test@test.com",
        created_at=now,
        updated_at=now,
    )

    empty_project_list = ProjectListResponse(items=[], next_cursor=None)

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with (
            patch(
                "app.api.v1.users.UserService.get_user_by_id",
                new=AsyncMock(return_value=target_user),
            ),
            patch(
                "app.api.v1.users.ProjectService.list_projects",
                new=AsyncMock(return_value=empty_project_list),
            ) as mock_list_projects,
        ):
            response = client.get(f"/api/v1/users/{target_user_id}/projects?limit=10")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"] == []

    await_args = mock_list_projects.await_args
    assert await_args is not None
    assert await_args.kwargs["created_by_id"] == target_user_id
    assert await_args.kwargs["limit"] == 10


def test_list_user_projects_user_not_found():
    target_user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with patch(
            "app.api.v1.users.UserService.get_user_by_id",
            new=AsyncMock(return_value=None),
        ):
            response = client.get(f"/api/v1/users/{target_user_id}/projects")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
