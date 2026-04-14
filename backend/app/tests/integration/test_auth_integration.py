import asyncio
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import pytest
import pytest_asyncio
import sqlalchemy as sa
from fastapi import APIRouter, Depends
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import _resolve_authenticated_user
from app.api.deps.auth import get_current_user
from app.db.database import get_db
from app.main import app
from app.models.user import User

router = APIRouter()


@router.get("/test-auth-integration")
async def check_auth_integration(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "auth_user_id": str(current_user.auth_user_id),
        "email": current_user.email,
        "username": current_user.username,
    }


app.include_router(router)


@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_get_current_user_returns_existing_user(
    api_client, db_session, monkeypatch
):
    auth_user_id = uuid4()
    existing_user = User(  # pyright: ignore[reportCallIssue]
        auth_user_id=auth_user_id,
        email="existing@ufl.edu",
        username="existing_user",
        role="student",
    )
    db_session.add(existing_user)
    await db_session.commit()
    await db_session.refresh(existing_user)

    monkeypatch.setattr(
        "app.api.deps.auth._decode_supabase_jwt",
        lambda _token: {
            "sub": str(auth_user_id),
            "email": "existing@ufl.edu",
            "aud": "authenticated",
            "iss": "https://issuer.example/auth/v1",
            "iat": 1,
            "exp": 9999999999,
            "user_metadata": {"username": "existing_user"},
            "email_confirmed_at": "2026-01-01T00:00:00Z",
        },
    )

    def fake_admin_get_user(self, _auth_user_id):
        return {
            "id": str(auth_user_id),
            "email_confirmed_at": "2026-01-01T00:00:00Z",
            "user_metadata": {"username": "existing_user"},
        }

    monkeypatch.setattr(
        "app.services.auth_bootstrap.SupabaseAdminClient.get_user", fake_admin_get_user
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/test-auth-integration",
            headers={"Authorization": "Bearer valid"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "id": str(existing_user.id),
            "auth_user_id": str(auth_user_id),
            "email": "existing@ufl.edu",
            "username": "existing_user",
        }
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_current_user_bootstraps_missing_user(
    api_client, db_session, monkeypatch
):
    auth_user_id = uuid4()

    monkeypatch.setattr(
        "app.api.deps.auth._decode_supabase_jwt",
        lambda _token: {
            "sub": str(auth_user_id),
            "email": "bootstrap@ufl.edu",
            "aud": "authenticated",
            "iss": "https://issuer.example/auth/v1",
            "iat": 1,
            "exp": 9999999999,
            "user_metadata": {
                "username": "bootstrap_user",
                "full_name": "Bootstrap User",
            },
            "email_confirmed_at": "2026-01-01T00:00:00Z",
        },
    )

    def fake_admin_get_user(self, _auth_user_id):
        return {
            "id": str(auth_user_id),
            "email_confirmed_at": "2026-01-01T00:00:00Z",
            "user_metadata": {
                "username": "bootstrap_user",
                "full_name": "Bootstrap User",
            },
        }

    monkeypatch.setattr(
        "app.services.auth_bootstrap.SupabaseAdminClient.get_user", fake_admin_get_user
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/test-auth-integration",
            headers={"Authorization": "Bearer valid"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["auth_user_id"] == str(auth_user_id)
        assert payload["email"] == "bootstrap@ufl.edu"
        assert payload["username"] == "bootstrap_user"

        result = await db_session.execute(
            sa.select(sa.func.count())
            .select_from(User)
            .where(User.auth_user_id == auth_user_id)  # pyright: ignore[reportArgumentType]
        )
        assert result.scalar_one() == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_current_user_allows_non_ufl_email(
    api_client, db_session, monkeypatch
):
    auth_user_id = uuid4()

    monkeypatch.setattr(
        "app.api.deps.auth._decode_supabase_jwt",
        lambda _token: {
            "sub": str(auth_user_id),
            "email": "person@example.com",
            "aud": "authenticated",
            "iss": "https://issuer.example/auth/v1",
            "iat": 1,
            "exp": 9999999999,
            "user_metadata": {"username": "outside_user"},
            "email_confirmed_at": "2026-01-01T00:00:00Z",
        },
    )

    monkeypatch.setattr(
        "app.services.auth_bootstrap.SupabaseAdminClient.get_user",
        lambda self, _auth_user_id: {
            "id": str(auth_user_id),
            "email_confirmed_at": "2026-01-01T00:00:00Z",
            "user_metadata": {"username": "outside_user"},
        },
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/test-auth-integration",
            headers={"Authorization": "Bearer valid"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["auth_user_id"] == str(auth_user_id)
        assert payload["email"] == "person@example.com"
        assert payload["username"] == "outside_user"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_current_user_rejects_unconfirmed_email(
    api_client, db_session, monkeypatch
):
    auth_user_id = uuid4()

    monkeypatch.setattr(
        "app.api.deps.auth._decode_supabase_jwt",
        lambda _token: {
            "sub": str(auth_user_id),
            "email": "pending@ufl.edu",
            "aud": "authenticated",
            "iss": "https://issuer.example/auth/v1",
            "iat": 1,
            "exp": 9999999999,
            "user_metadata": {"username": "pending_user"},
            "email_confirmed_at": None,
        },
    )

    monkeypatch.setattr(
        "app.services.auth_bootstrap.SupabaseAdminClient.get_user",
        lambda self, _auth_user_id: {
            "id": str(auth_user_id),
            "email_confirmed_at": None,
            "user_metadata": {"username": "pending_user"},
        },
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/test-auth-integration",
            headers={"Authorization": "Bearer valid"},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Email confirmation required"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_current_user_concurrent_bootstrap_is_idempotent(
    async_engine, monkeypatch
):
    auth_user_id = uuid4()

    payload = {
        "sub": str(auth_user_id),
        "email": "race@ufl.edu",
        "aud": "authenticated",
        "iss": "https://issuer.example/auth/v1",
        "iat": 1,
        "exp": 9999999999,
        "user_metadata": {"username": "race_user"},
        "email_confirmed_at": "2026-01-01T00:00:00Z",
    }

    monkeypatch.setattr(
        "app.api.deps.auth._decode_supabase_jwt",
        lambda _token: payload,
    )

    monkeypatch.setattr(
        "app.services.auth_bootstrap.SupabaseAdminClient.get_user",
        lambda self, _auth_user_id: {
            "id": str(auth_user_id),
            "email_confirmed_at": "2026-01-01T00:00:00Z",
            "user_metadata": {"username": "race_user"},
        },
    )

    async def authenticate_once():
        request = cast(Request, SimpleNamespace(state=SimpleNamespace()))
        async with AsyncSession(async_engine, expire_on_commit=False) as session:
            return await _resolve_authenticated_user(request, "race-token", session)

    first, second = await asyncio.gather(authenticate_once(), authenticate_once())
    assert first.auth_user_id == auth_user_id
    assert second.auth_user_id == auth_user_id

    async with AsyncSession(async_engine, expire_on_commit=False) as verify_session:
        result = await verify_session.execute(
            sa.select(sa.func.count())
            .select_from(User)
            .where(User.auth_user_id == auth_user_id)  # pyright: ignore[reportArgumentType]
        )
        assert result.scalar_one() == 1
