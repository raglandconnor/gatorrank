from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_user
from app.main import app
from app.models.user import User


from app.core.config import get_settings

# Force local HS256 JWT mocking for pytests instead of remote Supabase calls
get_settings().SUPABASE_URL = None
get_settings().SUPABASE_KEY = None


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_user():
    return User(id=uuid4(), email="test@ufl.edu", role="student")  # pyright: ignore[reportCallIssue]


@pytest.fixture
def authenticated_client(client, mock_user):
    # Override the auth dependency to inject the mock user for protected routes
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield client
    app.dependency_overrides.clear()
