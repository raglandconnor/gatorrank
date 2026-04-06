import pytest
import pytest_asyncio
from uuid import uuid4
from httpx import ASGITransport, AsyncClient
import sqlalchemy as sa
import jwt
from datetime import UTC, datetime, timedelta

from app.main import app
from app.db.database import get_db
from app.models.user import User
from app.models.project import Project, Vote
from app.core.config import get_settings
from app.services.vote import VoteService

settings = get_settings()


@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


def generate_token(user_id, email, jwt_secret):
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "email": email,
            "aud": "authenticated",
            "iat": int(now.timestamp()),
            "exp": now + timedelta(minutes=5),
        },
        jwt_secret,
        algorithm="HS256",
    )


async def seed_auth_user(
    db_session, *, user_id, email: str, username: str | None = None
) -> None:
    resolved_username = username or f"user_{uuid4().hex[:10]}"
    user = User(  # pyright: ignore[reportCallIssue]
        id=user_id,
        email=email,
        username=resolved_username,
        password_hash="integration-password-hash",
        role="student",
    )
    db_session.add(user)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_current_user_profile(api_client, db_session, monkeypatch):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    username = "profile_user"
    await seed_auth_user(db_session, user_id=user_id, email=email, username=username)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(user_id)
        assert data["email"] == email
        assert data["username"] == username
        assert data["full_name"] is None
        assert "updated_at" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_current_user_profile(api_client, db_session, monkeypatch):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "New Integration Name",
                "profile_picture_url": "https://example.com/pic.jpg",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "New Integration Name"
        assert data["profile_picture_url"] == "https://example.com/pic.jpg"

        # Verify DB
        db_user = await db_session.exec(sa.select(User).where(User.id == user_id))  # pyright: ignore[reportArgumentType]
        user_record = db_user.scalars().one()
        assert user_record.full_name == "New Integration Name"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_current_user_profile_partial_update(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "profile_picture_url": "https://example.com/partial.jpg",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] is None
        assert data["profile_picture_url"] == "https://example.com/partial.jpg"

        db_user = await db_session.exec(sa.select(User).where(User.id == user_id))  # pyright: ignore[reportArgumentType]
        user_record = db_user.scalars().one()
        assert user_record.full_name is None
        assert user_record.profile_picture_url == "https://example.com/partial.jpg"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_current_user_profile_empty_payload_returns_422(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_current_user_profile_invalid_url_returns_422(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"profile_picture_url": "invalid-url"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_current_user_profile_rejects_null_full_name(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        setup_response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Will Be Cleared"},
        )
        assert setup_response.status_code == 200

        response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": None},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_current_user_profile_rejects_username_update(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"username": "new_username"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_current_user_profile_unknown_user_returns_401(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_user_profile(api_client, db_session, monkeypatch):
    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"

    # Pre-insert user
    user = User(  # pyright: ignore[reportCallIssue]
        id=user_id,
        email=email,
        username="public_user",
        password_hash="integration-password-hash",
        full_name="Public User",
        role="student",
    )
    db_session.add(user)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(user_id)
        assert data["username"] == "public_user"
        assert data["full_name"] == "Public User"
        assert "email" not in data  # Public info
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_user_profile_by_username_case_insensitive(api_client, db_session):
    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    username = "public_lookup_user"

    user = User(  # pyright: ignore[reportCallIssue]
        id=user_id,
        email=email,
        username=username,
        password_hash="integration-password-hash",
        full_name="Public User",
        role="student",
    )
    db_session.add(user)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(f"/api/v1/users/by-username/{username.upper()}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(user_id)
        assert data["username"] == username
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_user_projects(api_client, db_session):
    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"

    # Pre-insert user and some projects
    user = User(  # pyright: ignore[reportCallIssue]
        id=user_id,
        email=email,
        username="author_user",
        password_hash="integration-password-hash",
        full_name="Author",
        role="student",
    )
    db_session.add(user)
    await db_session.commit()

    from datetime import datetime

    now = datetime.now(UTC)

    # Published project
    p1 = Project(
        id=uuid4(),
        title="Published Project",
        slug="published-project",
        short_description="Desc",
        is_published=True,
        published_at=now,
        created_by_id=user_id,
    )  # pyright: ignore[reportCallIssue]
    # Draft project (should not be returned)
    p2 = Project(
        id=uuid4(),
        title="Draft Project",
        slug="draft-project",
        short_description="Desc",
        is_published=False,
        created_by_id=user_id,
    )  # pyright: ignore[reportCallIssue]
    db_session.add_all([p1, p2])
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(f"/api/v1/users/{user_id}/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(p1.id)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_user_projects_by_username(api_client, db_session):
    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    username = "author_lookup_user"

    user = User(  # pyright: ignore[reportCallIssue]
        id=user_id,
        email=email,
        username=username,
        password_hash="integration-password-hash",
        full_name="Author",
        role="student",
    )
    db_session.add(user)
    await db_session.commit()

    now = datetime.now(UTC)
    p1 = Project(
        id=uuid4(),
        title="Published Project",
        slug="published-project",
        short_description="Desc",
        is_published=True,
        published_at=now,
        created_by_id=user_id,
    )  # pyright: ignore[reportCallIssue]
    p2 = Project(
        id=uuid4(),
        title="Draft Project",
        slug="draft-project",
        short_description="Desc",
        is_published=False,
        created_by_id=user_id,
    )  # pyright: ignore[reportCallIssue]
    db_session.add_all([p1, p2])
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            f"/api/v1/users/by-username/{username.upper()}/projects"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(p1.id)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_my_voted_projects_excludes_soft_deleted_projects(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-votes-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    now = datetime.now(UTC)
    visible = Project(
        id=uuid4(),
        title="Visible Voted Project",
        slug="visible-voted-project",
        short_description="Visible voted project description",
        is_published=True,
        published_at=now,
        created_by_id=user_id,
    )  # pyright: ignore[reportCallIssue]
    deleted = Project(
        id=uuid4(),
        title="Deleted Voted Project",
        slug="deleted-voted-project",
        short_description="Deleted voted project description",
        is_published=True,
        published_at=now,
        created_by_id=user_id,
        deleted_at=now,
    )  # pyright: ignore[reportCallIssue]
    db_session.add_all([visible, deleted])
    await db_session.commit()

    vote_service = VoteService(db_session)
    await vote_service.add_vote(project_id=visible.id, user_id=user_id)
    db_session.add(Vote(user_id=user_id, project_id=deleted.id, created_at=now))
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/api/v1/users/me/votes",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [str(visible.id)]
