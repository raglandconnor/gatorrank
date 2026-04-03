from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_user
from app.db.database import get_db
from app.main import app
from app.services.taxonomy import TaxonomyConflictError

client = TestClient(app)


async def _override_get_db():
    class MockSession:
        pass

    yield MockSession()


def _override_current_user(*, role: str):
    now = datetime.now(timezone.utc)
    return lambda: SimpleNamespace(
        id=uuid4(),
        email="taxonomy@ufl.edu",
        role=role,
        created_at=now,
        updated_at=now,
    )


def test_list_taxonomy_categories_requires_auth():
    response = client.get("/api/v1/taxonomy/categories")
    assert response.status_code == 401


def test_list_taxonomy_categories_returns_terms_for_authenticated_user():
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(role="student")
    terms = [{"id": str(uuid4()), "name": "Backend"}]
    try:
        with patch(
            "app.api.v1.taxonomy.TaxonomyService.list_categories",
            new=AsyncMock(return_value=terms),
        ):
            response = client.get("/api/v1/taxonomy/categories")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == terms


def test_create_taxonomy_category_requires_admin_role():
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(role="student")
    try:
        with patch(
            "app.api.v1.taxonomy.TaxonomyService.create_category",
            new=AsyncMock(),
        ) as mock_create:
            response = client.post(
                "/api/v1/taxonomy/categories",
                json={"name": "Backend"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Taxonomy management forbidden"
    assert mock_create.await_count == 0


def test_create_taxonomy_category_admin_success():
    term = {"id": str(uuid4()), "name": "Backend"}
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(role="admin")
    try:
        with patch(
            "app.api.v1.taxonomy.TaxonomyService.create_category",
            new=AsyncMock(return_value=term),
        ):
            response = client.post(
                "/api/v1/taxonomy/categories",
                json={"name": "Backend"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == term


def test_create_taxonomy_category_conflict_returns_409():
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(role="admin")
    try:
        with patch(
            "app.api.v1.taxonomy.TaxonomyService.create_category",
            new=AsyncMock(
                side_effect=TaxonomyConflictError("Taxonomy term already exists")
            ),
        ):
            response = client.post(
                "/api/v1/taxonomy/categories",
                json={"name": "Backend"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == "Taxonomy term already exists"


def test_create_taxonomy_category_invalid_name_returns_422():
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(role="admin")
    try:
        with patch(
            "app.api.v1.taxonomy.TaxonomyService.create_category",
            new=AsyncMock(),
        ) as mock_create:
            response = client.post(
                "/api/v1/taxonomy/categories",
                json={"name": " "},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert mock_create.await_count == 0
