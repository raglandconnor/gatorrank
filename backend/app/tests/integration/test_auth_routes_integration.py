import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

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
    username = f"signup_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
                "password": "valid-signup-password-123",
                "full_name": "Signup User",
                "remember_me": False,
            },
        )
        assert response.status_code == 201
        payload = response.json()
        assert payload["token_type"] == "bearer"
        assert payload["user"]["email"] == email
        assert payload["user"]["username"] == username
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
    username = f"login_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        signup = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
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
        assert payload["user"]["username"] == username
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
@pytest.mark.parametrize(
    ("password", "expected_status"),
    [
        ("a" * 11, 422),
        ("a" * 12, 201),
        ("a" * 128, 201),
        ("a" * 129, 422),
    ],
)
async def test_signup_password_length_boundaries(
    api_client, db_session, monkeypatch, password: str, expected_status: int
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"pwd-boundary-{uuid4().hex[:8]}@ufl.edu"
    username = f"pwd_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
                "password": password,
                "remember_me": False,
            },
        )
        assert response.status_code == expected_status
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_signup_whitespace_only_password_rejected(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"pwd-whitespace-{uuid4().hex[:8]}@ufl.edu"
    username = f"pwdws_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
                "password": "            ",
                "remember_me": False,
            },
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_signup_email_is_normalized_before_persist(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    raw_email = f"  MiXeD-Case-{uuid4().hex[:8]}@UFL.EDU  "
    expected_email = raw_email.strip().lower()
    username = f"norm_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": raw_email,
                "username": username,
                "password": "valid-normalize-password-123",
                "remember_me": False,
            },
        )
        assert response.status_code == 201
        assert response.json()["user"]["email"] == expected_email

        user_result = await db_session.exec(
            sa.select(User).where(User.email == expected_email)  # pyright: ignore[reportArgumentType]
        )
        user = user_result.scalars().one_or_none()
        assert user is not None
        assert user.email == expected_email
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_email_is_normalized_for_lookup(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    normalized_email = f"login-norm-{uuid4().hex[:8]}@ufl.edu"
    username = f"lognorm_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        signup = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": normalized_email,
                "username": username,
                "password": "valid-login-normalized-password-123",
                "remember_me": False,
            },
        )
        assert signup.status_code == 201

        login = await api_client.post(
            "/api/v1/auth/login",
            json={
                "email": f"  {normalized_email.upper()}  ",
                "password": "valid-login-normalized-password-123",
                "remember_me": False,
            },
        )
        assert login.status_code == 200
        assert login.json()["user"]["email"] == normalized_email
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_invalid_credentials_are_generic_for_wrong_email_and_password(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"invalid-generic-{uuid4().hex[:8]}@ufl.edu"
    password = "valid-generic-password-123"
    username = f"inval_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        signup = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
                "password": password,
                "remember_me": False,
            },
        )
        assert signup.status_code == 201

        wrong_password = await api_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrong-password-123"},
        )
        assert wrong_password.status_code == 401
        assert wrong_password.json()["detail"] == "Invalid credentials"

        wrong_email = await api_client.post(
            "/api/v1/auth/login",
            json={"email": f"missing-{uuid4().hex[:8]}@ufl.edu", "password": password},
        )
        assert wrong_email.status_code == 401
        assert wrong_email.json()["detail"] == "Invalid credentials"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_auth_me_uses_issued_access_token(api_client, db_session, monkeypatch):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"me-{uuid4().hex[:8]}@ufl.edu"
    username = f"me_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        signup = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
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
        assert payload["username"] == username
        assert "created_at" in payload
        assert "updated_at" in payload
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_auth_me_excludes_sensitive_user_fields(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"me-safe-{uuid4().hex[:8]}@ufl.edu"
    username = f"mesafe_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        signup = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
                "password": "valid-me-safe-password-123",
                "remember_me": False,
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
        forbidden_keys = {
            "password_hash",
            "refresh_token",
            "refresh_token_expires_in",
            "token_hash",
            "expires_at",
            "revoked_at",
            "refresh_sessions",
        }
        assert forbidden_keys.isdisjoint(payload.keys())
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_refresh_rotates_and_logout_is_idempotent(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"refresh-{uuid4().hex[:8]}@ufl.edu"
    username = f"refresh_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        signup = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
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


@pytest.mark.asyncio
async def test_signup_duplicate_email_race_returns_one_201_and_one_409(
    api_client, async_engine: AsyncEngine, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"race-signup-{uuid4().hex[:8]}@ufl.edu"
    username = f"race_{uuid4().hex[:8]}"
    payload = {
        "email": email,
        "username": username,
        "password": "valid-race-password-123",
        "full_name": "Race Signup",
        "remember_me": False,
    }

    async def override_get_db():
        async with AsyncSession(async_engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        first, second = await asyncio.gather(
            api_client.post("/api/v1/auth/signup", json=payload),
            api_client.post("/api/v1/auth/signup", json=payload),
        )
        statuses = sorted([first.status_code, second.status_code])
        assert statuses == [201, 409]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_refresh_rejects_revoked_token(api_client, db_session, monkeypatch):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"revoked-refresh-{uuid4().hex[:8]}@ufl.edu"
    username = f"revoke_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        signup = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
                "password": "valid-revoke-password-123",
                "remember_me": False,
            },
        )
        assert signup.status_code == 201
        refresh_token = signup.json()["refresh_token"]

        logout_response = await api_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert logout_response.status_code == 204

        refresh_response = await api_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 401
        assert refresh_response.json()["detail"] == "Invalid refresh token"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_concurrent_refresh_with_same_token_only_one_succeeds(
    api_client, async_engine: AsyncEngine, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"concurrent-refresh-{uuid4().hex[:8]}@ufl.edu"
    username = f"conref_{uuid4().hex[:8]}"

    async def override_get_db():
        async with AsyncSession(async_engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        signup = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
                "password": "valid-concurrency-password-123",
                "remember_me": False,
            },
        )
        assert signup.status_code == 201
        refresh_token = signup.json()["refresh_token"]

        responses = await asyncio.gather(
            api_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            ),
            api_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            ),
            api_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            ),
        )
        success_count = sum(resp.status_code == 200 for resp in responses)
        invalid_count = sum(resp.status_code == 401 for resp in responses)
        assert success_count == 1
        assert invalid_count == 2
        assert all(
            resp.status_code == 200
            or resp.json().get("detail") == "Invalid refresh token"
            for resp in responses
        )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_signup_duplicate_email_sequential_returns_409(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"dup-seq-{uuid4().hex[:8]}@ufl.edu"
    username = f"dupseq_{uuid4().hex[:8]}"
    payload = {
        "email": email,
        "username": username,
        "password": "valid-duplicate-password-123",
        "remember_me": False,
    }

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        first = await api_client.post("/api/v1/auth/signup", json=payload)
        assert first.status_code == 201

        second = await api_client.post("/api/v1/auth/signup", json=payload)
        assert second.status_code == 409
        assert second.json()["detail"] == "Email already registered"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_signup_duplicate_email_case_variant_sequential_returns_409(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    first_email = f"Case-Seq-{uuid4().hex[:8]}@UFL.EDU"
    second_email = f"  {first_email.lower()}  "
    username = f"caseseq_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        first = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": first_email,
                "username": username,
                "password": "valid-duplicate-case-password-123",
                "remember_me": False,
            },
        )
        assert first.status_code == 201

        second = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": second_email,
                "username": username,
                "password": "valid-duplicate-case-password-123",
                "remember_me": False,
            },
        )
        assert second.status_code == 409
        assert second.json()["detail"] == "Email already registered"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_signup_duplicate_email_case_variant_race_returns_one_201_and_one_409(
    api_client, async_engine: AsyncEngine, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    canonical_email = f"race-case-{uuid4().hex[:8]}@ufl.edu"
    username = f"racecase_{uuid4().hex[:8]}"
    first_payload = {
        "email": canonical_email.upper(),
        "username": username,
        "password": "valid-race-case-password-123",
        "remember_me": False,
    }
    second_payload = {
        "email": f"  {canonical_email}  ",
        "username": username,
        "password": "valid-race-case-password-123",
        "remember_me": False,
    }

    async def override_get_db():
        async with AsyncSession(async_engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        first, second = await asyncio.gather(
            api_client.post("/api/v1/auth/signup", json=first_payload),
            api_client.post("/api/v1/auth/signup", json=second_payload),
        )
        statuses = sorted([first.status_code, second.status_code])
        assert statuses == [201, 409]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_logout_after_token_already_revoked_remains_204(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"logout-revoked-{uuid4().hex[:8]}@ufl.edu"
    username = f"logout_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        signup = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
                "password": "valid-logout-revoked-password-123",
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

        # The original token is already revoked by rotation.
        logout_response = await api_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": original_refresh_token},
        )
        assert logout_response.status_code == 204
        assert logout_response.content == b""
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_password_is_not_trimmed_or_normalized(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)
    email = f"password-raw-{uuid4().hex[:8]}@ufl.edu"
    raw_password = "  pass phrase with spaces  "
    username = f"rawpwd_{uuid4().hex[:8]}"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        signup = await api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
                "password": raw_password,
                "remember_me": False,
            },
        )
        assert signup.status_code == 201

        exact_login = await api_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": raw_password},
        )
        assert exact_login.status_code == 200

        normalized_login = await api_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": raw_password.strip()},
        )
        assert normalized_login.status_code == 401
        assert normalized_login.json()["detail"] == "Invalid credentials"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"refresh_token": ""},
        {"refresh_token": None},
    ],
)
async def test_refresh_structurally_invalid_body_returns_422(
    api_client, db_session, monkeypatch, payload: dict[str, object]
):
    jwt_secret = "integration-auth-routes-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.post("/api/v1/auth/refresh", json=payload)
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
