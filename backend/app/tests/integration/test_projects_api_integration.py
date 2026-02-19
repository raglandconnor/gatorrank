from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps.auth import get_current_user_id_optional
from app.db.database import get_db
from app.main import app
from app.models.project import Project, ProjectMember
from app.models.user import User


@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def _seed_user(db_session, email: str, name: str) -> User:
    now = datetime.now(timezone.utc)
    user = User(email=email, full_name=name, created_at=now, updated_at=now)
    db_session.add(user)
    await db_session.flush()
    return user


async def _seed_project(
    db_session,
    *,
    created_by_id,
    title: str,
    is_published: bool,
) -> Project:
    now = datetime.now(timezone.utc)
    project = Project(
        created_by_id=created_by_id,
        title=title,
        description=f"{title} description",
        vote_count=0,
        is_group_project=False,
        is_published=is_published,
        published_at=now if is_published else None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(project)
    await db_session.flush()
    return project


async def _seed_member(db_session, *, project_id, user_id, role: str) -> None:
    now = datetime.now(timezone.utc)
    member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role=role,
        added_at=now,
    )
    db_session.add(member)
    await db_session.flush()


@pytest.mark.asyncio
async def test_get_project_detail_published_visible_anonymous(api_client, db_session):
    owner = await _seed_user(db_session, "owner_api_pub@ufl.edu", "Owner API Pub")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Published API Project",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id_optional] = lambda: None
    try:
        response = await api_client.get(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(project.id)
    assert payload["is_published"] is True


@pytest.mark.asyncio
async def test_get_project_detail_unpublished_hidden_anonymous(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_api_private@ufl.edu", "Owner API Private"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Hidden API Project",
        is_published=False,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id_optional] = lambda: None
    try:
        response = await api_client.get(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


@pytest.mark.asyncio
async def test_get_project_detail_unpublished_visible_to_member(api_client, db_session):
    owner = await _seed_user(
        db_session, f"owner_api_member_{uuid4().hex[:8]}@ufl.edu", "Owner API Member"
    )
    member = await _seed_user(
        db_session, f"member_api_{uuid4().hex[:8]}@ufl.edu", "Member API"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Member Visible API Project",
        is_published=False,
    )
    await _seed_member(
        db_session,
        project_id=project.id,
        user_id=member.id,
        role="contributor",
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id_optional] = lambda: member.id
    try:
        response = await api_client.get(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(project.id)
    assert [m["user_id"] for m in payload["members"]] == [str(member.id)]
