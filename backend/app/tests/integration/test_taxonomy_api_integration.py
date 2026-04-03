from datetime import datetime, timezone
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import select

from app.api.deps.auth import get_current_user
from app.db.database import get_db
from app.main import app
from app.models.taxonomy import Category
from app.models.user import User


@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def _seed_user(db_session, *, email: str, role: str) -> User:
    now = datetime.now(timezone.utc)
    user = User(
        email=email,
        password_hash="integration-password-hash",
        role=role,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def _seed_category(db_session, *, name: str, normalized_name: str) -> Category:
    now = datetime.now(timezone.utc)
    category = Category(name=name, normalized_name=normalized_name, created_at=now)
    db_session.add(category)
    await db_session.flush()
    return category


def _override_authed_user(user: User):
    return lambda: user


@pytest.mark.asyncio
async def test_list_categories_requires_auth(api_client, db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get("/api/v1/taxonomy/categories")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_categories_returns_full_alphabetical_list(api_client, db_session):
    viewer = await _seed_user(
        db_session, email="taxonomy-viewer@ufl.edu", role="student"
    )
    await _seed_category(db_session, name="zeta", normalized_name="zeta")
    await _seed_category(db_session, name="Alpha", normalized_name="alpha")
    await _seed_category(db_session, name="beta", normalized_name="beta")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(viewer)
    try:
        response = await api_client.get("/api/v1/taxonomy/categories")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Alpha", "beta", "zeta"]


@pytest.mark.asyncio
async def test_create_category_requires_admin(api_client, db_session):
    viewer = await _seed_user(
        db_session, email="taxonomy-non-admin@ufl.edu", role="student"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(viewer)
    try:
        response = await api_client.post(
            "/api/v1/taxonomy/categories",
            json={"name": "Backend"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Taxonomy management forbidden"


@pytest.mark.asyncio
async def test_create_category_admin_success_and_normalized_persisted(
    api_client, db_session
):
    admin = await _seed_user(db_session, email="taxonomy-admin@ufl.edu", role="admin")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(admin)
    try:
        response = await api_client.post(
            "/api/v1/taxonomy/categories",
            json={"name": "  Backend Tools  "},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Backend Tools"

    result = await db_session.exec(
        select(Category).where(Category.id == UUID(payload["id"]))
    )
    created = result.one()
    assert created.normalized_name == "backend tools"


@pytest.mark.asyncio
async def test_create_category_duplicate_returns_409(api_client, db_session):
    admin = await _seed_user(
        db_session, email="taxonomy-admin-dup@ufl.edu", role="admin"
    )
    await _seed_category(db_session, name="Backend", normalized_name="backend")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(admin)
    try:
        response = await api_client.post(
            "/api/v1/taxonomy/categories",
            json={"name": " backend "},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == "Taxonomy term already exists"
