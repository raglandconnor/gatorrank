from collections.abc import Iterator
from types import SimpleNamespace
from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.api.deps.auth import (
    get_current_user,
    get_current_user_id_optional,
    get_current_user_optional,
)
from app.main import app
from app.models.user import User
from app.services.auth_bootstrap import EmailPolicyError, UsernameConflictError

router = APIRouter()


@router.get("/test-auth")
async def check_auth(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email}


@router.get("/test-auth-optional")
async def check_auth_optional(
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
):
    current_user_id = getattr(request.state, "current_user_id", None)
    current_auth_user_id = getattr(request.state, "current_auth_user_id", None)
    if current_user is None:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "email": current_user.email,
        "state_user_id": str(current_user_id),
        "state_auth_user_id": str(current_auth_user_id),
    }


app.include_router(router)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as tc:
        yield tc


def _user(*, app_user_id: UUID | None = None, auth_user_id: UUID | None = None) -> User:
    return User(  # pyright: ignore[reportCallIssue]
        id=app_user_id or uuid4(),
        auth_user_id=auth_user_id or uuid4(),
        email="student@ufl.edu",
        username="student_user",
        role="student",
    )


def test_unauthenticated_route(client):
    response = client.get("/test-auth")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_optional_auth_no_header_returns_anonymous(client):
    response = client.get("/test-auth-optional")
    assert response.status_code == 200
    assert response.json() == {"authenticated": False}


def test_optional_auth_valid_token_maps_bootstrapped_user(client, monkeypatch):
    app_user_id = uuid4()
    auth_user_id = uuid4()
    resolved_user = _user(app_user_id=app_user_id, auth_user_id=auth_user_id)

    monkeypatch.setattr(
        "app.api.deps.auth._decode_supabase_jwt",
        lambda _token: {
            "sub": str(auth_user_id),
            "email": "student@ufl.edu",
            "aud": "authenticated",
            "iss": "https://issuer.example/auth/v1",
            "iat": 1,
            "exp": 9999999999,
            "user_metadata": {"username": "student_user"},
            "email_confirmed_at": "2026-01-01T00:00:00Z",
        },
    )

    async def fake_get_or_create_user(self, identity):
        assert identity.auth_user_id == auth_user_id
        assert identity.email == "student@ufl.edu"
        assert identity.username == "student_user"
        assert identity.email_confirmed is True
        return resolved_user

    monkeypatch.setattr(
        "app.services.auth_bootstrap.AuthBootstrapService.get_or_create_user",
        fake_get_or_create_user,
    )

    response = client.get(
        "/test-auth-optional",
        headers={"Authorization": "Bearer valid.supabase.jwt"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["authenticated"] is True
    assert payload["email"] == "student@ufl.edu"
    assert payload["state_user_id"] == str(app_user_id)
    assert payload["state_auth_user_id"] == str(auth_user_id)


def test_optional_auth_invalid_token_still_401(client, monkeypatch):
    def fail_decode(_token: str):
        raise ValueError("bad token")

    monkeypatch.setattr("app.api.deps.auth._decode_supabase_jwt", fail_decode)

    response = client.get(
        "/test-auth-optional",
        headers={"Authorization": "Bearer invalid"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_optional_auth_expired_token_still_401(client, monkeypatch):
    import jwt

    def fail_decode(_token: str):
        raise jwt.ExpiredSignatureError("expired")

    monkeypatch.setattr("app.api.deps.auth._decode_supabase_jwt", fail_decode)

    response = client.get(
        "/test-auth-optional",
        headers={"Authorization": "Bearer expired"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"


def test_optional_auth_email_policy_failure_returns_403(client, monkeypatch):
    auth_user_id = uuid4()

    monkeypatch.setattr(
        "app.api.deps.auth._decode_supabase_jwt",
        lambda _token: {
            "sub": str(auth_user_id),
            "email": "student@ufl.edu",
            "aud": "authenticated",
            "iss": "https://issuer.example/auth/v1",
            "iat": 1,
            "exp": 9999999999,
        },
    )

    async def fail_policy(self, _identity):
        raise EmailPolicyError("Email confirmation required")

    monkeypatch.setattr(
        "app.services.auth_bootstrap.AuthBootstrapService.get_or_create_user",
        fail_policy,
    )

    response = client.get(
        "/test-auth-optional",
        headers={"Authorization": "Bearer denied"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Email confirmation required"


def test_optional_auth_username_conflict_returns_409(client, monkeypatch):
    auth_user_id = uuid4()

    monkeypatch.setattr(
        "app.api.deps.auth._decode_supabase_jwt",
        lambda _token: {
            "sub": str(auth_user_id),
            "email": "student@ufl.edu",
            "aud": "authenticated",
            "iss": "https://issuer.example/auth/v1",
            "iat": 1,
            "exp": 9999999999,
        },
    )

    async def fail_conflict(self, _identity):
        raise UsernameConflictError("username_taken")

    monkeypatch.setattr(
        "app.services.auth_bootstrap.AuthBootstrapService.get_or_create_user",
        fail_conflict,
    )

    response = client.get(
        "/test-auth-optional",
        headers={"Authorization": "Bearer conflict"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "username_taken"


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
