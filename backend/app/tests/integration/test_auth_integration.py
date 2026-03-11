from datetime import UTC, datetime, timedelta
import asyncio
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import jwt
import pytest
import pytest_asyncio
import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import _resolve_authenticated_user, get_current_user
from app.core.config import get_settings
from app.db.database import get_db
from app.main import app
from app.models.user import User

router = APIRouter()
settings = get_settings()


@router.get("/test-auth-integration")
async def check_auth_integration(current_user: User = Depends(get_current_user)):
    return {"id": str(current_user.id), "email": current_user.email}


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
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"auth-int-{uuid4().hex[:8]}@ufl.edu"
    existing_user = User(  # pyright: ignore[reportCallIssue]
        id=user_id,
        email=email,
        password_hash="integration-password-hash",
        role="student",
    )
    db_session.add(existing_user)
    await db_session.commit()

    token = jwt.encode(
        {
            "sub": str(user_id),
            "email": email,
            "aud": "authenticated",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        jwt_secret,
        algorithm="HS256",
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/test-auth-integration",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == {"id": str(user_id), "email": email}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_current_user_rejects_unknown_user(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"auth-int-{uuid4().hex[:8]}@ufl.edu"
    token = jwt.encode(
        {
            "sub": str(user_id),
            "email": email,
            "aud": "authenticated",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        jwt_secret,
        algorithm="HS256",
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/test-auth-integration",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_current_user_concurrent_unknown_user_requests_are_rejected(
    async_engine: AsyncEngine, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"auth-race-{uuid4().hex[:8]}@ufl.edu"
    token = jwt.encode(
        {
            "sub": str(user_id),
            "email": email,
            "aud": "authenticated",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        jwt_secret,
        algorithm="HS256",
    )

    async def authenticate_once() -> User:
        request = cast(Request, SimpleNamespace(state=SimpleNamespace()))
        async with AsyncSession(async_engine, expire_on_commit=False) as session:
            return await _resolve_authenticated_user(request, token, session)

    first_response, second_response = await asyncio.gather(
        authenticate_once(), authenticate_once(), return_exceptions=True
    )
    assert isinstance(first_response, HTTPException)
    assert isinstance(second_response, HTTPException)
    assert first_response.status_code == 401
    assert second_response.status_code == 401

    async with AsyncSession(async_engine, expire_on_commit=False) as verify_session:
        count_result = await verify_session.exec(  # pyright: ignore[reportCallIssue]
            sa.select(sa.func.count()).select_from(User).where(User.id == user_id)  # pyright: ignore[reportArgumentType]
        )
        assert count_result.scalar_one() == 0
