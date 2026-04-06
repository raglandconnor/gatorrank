from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_user
from app.db.database import get_db
from app.main import app
from app.models.user import User
from app.services.auth import (
    DuplicateEmailError,
    DuplicateUsernameError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    TokenPair,
)

client = TestClient(app)


async def _override_get_db():
    class MockSession:
        pass

    yield MockSession()


def _build_user(
    email: str = "api-auth@ufl.edu", username: str = "api_auth_user"
) -> User:
    now = datetime.now(UTC)
    return User(  # pyright: ignore[reportCallIssue]
        id=uuid4(),
        email=email,
        username=username,
        password_hash="test-password-hash",
        role="student",
        full_name="Auth User",
        created_at=now,
        updated_at=now,
    )


def _build_token_pair() -> TokenPair:
    return TokenPair(
        access_token="access-token",
        token_type="bearer",
        expires_in=1800,
        refresh_token="refresh-token",
        refresh_token_expires_in=1209600,
    )


def test_signup_returns_201_and_token_payload():
    user = _build_user(email="signup@ufl.edu", username="signup_user")
    token_pair = _build_token_pair()
    app.dependency_overrides[get_db] = _override_get_db
    try:
        with (
            patch(
                "app.api.v1.auth.AuthService.create_user",
                new=AsyncMock(return_value=user),
            ),
            patch(
                "app.api.v1.auth.AuthService.issue_token_pair",
                new=AsyncMock(return_value=token_pair),
            ),
        ):
            response = client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "signup@ufl.edu",
                    "username": "signup_user",
                    "password": "long-password-123",
                    "remember_me": False,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["access_token"] == token_pair.access_token
    assert payload["refresh_token"] == token_pair.refresh_token
    assert payload["user"]["email"] == "signup@ufl.edu"
    assert payload["user"]["username"] == "signup_user"


def test_signup_duplicate_email_returns_409():
    app.dependency_overrides[get_db] = _override_get_db
    try:
        with patch(
            "app.api.v1.auth.AuthService.create_user",
            new=AsyncMock(side_effect=DuplicateEmailError("Email already registered")),
        ):
            response = client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "dup@ufl.edu",
                    "username": "dup_user",
                    "password": "long-password-123",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_signup_duplicate_username_returns_409():
    app.dependency_overrides[get_db] = _override_get_db
    try:
        with patch(
            "app.api.v1.auth.AuthService.create_user",
            new=AsyncMock(side_effect=DuplicateUsernameError("Username already taken")),
        ):
            response = client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "dup2@ufl.edu",
                    "username": "dup_user",
                    "password": "long-password-123",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == "Username already taken"


def test_login_invalid_credentials_returns_401():
    app.dependency_overrides[get_db] = _override_get_db
    try:
        with patch(
            "app.api.v1.auth.AuthService.authenticate_user",
            new=AsyncMock(side_effect=InvalidCredentialsError("Invalid credentials")),
        ):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "login@ufl.edu",
                    "password": "wrong-password",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_auth_me_requires_authentication():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_auth_me_returns_current_user():
    user = _build_user(email="me@ufl.edu", username="me_user")
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        response = client.get("/api/v1/auth/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(user.id)
    assert payload["email"] == "me@ufl.edu"
    assert payload["username"] == "me_user"


def test_refresh_invalid_token_returns_401():
    app.dependency_overrides[get_db] = _override_get_db
    try:
        with patch(
            "app.api.v1.auth.AuthService.refresh_token_pair",
            new=AsyncMock(
                side_effect=InvalidRefreshTokenError("Invalid refresh token")
            ),
        ):
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"


def test_logout_is_idempotent_and_returns_204():
    app.dependency_overrides[get_db] = _override_get_db
    try:
        with patch(
            "app.api.v1.auth.AuthService.revoke_refresh_session",
            new=AsyncMock(return_value=False),
        ):
            response = client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": "missing-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""


def test_refresh_success_returns_token_payload():
    user = _build_user(email="refresh@ufl.edu", username="refresh_user")
    token_pair = _build_token_pair()
    app.dependency_overrides[get_db] = _override_get_db
    try:
        with patch(
            "app.api.v1.auth.AuthService.refresh_token_pair",
            new=AsyncMock(return_value=(token_pair, user)),
        ):
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "valid-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] == token_pair.access_token
    assert payload["user"]["email"] == "refresh@ufl.edu"
    assert payload["user"]["username"] == "refresh_user"


def test_signup_password_policy_validation_returns_422():
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "policy@ufl.edu",
            "username": "policy_user",
            "password": "short",
            "remember_me": False,
        },
    )
    assert response.status_code == 422


def test_auth_openapi_metadata_and_response_codes_align_with_routes():
    openapi = app.openapi()
    paths = openapi["paths"]

    signup = paths["/api/v1/auth/signup"]["post"]
    assert signup["summary"] == "Sign up with email and password"
    assert signup["description"]
    assert {"201", "409", "422"}.issubset(signup["responses"].keys())

    login = paths["/api/v1/auth/login"]["post"]
    assert login["summary"] == "Log in with email and password"
    assert login["description"]
    assert {"200", "401", "422"}.issubset(login["responses"].keys())

    auth_me = paths["/api/v1/auth/me"]["get"]
    assert auth_me["summary"] == "Get authenticated user profile"
    assert auth_me["description"]
    assert {"200", "401"}.issubset(auth_me["responses"].keys())

    refresh = paths["/api/v1/auth/refresh"]["post"]
    assert refresh["summary"] == "Rotate refresh token"
    assert refresh["description"]
    assert {"200", "401", "422"}.issubset(refresh["responses"].keys())

    logout = paths["/api/v1/auth/logout"]["post"]
    assert logout["summary"] == "Log out refresh session"
    assert logout["description"]
    assert "204" in logout["responses"]


def test_auth_openapi_response_models_align_with_contract():
    openapi = app.openapi()
    paths = openapi["paths"]

    signup_201_schema = paths["/api/v1/auth/signup"]["post"]["responses"]["201"][
        "content"
    ]["application/json"]["schema"]
    assert signup_201_schema["$ref"].endswith("/AuthTokenResponse")

    login_200_schema = paths["/api/v1/auth/login"]["post"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert login_200_schema["$ref"].endswith("/AuthTokenResponse")

    refresh_200_schema = paths["/api/v1/auth/refresh"]["post"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert refresh_200_schema["$ref"].endswith("/AuthTokenResponse")

    auth_me_200_schema = paths["/api/v1/auth/me"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert auth_me_200_schema["$ref"].endswith("/AuthMeResponse")
