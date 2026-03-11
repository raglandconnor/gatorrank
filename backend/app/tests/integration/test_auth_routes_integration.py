from uuid import uuid4

import pytest
import pytest_asyncio
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.db.database import get_db
from app.main import app
from app.models.auth import RefreshSession
from app.models.user import User

settings = get_settings()


@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_signup_creates_user_and_returns_auth_payload(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"signup-{uuid4().hex[:8]}@ufl.edu"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": "valid-signup-password-123",
                "full_name": "Signup User",
                "remember_me": False,
            },
        )
        assert response.status_code == 201
        payload = response.json()
        assert payload["token_type"] == "bearer"
        assert payload["user"]["email"] == email
        assert payload["expires_in"] == 1800
        assert payload["refresh_token_expires_in"] == 1209600

        user_result = await db_session.exec(
            sa.select(User).where(User.email == email)  # pyright: ignore[reportArgumentType]
        )
        user = user_result.scalars().one_or_none()
        assert user is not None
        assert user.password_hash != "valid-signup-password-123"

        session_result = await db_session.exec(
            sa.select(RefreshSession).where(RefreshSession.user_id == user.id)  # pyright: ignore[reportArgumentType]
        )
        refresh_session = session_result.scalars().one_or_none()
        assert refresh_session is not None
        assert refresh_session.revoked_at is None
        assert refresh_session.token_hash != payload["refresh_token"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_returns_auth_payload_for_valid_credentials(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"login-{uuid4().hex[:8]}@ufl.edu"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        signup = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": "valid-login-password-123",
                "remember_me": True,
            },
        )
        assert signup.status_code == 201

        response = await api_client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "valid-login-password-123",
                "remember_me": True,
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["user"]["email"] == email
        assert payload["refresh_token_expires_in"] == 15552000
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_invalid_credentials_returns_401(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.post(
            "/api/v1/auth/login",
            json={
                "email": f"missing-{uuid4().hex[:8]}@ufl.edu",
                "password": "missing-password-123",
            },
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_auth_me_uses_issued_access_token(api_client, db_session, monkeypatch):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"me-{uuid4().hex[:8]}@ufl.edu"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        signup = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": "valid-me-password-123",
            },
        )
        assert signup.status_code == 201
        access_token = signup.json()["access_token"]

        response = await api_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["email"] == email
        assert "created_at" in payload
        assert "updated_at" in payload
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_refresh_rotates_and_logout_is_idempotent(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"refresh-{uuid4().hex[:8]}@ufl.edu"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        signup = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": "valid-refresh-password-123",
                "remember_me": False,
            },
        )
        assert signup.status_code == 201
        original_refresh_token = signup.json()["refresh_token"]

        refresh_response = await api_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": original_refresh_token},
        )
        assert refresh_response.status_code == 200
        refreshed_payload = refresh_response.json()
        replacement_refresh_token = refreshed_payload["refresh_token"]
        assert replacement_refresh_token != original_refresh_token

        reuse_old_response = await api_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": original_refresh_token},
        )
        assert reuse_old_response.status_code == 401
        assert reuse_old_response.json()["detail"] == "Invalid refresh token"

        logout_response = await api_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": replacement_refresh_token},
        )
        assert logout_response.status_code == 204

        logout_again_response = await api_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": replacement_refresh_token},
        )
        assert logout_again_response.status_code == 204
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_refresh_invalid_token_returns_401(api_client, db_session, monkeypatch):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"
    finally:
        app.dependency_overrides.clear()
