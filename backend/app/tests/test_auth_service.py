from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import jwt
import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
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


class DummySession:
    pass


class FakeIssueSession:
    def __init__(self):
        self.added: list[object] = []
        self.commit = AsyncMock()

    def add(self, obj: object) -> None:
        self.added.append(obj)


def _build_user(*, email: str = "auth-service@ufl.edu") -> User:
    now = datetime.now(UTC)
    return User(  # pyright: ignore[reportCallIssue]
        id=uuid4(),
        email=email,
        password_hash="placeholder",
        role="student",
        created_at=now,
        updated_at=now,
    )


def test_hash_password_and_verify_round_trip():
    service = AuthService(cast(AsyncSession, DummySession()))
    password = "example-password-123!"

    password_hash = service.hash_password(password)
    assert password_hash != password
    assert service.verify_password(password, password_hash) is True
    assert service.verify_password("wrong-password", password_hash) is False


def test_hash_refresh_token_is_stable_and_non_reversible():
    service = AuthService(cast(AsyncSession, DummySession()))
    raw_token = "raw-refresh-token"

    first_hash = service.hash_refresh_token(raw_token)
    second_hash = service.hash_refresh_token(raw_token)
    other_hash = service.hash_refresh_token("different-token")

    assert first_hash == second_hash
    assert first_hash != raw_token
    assert other_hash != first_hash


@pytest.mark.asyncio
async def test_issue_token_pair_access_token_claims_match_auth_dependency_contract(
    monkeypatch,
):
    settings = get_settings()
    monkeypatch.setattr(
        settings, "DATABASE_JWT_SECRET", "unit-test-secret-at-least-32-bytes"
    )
    db = FakeIssueSession()
    service = AuthService(cast(AsyncSession, db))
    user = _build_user(email="claims-user@ufl.edu")
    tokens = await service.issue_token_pair(user=user, remember_me=False)
    payload = jwt.decode(
        tokens.access_token,
        settings.DATABASE_JWT_SECRET,
        algorithms=["HS256"],
        audience="authenticated",
    )
    assert payload["sub"] == str(user.id)
    assert payload["email"] == "claims-user@ufl.edu"
    assert payload["aud"] == "authenticated"
    assert isinstance(payload["iat"], int)
    assert isinstance(payload["exp"], int)
    assert payload["exp"] > payload["iat"]
    assert tokens.expires_in == int(ACCESS_TOKEN_TTL.total_seconds())
    db.commit.assert_awaited_once()
    assert len(db.added) == 1


@pytest.mark.asyncio
async def test_authenticate_user_rejects_missing_user():
    service = AuthService(cast(AsyncSession, DummySession()))
    service.get_user_by_email = AsyncMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(InvalidCredentialsError, match="Invalid credentials"):
        await service.authenticate_user(email="missing@ufl.edu", password="pass")


@pytest.mark.asyncio
async def test_authenticate_user_rejects_invalid_password():
    service = AuthService(cast(AsyncSession, DummySession()))
    user = _build_user()
    user.password_hash = service.hash_password("correct-password")
    service.get_user_by_email = AsyncMock(return_value=user)  # type: ignore[method-assign]

    with pytest.raises(InvalidCredentialsError, match="Invalid credentials"):
        await service.authenticate_user(
            email="auth-service@ufl.edu", password="wrong-password"
        )


@pytest.mark.asyncio
async def test_authenticate_user_returns_user_when_credentials_match():
    service = AuthService(cast(AsyncSession, DummySession()))
    user = _build_user()
    user.password_hash = service.hash_password("correct-password")
    service.get_user_by_email = AsyncMock(return_value=user)  # type: ignore[method-assign]

    authenticated = await service.authenticate_user(
        email="auth-service@ufl.edu", password="correct-password"
    )
    assert authenticated is user


def test_refresh_ttl_policy_values():
    assert AuthService._refresh_ttl(False) == REFRESH_TOKEN_TTL_DEFAULT
    assert AuthService._refresh_ttl(True) == REFRESH_TOKEN_TTL_REMEMBER_ME


def test_derive_original_refresh_ttl_defaults_when_non_positive_delta():
    now = datetime.now(UTC)
    session = RefreshSession(  # pyright: ignore[reportCallIssue]
        id=uuid4(),
        user_id=uuid4(),
        token_hash="session-hash",
        created_at=now + timedelta(seconds=1),
        expires_at=now,
    )
    assert (
        AuthService._derive_original_refresh_ttl(session) == REFRESH_TOKEN_TTL_DEFAULT
    )


@pytest.mark.asyncio
async def test_refresh_token_pair_rejects_unknown_token():
    class SessionWithNoRefreshRows:
        async def exec(self, _statement):
            return type("Result", (), {"one_or_none": lambda self: None})()

    service = AuthService(cast(AsyncSession, SessionWithNoRefreshRows()))
    with pytest.raises(InvalidRefreshTokenError, match="Invalid refresh token"):
        await service.refresh_token_pair(refresh_token="missing-token")


@pytest.mark.asyncio
async def test_refresh_token_pair_rejects_token_for_missing_user():
    class _ResultWithOneOrNone:
        def __init__(self, row):
            self._row = row

        def one_or_none(self):
            return self._row

    class _ResultWithFirst:
        def __init__(self, row):
            self._row = row

        def first(self):
            return self._row

    class SessionWithRevokedRowMissingUser:
        def __init__(self):
            now = datetime.now(UTC)
            self.results = [
                _ResultWithOneOrNone((uuid4(), uuid4(), now, now + timedelta(days=14))),
                _ResultWithFirst(None),
            ]
            self.commit = AsyncMock()

        async def exec(self, _statement):
            return self.results.pop(0)

        def add(self, _obj):
            return None

    service = AuthService(cast(AsyncSession, SessionWithRevokedRowMissingUser()))
    with pytest.raises(InvalidRefreshTokenError, match="Invalid refresh token"):
        await service.refresh_token_pair(refresh_token="missing-user-token")


@pytest.mark.asyncio
async def test_create_user_rolls_back_on_commit_failure():
    class SessionCommitFails:
        def __init__(self):
            self.rollback = AsyncMock()
            self.commit = AsyncMock(side_effect=RuntimeError("commit failed"))
            self.refresh = AsyncMock()
            self.added: list[object] = []

        async def exec(self, _statement):
            return type("Result", (), {"first": lambda self: None})()

        def add(self, obj):
            self.added.append(obj)
            return None

    db = SessionCommitFails()
    service = AuthService(cast(AsyncSession, db))
    service.get_user_by_email = AsyncMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="commit failed"):
        await service.create_user(
            email="rollback-create@ufl.edu",
            password="valid-create-password-123",
        )
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_token_pair_rolls_back_on_commit_failure():
    class _ResultWithOneOrNone:
        def __init__(self, row):
            self._row = row

        def one_or_none(self):
            return self._row

    class _ResultWithFirst:
        def __init__(self, row):
            self._row = row

        def first(self):
            return self._row

    class SessionCommitFailsOnRefresh:
        def __init__(self):
            now = datetime.now(UTC)
            user_id = uuid4()
            self.results = [
                _ResultWithOneOrNone((uuid4(), user_id, now, now + timedelta(days=14))),
                _ResultWithFirst(_build_user(email="refresh-rollback@ufl.edu")),
            ]
            self.rollback = AsyncMock()
            self.commit = AsyncMock(side_effect=RuntimeError("commit failed"))
            self.added: list[object] = []

        async def exec(self, _statement):
            return self.results.pop(0)

        def add(self, obj):
            self.added.append(obj)
            return None

    db = SessionCommitFailsOnRefresh()
    service = AuthService(cast(AsyncSession, db))

    with pytest.raises(RuntimeError, match="commit failed"):
        await service.refresh_token_pair(refresh_token="refresh-rollback-token")
    db.rollback.assert_awaited_once()
