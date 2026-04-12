import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.api.deps.auth import get_current_user, get_current_user_optional
from app.db.database import get_db
from app.main import app
from app.models.comment import Comment
from app.models.comment_like import CommentLike


from httpx import ASGITransport, AsyncClient
import pytest_asyncio

@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

async def _seed_user(db_session, email: str, role: str = "member"):
    from app.models.user import User
    now = datetime.now(timezone.utc)
    user = User(
        email=email,
        username=f"user_{uuid4().hex[:10]}",
        password_hash="integration-password-hash",
        full_name="Comment Test User",
        clerk_id=f"test_clerk_{uuid4().hex[:8]}",
        role=role,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _seed_project(db_session, owner_id):
    from app.models.project import Project
    project = Project(
        created_by_id=owner_id,
        title=f"Test Project {uuid4().hex[:8]}",
        slug=f"tp-{uuid4().hex[:8]}",
        short_description="Desc",
        is_published=True,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


def _override_authed_user(user):
    return lambda: user


@pytest.mark.asyncio
async def test_create_comment(api_client, db_session):
    user = await _seed_user(db_session, f"creator_{uuid4().hex[:8]}@test.com")
    project = await _seed_project(db_session, user.id)

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = _override_authed_user(user)

    response = await api_client.post(
        f"/api/v1/projects/{project.id}/comments",
        json={"body": "This is a great project!"}
    )

    app.dependency_overrides.clear()
    assert response.status_code == 201
    data = response.json()
    assert data["body"] == "This is a great project!"
    assert data["author_id"] == str(user.id)
    assert data["project_id"] == str(project.id)


@pytest.mark.asyncio
async def test_list_comments(api_client, db_session):
    user = await _seed_user(db_session, f"viewer_{uuid4().hex[:8]}@test.com")
    project = await _seed_project(db_session, user.id)

    # Seed comments
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = _override_authed_user(user)
    
    await api_client.post(
        f"/api/v1/projects/{project.id}/comments",
        json={"body": "First"}
    )
    await api_client.post(
        f"/api/v1/projects/{project.id}/comments",
        json={"body": "Second"}
    )

    app.dependency_overrides[get_current_user_optional] = _override_authed_user(user)
    
    response = await api_client.get(f"/api/v1/projects/{project.id}/comments?sort=oldest")
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["body"] == "First"
    assert data[1]["body"] == "Second"


@pytest.mark.asyncio
async def test_delete_own_comment(api_client, db_session):
    user = await _seed_user(db_session, f"deleter_{uuid4().hex[:8]}@test.com")
    project = await _seed_project(db_session, user.id)

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = _override_authed_user(user)
    
    c_resp = await api_client.post(
        f"/api/v1/projects/{project.id}/comments",
        json={"body": "To be deleted"}
    )
    comment_id = c_resp.json()["id"]

    del_resp = await api_client.delete(f"/api/v1/comments/{comment_id}")
    assert del_resp.status_code == 204

    # Verify not listed or listed as deleted
    list_resp = await api_client.get(f"/api/v1/projects/{project.id}/comments")
    app.dependency_overrides.clear()
    data = list_resp.json()
    assert len(data) == 1
    assert data[0]["is_deleted"] is True
    assert data[0]["body"] == "[This comment has been removed or hidden by moderation]"


@pytest.mark.asyncio
async def test_admin_moderation(api_client, db_session):
    admin = await _seed_user(db_session, f"admin_{uuid4().hex[:8]}@test.com", role="admin")
    user = await _seed_user(db_session, f"user_{uuid4().hex[:8]}@test.com")
    project = await _seed_project(db_session, user.id)

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = _override_authed_user(user)
    c_resp = await api_client.post(
        f"/api/v1/projects/{project.id}/comments",
        json={"body": "Inappropriate comment"}
    )
    comment_id = c_resp.json()["id"]

    app.dependency_overrides[get_current_user] = _override_authed_user(admin)
    mod_resp = await api_client.patch(f"/api/v1/comments/{comment_id}/moderate?state=hidden")
    assert mod_resp.status_code == 204
    
    list_resp = await api_client.get(f"/api/v1/projects/{project.id}/comments")
    app.dependency_overrides.clear()
    
    data = list_resp.json()
    assert data[0]["moderation_state"] == "hidden"
    assert data[0]["body"] == "[This comment has been removed or hidden by moderation]"

