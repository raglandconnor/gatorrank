from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
import sqlalchemy as sa
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.db.database import get_db
from app.main import app
from app.models.auth import RefreshSession
from app.models.user import User
from app.services.auth import (
    ACCESS_TOKEN_TTL,
    AuthService,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    REFRESH_TOKEN_TTL_DEFAULT,
    REFRESH_TOKEN_TTL_REMEMBER_ME,
)


@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def _seed_user_with_password(
    db_session,
    *,
    email: str,
    password: str,
) -> tuple[User, AuthService]:
    service = AuthService(db_session)
    user = User(  # pyright: ignore[reportCallIssue]
        id=uuid4(),
        email=email,
        password_hash=service.hash_password(password),
        role="student",
    )
    db_session.add(user)
    await db_session.commit()
    return user, service


@pytest.mark.asyncio
async def test_issue_token_pair_persists_hashed_refresh_session(
    db_session, monkeypatch
):
    settings = get_settings()
    monkeypatch.setattr(
        settings, "DATABASE_JWT_SECRET", "auth-service-int-secret-at-least-32b"
    )
    user, service = await _seed_user_with_password(
        db_session,
        email=f"issue-{uuid4().hex[:8]}@ufl.edu",
        password="correct-password",
    )

    tokens = await service.issue_token_pair(user=user, remember_me=False)

    assert tokens.token_type == "bearer"
    assert tokens.expires_in == int(ACCESS_TOKEN_TTL.total_seconds())
    assert tokens.refresh_token_expires_in == int(
        REFRESH_TOKEN_TTL_DEFAULT.total_seconds()
    )

    refresh_hash = service.hash_refresh_token(tokens.refresh_token)
    result = await db_session.exec(
        sa.select(RefreshSession).where(RefreshSession.user_id == user.id)  # pyright: ignore[reportArgumentType]
    )
    sessions = list(result.scalars().all())
    assert len(sessions) == 1
    assert sessions[0].token_hash == refresh_hash
    assert sessions[0].token_hash != tokens.refresh_token
    assert sessions[0].revoked_at is None

    decoded = jwt.decode(
        tokens.access_token,
        settings.DATABASE_JWT_SECRET,
        algorithms=["HS256"],
        audience="authenticated",
    )
    assert decoded["sub"] == str(user.id)
    assert decoded["email"] == user.email


@pytest.mark.asyncio
async def test_authenticate_user_checks_password(db_session):
    user, service = await _seed_user_with_password(
        db_session,
        email=f"authn-{uuid4().hex[:8]}@ufl.edu",
        password="correct-password",
    )

    authenticated = await service.authenticate_user(
        email=user.email, password="correct-password"
    )
    assert authenticated.id == user.id

    with pytest.raises(InvalidCredentialsError, match="Invalid credentials"):
        await service.authenticate_user(email=user.email, password="wrong-password")


@pytest.mark.asyncio
async def test_refresh_rotation_revokes_old_token_and_issues_new_token(
    db_session, monkeypatch
):
    settings = get_settings()
    monkeypatch.setattr(
        settings, "DATABASE_JWT_SECRET", "auth-service-int-secret-at-least-32b"
    )
    user, service = await _seed_user_with_password(
        db_session,
        email=f"rotate-{uuid4().hex[:8]}@ufl.edu",
        password="correct-password",
    )

    initial_tokens = await service.issue_token_pair(user=user, remember_me=True)
    rotated_tokens = await service.refresh_token_pair(
        refresh_token=initial_tokens.refresh_token
    )

    assert rotated_tokens.refresh_token != initial_tokens.refresh_token
    assert rotated_tokens.refresh_token_expires_in == int(
        REFRESH_TOKEN_TTL_REMEMBER_ME.total_seconds()
    )
    assert rotated_tokens.expires_in == int(ACCESS_TOKEN_TTL.total_seconds())

    sessions_result = await db_session.exec(
        sa.select(RefreshSession)
        .where(RefreshSession.user_id == user.id)  # pyright: ignore[reportArgumentType]
        .order_by(getattr(RefreshSession, "__table__").c.created_at.asc())
    )
    sessions = list(sessions_result.scalars().all())
    assert len(sessions) == 2
    assert sessions[0].revoked_at is not None
    assert sessions[1].revoked_at is None
    assert sessions[1].token_hash == service.hash_refresh_token(
        rotated_tokens.refresh_token
    )

    with pytest.raises(InvalidRefreshTokenError, match="Invalid refresh token"):
        await service.refresh_token_pair(refresh_token=initial_tokens.refresh_token)


@pytest.mark.asyncio
async def test_refresh_rotation_preserves_default_ttl_for_non_remember_me(db_session):
    user, service = await _seed_user_with_password(
        db_session,
        email=f"default-ttl-{uuid4().hex[:8]}@ufl.edu",
        password="correct-password",
    )

    initial_tokens = await service.issue_token_pair(user=user, remember_me=False)
    rotated_tokens = await service.refresh_token_pair(
        refresh_token=initial_tokens.refresh_token
    )

    assert rotated_tokens.refresh_token_expires_in == int(
        REFRESH_TOKEN_TTL_DEFAULT.total_seconds()
    )


@pytest.mark.asyncio
async def test_refresh_rejects_expired_session_token(db_session):
    user, service = await _seed_user_with_password(
        db_session,
        email=f"expired-{uuid4().hex[:8]}@ufl.edu",
        password="correct-password",
    )
    raw_refresh_token = "expired-raw-token"
    expired_session = RefreshSession(  # pyright: ignore[reportCallIssue]
        user_id=user.id,
        token_hash=service.hash_refresh_token(raw_refresh_token),
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
        revoked_at=None,
    )
    db_session.add(expired_session)
    await db_session.commit()

    with pytest.raises(InvalidRefreshTokenError, match="Invalid refresh token"):
        await service.refresh_token_pair(refresh_token=raw_refresh_token)


@pytest.mark.asyncio
async def test_issued_access_token_is_accepted_by_auth_dependency(
    api_client, db_session, monkeypatch
):
    settings = get_settings()
    monkeypatch.setattr(
        settings, "DATABASE_JWT_SECRET", "auth-service-int-secret-at-least-32b"
    )
    user, service = await _seed_user_with_password(
        db_session,
        email=f"accepted-{uuid4().hex[:8]}@ufl.edu",
        password="correct-password",
    )
    tokens = await service.issue_token_pair(user=user, remember_me=False)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {tokens.access_token}"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["id"] == str(user.id)
        assert payload["email"] == user.email
    finally:
        app.dependency_overrides.clear()
