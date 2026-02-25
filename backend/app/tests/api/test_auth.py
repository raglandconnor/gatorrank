from datetime import UTC, datetime, timedelta
from typing import cast
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from fastapi import APIRouter, Depends
from starlette.requests import Request

from app.api.deps.auth import (
    get_current_user,
    get_current_user_id_optional,
    get_current_user_optional,
)
from app.core.config import get_settings
from app.db.database import get_db
from app.main import app
from app.models.user import User

# Temporary test route
router = APIRouter()
settings = get_settings()


@router.get("/test-auth")
async def check_auth(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email}


@router.get("/test-auth-optional")
async def check_auth_optional(
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
):
    current_user_id = cast(str | None, getattr(request.state, "current_user_id", None))
    if current_user is None:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "email": current_user.email,
        "state_user_id": str(current_user_id),
    }


app.include_router(router)


def test_authenticated_route(authenticated_client, mock_user):
    response = authenticated_client.get("/test-auth")
    assert response.status_code == 200
    assert response.json() == {"email": mock_user.email}


def test_unauthenticated_route(client):
    response = client.get("/test-auth")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_optional_auth_no_header_returns_anonymous(client):
    response = client.get("/test-auth-optional")
    assert response.status_code == 200
    assert response.json() == {"authenticated": False}


def test_optional_auth_valid_token_returns_user(jwt_test_client):
    token = _make_token("test-jwt-secret-at-least-32-bytes!!")
    response = jwt_test_client.get(
        "/test-auth-optional",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["authenticated"] is True
    assert payload["email"] == "jwt-test@ufl.edu"
    assert payload["state_user_id"] is not None


def test_optional_auth_invalid_token_still_401(jwt_test_client):
    token = _make_token("wrong-secret-at-least-32-bytes!!!!")
    response = jwt_test_client.get(
        "/test-auth-optional",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_optional_auth_expired_token_still_401(jwt_test_client):
    token = _make_token(
        "test-jwt-secret-at-least-32-bytes!!",
        exp=datetime.now(UTC) - timedelta(minutes=1),
    )
    response = jwt_test_client.get(
        "/test-auth-optional",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"


def test_optional_auth_invalid_header_scheme_401(jwt_test_client):
    response = jwt_test_client.get(
        "/test-auth-optional",
        headers={"Authorization": "Basic abc123"},
    )
    assert response.status_code == 401


def test_optional_auth_empty_bearer_token_401(jwt_test_client):
    response = jwt_test_client.get(
        "/test-auth-optional",
        headers={"Authorization": "Bearer "},
    )
    assert response.status_code == 401


def test_optional_auth_missing_sub_claim_401(jwt_test_client):
    token = _make_token("test-jwt-secret-at-least-32-bytes!!")
    payload = jwt.decode(
        token,
        "test-jwt-secret-at-least-32-bytes!!",
        algorithms=["HS256"],
        options={"verify_exp": False, "verify_aud": False},
    )
    payload.pop("sub", None)
    token_without_sub = jwt.encode(
        payload,
        "test-jwt-secret-at-least-32-bytes!!",
        algorithm="HS256",
    )
    response = jwt_test_client.get(
        "/test-auth-optional",
        headers={"Authorization": f"Bearer {token_without_sub}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token payload"


def test_optional_auth_missing_email_claim_401(jwt_test_client):
    token = _make_token("test-jwt-secret-at-least-32-bytes!!")
    payload = jwt.decode(
        token,
        "test-jwt-secret-at-least-32-bytes!!",
        algorithms=["HS256"],
        options={"verify_exp": False, "verify_aud": False},
    )
    payload.pop("email", None)
    token_without_email = jwt.encode(
        payload,
        "test-jwt-secret-at-least-32-bytes!!",
        algorithm="HS256",
    )
    response = jwt_test_client.get(
        "/test-auth-optional",
        headers={"Authorization": f"Bearer {token_without_email}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token payload"


def test_optional_auth_valid_token_upserts_user(jwt_test_context):
    user_id = uuid4()
    session = jwt_test_context["configure_db"](existing_user=None)
    token = _make_token(
        "test-jwt-secret-at-least-32-bytes!!",
        sub=str(user_id),
        email="optional-user@ufl.edu",
    )
    response = jwt_test_context["client"].get(
        "/test-auth-optional",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["authenticated"] is True
    assert payload["email"] == "optional-user@ufl.edu"
    assert payload["state_user_id"] == str(user_id)
    assert session.add_calls == 1
    assert session.commit_calls == 1
    assert session.refresh_calls == 1


class _MockResult:
    def __init__(self, user: User | None):
        self._user = user

    def one_or_none(self):
        return self._user

    def scalar_one_or_none(self):
        return self._user


class _MockSession:
    def __init__(
        self,
        existing_user: User | None = None,
        execute_error: Exception | None = None,
        commit_error: Exception | None = None,
        refresh_error: Exception | None = None,
    ):
        self._existing_user = existing_user
        self._execute_error = execute_error
        self._commit_error = commit_error
        self._refresh_error = refresh_error
        self.add_calls = 0
        self.commit_calls = 0
        self.refresh_calls = 0
        self.added_user: User | None = None
        self.refreshed_user: User | None = None

    async def execute(self, _query):
        if self._execute_error is not None:
            raise self._execute_error
        return _MockResult(self._existing_user)

    async def exec(self, _query):
        return await self.execute(_query)

    def add(self, obj):
        self.add_calls += 1
        self.added_user = obj
        return None

    async def commit(self):
        self.commit_calls += 1
        if self._commit_error is not None:
            raise self._commit_error
        return None

    async def refresh(self, obj):
        self.refresh_calls += 1
        self.refreshed_user = obj
        if self._refresh_error is not None:
            raise self._refresh_error
        return None


@pytest.fixture
def jwt_test_client(client, monkeypatch):
    monkeypatch.setattr(
        settings,
        "DATABASE_JWT_SECRET",
        "test-jwt-secret-at-least-32-bytes!!",
    )

    async def override_get_db():
        yield _MockSession()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def jwt_test_context(client, monkeypatch):
    monkeypatch.setattr(
        settings,
        "DATABASE_JWT_SECRET",
        "test-jwt-secret-at-least-32-bytes!!",
    )

    state: dict[str, _MockSession] = {}

    def configure_db(
        existing_user: User | None = None,
        execute_error: Exception | None = None,
        commit_error: Exception | None = None,
        refresh_error: Exception | None = None,
    ) -> _MockSession:
        session = _MockSession(
            existing_user=existing_user,
            execute_error=execute_error,
            commit_error=commit_error,
            refresh_error=refresh_error,
        )
        state["session"] = session
        return session

    configure_db()

    async def override_get_db():
        yield state["session"]

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield {"client": client, "configure_db": configure_db, "state": state}
    finally:
        app.dependency_overrides.clear()


def _make_token(secret: str, **overrides: object) -> str:
    payload = {
        "sub": str(uuid4()),
        "email": "jwt-test@ufl.edu",
        "aud": "authenticated",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    payload.update(overrides)
    return jwt.encode(payload, secret, algorithm="HS256")


def test_real_jwt_valid_token(jwt_test_client):
    token = _make_token("test-jwt-secret-at-least-32-bytes!!")
    response = jwt_test_client.get(
        "/test-auth",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"email": "jwt-test@ufl.edu"}


def test_real_jwt_invalid_signature(jwt_test_client):
    token = _make_token("wrong-secret-at-least-32-bytes!!!!")
    response = jwt_test_client.get(
        "/test-auth",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_real_jwt_expired_token(jwt_test_client):
    token = _make_token(
        "test-jwt-secret-at-least-32-bytes!!",
        exp=datetime.now(UTC) - timedelta(minutes=1),
    )
    response = jwt_test_client.get(
        "/test-auth",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"


def test_real_jwt_malformed_sub_claim(jwt_test_client):
    token = _make_token(
        "test-jwt-secret-at-least-32-bytes!!",
        sub="not-a-uuid",
    )
    response = jwt_test_client.get(
        "/test-auth",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_real_jwt_wrong_audience(jwt_test_client):
    token = _make_token(
        "test-jwt-secret-at-least-32-bytes!!",
        aud="not-authenticated",
    )
    response = jwt_test_client.get(
        "/test-auth",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_real_jwt_missing_email_claim(jwt_test_client):
    token = _make_token(
        "test-jwt-secret-at-least-32-bytes!!",
        email=None,
    )
    response = jwt_test_client.get(
        "/test-auth",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token payload"


def test_real_jwt_missing_sub_claim(jwt_test_client):
    token = _make_token("test-jwt-secret-at-least-32-bytes!!")
    payload = jwt.decode(
        token,
        "test-jwt-secret-at-least-32-bytes!!",
        algorithms=["HS256"],
        options={"verify_exp": False, "verify_aud": False},
    )
    payload.pop("sub", None)
    token_without_sub = jwt.encode(
        payload,
        "test-jwt-secret-at-least-32-bytes!!",
        algorithm="HS256",
    )
    response = jwt_test_client.get(
        "/test-auth",
        headers={"Authorization": f"Bearer {token_without_sub}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token payload"


def test_real_jwt_missing_email_claim_omitted(jwt_test_client):
    token = _make_token("test-jwt-secret-at-least-32-bytes!!")
    payload = jwt.decode(
        token,
        "test-jwt-secret-at-least-32-bytes!!",
        algorithms=["HS256"],
        options={"verify_exp": False, "verify_aud": False},
    )
    payload.pop("email", None)
    token_without_email = jwt.encode(
        payload,
        "test-jwt-secret-at-least-32-bytes!!",
        algorithm="HS256",
    )
    response = jwt_test_client.get(
        "/test-auth",
        headers={"Authorization": f"Bearer {token_without_email}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token payload"


def test_auth_invalid_header_scheme(jwt_test_client):
    response = jwt_test_client.get(
        "/test-auth",
        headers={"Authorization": "Basic abc123"},
    )
    assert response.status_code == 401


def test_auth_empty_bearer_token(jwt_test_client):
    response = jwt_test_client.get(
        "/test-auth",
        headers={"Authorization": "Bearer "},
    )
    assert response.status_code == 401


def test_auth_garbage_bearer_token(jwt_test_client):
    response = jwt_test_client.get(
        "/test-auth",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_real_jwt_missing_aud_claim(jwt_test_client):
    token = _make_token("test-jwt-secret-at-least-32-bytes!!")
    payload = jwt.decode(
        token,
        "test-jwt-secret-at-least-32-bytes!!",
        algorithms=["HS256"],
        options={"verify_exp": False, "verify_aud": False},
    )
    payload.pop("aud", None)
    token_without_aud = jwt.encode(
        payload,
        "test-jwt-secret-at-least-32-bytes!!",
        algorithm="HS256",
    )
    response = jwt_test_client.get(
        "/test-auth",
        headers={"Authorization": f"Bearer {token_without_aud}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_real_jwt_missing_exp_claim_currently_allowed(jwt_test_client):
    token = _make_token("test-jwt-secret-at-least-32-bytes!!")
    payload = jwt.decode(
        token,
        "test-jwt-secret-at-least-32-bytes!!",
        algorithms=["HS256"],
        options={"verify_exp": False, "verify_aud": False},
    )
    payload.pop("exp", None)
    token_without_exp = jwt.encode(
        payload,
        "test-jwt-secret-at-least-32-bytes!!",
        algorithm="HS256",
    )
    response = jwt_test_client.get(
        "/test-auth",
        headers={"Authorization": f"Bearer {token_without_exp}"},
    )
    assert response.status_code == 200
    assert response.json() == {"email": "jwt-test@ufl.edu"}


def test_real_jwt_existing_user_does_not_create(jwt_test_context):
    user_id = uuid4()
    existing_user = User(  # pyright: ignore[reportCallIssue]
        id=user_id, email="existing@ufl.edu", role="student"
    )
    session = jwt_test_context["configure_db"](existing_user=existing_user)
    token = _make_token(
        "test-jwt-secret-at-least-32-bytes!!",
        sub=str(user_id),
        email=existing_user.email,
    )

    response = jwt_test_context["client"].get(
        "/test-auth",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"email": existing_user.email}
    assert session.add_calls == 0
    assert session.commit_calls == 0
    assert session.refresh_calls == 0


def test_real_jwt_new_user_creates_and_commits(jwt_test_context):
    user_id = uuid4()
    session = jwt_test_context["configure_db"](existing_user=None)
    token = _make_token(
        "test-jwt-secret-at-least-32-bytes!!",
        sub=str(user_id),
        email="new-user@ufl.edu",
    )

    response = jwt_test_context["client"].get(
        "/test-auth",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"email": "new-user@ufl.edu"}
    assert session.add_calls == 1
    assert session.commit_calls == 1
    assert session.refresh_calls == 1
    assert session.added_user is not None
    assert session.added_user.id == user_id
    assert session.added_user.email == "new-user@ufl.edu"
    assert session.refreshed_user is session.added_user


def test_real_jwt_db_execute_failure_bubbles(jwt_test_context):
    jwt_test_context["configure_db"](execute_error=RuntimeError("db execute failed"))
    token = _make_token("test-jwt-secret-at-least-32-bytes!!")

    with pytest.raises(RuntimeError, match="db execute failed"):
        jwt_test_context["client"].get(
            "/test-auth",
            headers={"Authorization": f"Bearer {token}"},
        )


def test_real_jwt_db_commit_failure_bubbles(jwt_test_context):
    session = jwt_test_context["configure_db"](
        commit_error=RuntimeError("db commit failed")
    )
    token = _make_token("test-jwt-secret-at-least-32-bytes!!")

    with pytest.raises(RuntimeError, match="db commit failed"):
        jwt_test_context["client"].get(
            "/test-auth",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert session.add_calls == 1
    assert session.commit_calls == 1
    assert session.refresh_calls == 0


def test_real_jwt_db_refresh_failure_bubbles(jwt_test_context):
    session = jwt_test_context["configure_db"](
        refresh_error=RuntimeError("db refresh failed")
    )
    token = _make_token("test-jwt-secret-at-least-32-bytes!!")

    with pytest.raises(RuntimeError, match="db refresh failed"):
        jwt_test_context["client"].get(
            "/test-auth",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert session.add_calls == 1
    assert session.commit_calls == 1
    assert session.refresh_calls == 1


def test_get_current_user_id_optional_with_uuid_value():
    user_id = uuid4()
    request = cast(
        Request, SimpleNamespace(state=SimpleNamespace(current_user_id=user_id))
    )
    assert get_current_user_id_optional(request) == user_id


def test_get_current_user_id_optional_with_uuid_string():
    user_id = uuid4()
    request = cast(
        Request, SimpleNamespace(state=SimpleNamespace(current_user_id=str(user_id)))
    )
    assert get_current_user_id_optional(request) == user_id


def test_get_current_user_id_optional_with_invalid_string_returns_none():
    request = cast(
        Request, SimpleNamespace(state=SimpleNamespace(current_user_id="not-a-uuid"))
    )
    assert get_current_user_id_optional(request) is None


def test_get_current_user_id_optional_with_missing_value_returns_none():
    request = cast(Request, SimpleNamespace(state=SimpleNamespace()))
    assert get_current_user_id_optional(request) is None
