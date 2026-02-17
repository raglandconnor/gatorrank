from fastapi.testclient import TestClient

from app.db.database import get_db
from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["message"] == "API is running"
    assert "timestamp" in payload
    assert payload["timestamp"].endswith("Z") or "+" in payload["timestamp"]


def test_db_health_endpoint_success():
    class MockResult:
        def scalar_one(self):
            from datetime import datetime, timezone

            return datetime.now(timezone.utc)

    class MockSession:
        async def execute(self, _query):
            return MockResult()

    async def override_get_db():
        yield MockSession()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/v1/db-health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "connected"
    assert payload["message"] == "Database connection successful"
    assert "timestamp" in payload
    assert payload["timestamp"].endswith("Z") or "+" in payload["timestamp"]


def test_db_health_endpoint_failure():
    class MockSession:
        async def execute(self, _query):
            raise RuntimeError("db unavailable")

    async def override_get_db():
        yield MockSession()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/v1/db-health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    payload = response.json()
    assert payload["detail"] == "Database unavailable"
