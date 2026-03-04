from datetime import UTC, datetime, timedelta
import asyncio
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import jwt
import pytest
import pytest_asyncio
import sqlalchemy as sa
from fastapi import APIRouter, Depends
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
async def test_get_current_user_upserts_user_in_real_db(
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
        before = await db_session.exec(sa.select(User).where(User.id == user_id))  # pyright: ignore[reportArgumentType]
        assert before.scalars().one_or_none() is None

        response = await api_client.get(
            "/test-auth-integration",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == {"id": str(user_id), "email": email}

        after = await db_session.exec(sa.select(User).where(User.id == user_id))  # pyright: ignore[reportArgumentType]
        created_user = after.scalars().one_or_none()
        assert created_user is not None
        assert created_user.email == email
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_current_user_concurrent_first_requests_are_race_safe(
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

    first_user, second_user = await asyncio.gather(
        authenticate_once(), authenticate_once()
    )
    assert first_user.id == user_id
    assert second_user.id == user_id
    assert first_user.email == email
    assert second_user.email == email

    async with AsyncSession(async_engine, expire_on_commit=False) as verify_session:
        count_result = await verify_session.exec(  # pyright: ignore[reportCallIssue]
            sa.select(sa.func.count()).select_from(User).where(User.id == user_id)  # pyright: ignore[reportArgumentType]
        )
        assert count_result.scalar_one() == 1
        stored_user_result = await verify_session.exec(  # pyright: ignore[reportCallIssue]
            sa.select(User).where(User.id == user_id)  # pyright: ignore[reportArgumentType]
        )
        stored_user = stored_user_result.scalars().one()
        assert stored_user.email == email
        await verify_session.delete(stored_user)
        await verify_session.commit()
