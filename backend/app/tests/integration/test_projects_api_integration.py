from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import select

from app.api.deps.auth import get_current_user, get_current_user_optional
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


def _create_project_payload(**overrides):
    payload = {
        "title": "  API Create Project  ",
        "description": "  API create project description  ",
        "github_url": "https://github.com/example/api-create",
    }
    payload.update(overrides)
    return payload


def _override_authed_user(user: User):
    return lambda: user


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
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(project.id)
    assert payload["is_published"] is True


@pytest.mark.asyncio
async def test_create_project_authenticated_returns_201_and_persists_draft(
    api_client, db_session
):
    creator = await _seed_user(db_session, "creator_api@ufl.edu", "Creator API")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["created_by_id"] == str(creator.id)
    assert payload["title"] == "API Create Project"
    assert payload["description"] == "API create project description"
    assert payload["github_url"] == "https://github.com/example/api-create"
    assert payload["is_published"] is False
    assert payload["published_at"] is None
    assert payload["vote_count"] == 0
    assert payload["is_group_project"] is False
    assert [m["user_id"] for m in payload["members"]] == [str(creator.id)]
    assert [m["role"] for m in payload["members"]] == ["owner"]

    project_id = payload["id"]
    project_result = await db_session.exec(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.one()
    assert project.created_by_id == creator.id
    assert project.is_published is False
    assert project.published_at is None

    member_result = await db_session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == creator.id,
        )
    )
    member = member_result.one()
    assert member.role == "owner"


@pytest.mark.asyncio
async def test_create_project_unauthenticated_returns_401(api_client, db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_project_missing_title_returns_422(api_client, db_session):
    creator = await _seed_user(
        db_session, "creator_missing_title@ufl.edu", "Creator MT"
    )
    payload = _create_project_payload()
    payload.pop("title")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        response = await api_client.post("/api/v1/projects", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_project_blank_title_or_description_returns_422(
    api_client, db_session
):
    creator = await _seed_user(db_session, "creator_blank@ufl.edu", "Creator Blank")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        title_response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(title="   "),
        )
        description_response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(description="   "),
        )
    finally:
        app.dependency_overrides.clear()

    assert title_response.status_code == 422
    assert description_response.status_code == 422


@pytest.mark.asyncio
async def test_create_project_requires_at_least_one_url_returns_422(
    api_client, db_session
):
    creator = await _seed_user(db_session, "creator_no_urls@ufl.edu", "Creator No URLs")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(
                demo_url=None,
                github_url=None,
                video_url=None,
            ),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(
        "Provide at least one of demo_url, github_url, or video_url."
        in str(error.get("msg", ""))
        for error in errors
    )


@pytest.mark.asyncio
async def test_create_project_invalid_url_returns_422(api_client, db_session):
    creator = await _seed_user(db_session, "creator_bad_url@ufl.edu", "Creator Bad URL")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(github_url="not-a-url"),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_project_accepts_http_and_https_urls(api_client, db_session):
    creator = await _seed_user(db_session, "creator_http_https@ufl.edu", "Creator URLs")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(
                demo_url="http://example.com/demo",
                github_url=None,
                video_url="https://example.com/video",
            ),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["demo_url"] == "http://example.com/demo"
    assert payload["video_url"] == "https://example.com/video"


@pytest.mark.asyncio
async def test_create_project_normalizes_empty_urls_to_null_in_response_and_db(
    api_client, db_session
):
    creator = await _seed_user(db_session, "creator_norm_urls@ufl.edu", "Creator Norm")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(
                demo_url="   ",
                github_url="https://github.com/example/normalized-api",
                video_url="",
            ),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["demo_url"] is None
    assert payload["github_url"] == "https://github.com/example/normalized-api"
    assert payload["video_url"] is None

    project_result = await db_session.exec(
        select(Project).where(Project.id == payload["id"])
    )
    project = project_result.one()
    assert project.demo_url is None
    assert project.github_url == "https://github.com/example/normalized-api"
    assert project.video_url is None


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
    app.dependency_overrides[get_current_user_optional] = lambda: None
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
    app.dependency_overrides[get_current_user_optional] = lambda: member
    try:
        response = await api_client.get(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(project.id)
    assert [m["user_id"] for m in payload["members"]] == [str(member.id)]


@pytest.mark.asyncio
async def test_get_project_detail_unpublished_forbidden_to_authenticated_non_member(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, f"owner_api_forbid_{uuid4().hex[:8]}@ufl.edu", "Owner API Forbid"
    )
    stranger = await _seed_user(
        db_session, f"stranger_api_{uuid4().hex[:8]}@ufl.edu", "Stranger API"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Forbidden Draft API Project",
        is_published=False,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: stranger
    try:
        response = await api_client.get(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project access forbidden"


@pytest.mark.asyncio
async def test_list_projects_returns_only_published(api_client, db_session):
    owner = await _seed_user(db_session, "owner_api_list_pub@ufl.edu", "Owner List")
    published = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Published List API Project",
        is_published=True,
    )
    _draft = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Draft List API Project",
        is_published=False,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get("/api/v1/projects")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [str(published.id)]


@pytest.mark.asyncio
async def test_list_projects_sort_new_and_cursor_pagination(api_client, db_session):
    owner = await _seed_user(db_session, "owner_api_list_new@ufl.edu", "Owner List New")

    now = datetime.now(timezone.utc)
    oldest = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Oldest API Feed Project",
        is_published=True,
    )
    oldest.created_at = now - timedelta(minutes=2)
    oldest.updated_at = oldest.created_at

    middle = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Middle API Feed Project",
        is_published=True,
    )
    middle.created_at = now - timedelta(minutes=1)
    middle.updated_at = middle.created_at

    newest = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Newest API Feed Project",
        is_published=True,
    )
    newest.created_at = now
    newest.updated_at = newest.created_at
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        page_one = await api_client.get("/api/v1/projects?sort=new&limit=2")
        assert page_one.status_code == 200
        page_one_payload = page_one.json()
        assert [item["id"] for item in page_one_payload["items"]] == [
            str(newest.id),
            str(middle.id),
        ]
        assert page_one_payload["next_cursor"] is not None

        page_two = await api_client.get(
            f"/api/v1/projects?sort=new&limit=2&cursor={page_one_payload['next_cursor']}"
        )
    finally:
        app.dependency_overrides.clear()

    assert page_two.status_code == 200
    page_two_payload = page_two.json()
    assert [item["id"] for item in page_two_payload["items"]] == [str(oldest.id)]


@pytest.mark.asyncio
async def test_list_projects_invalid_cursor_returns_400(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_api_list_cursor@ufl.edu", "Owner List Cursor"
    )
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Cursor API Feed Project",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get("/api/v1/projects?cursor=not-a-cursor")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid cursor"


@pytest.mark.asyncio
async def test_list_projects_limit_is_clamped(api_client, db_session):
    owner = await _seed_user(db_session, "owner_api_limit@ufl.edu", "Owner Limit")
    for index in range(105):
        await _seed_project(
            db_session,
            created_by_id=owner.id,
            title=f"Limit Project {index}",
            is_published=True,
        )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response_low = await api_client.get("/api/v1/projects?limit=0")
        response_high = await api_client.get("/api/v1/projects?limit=500")
    finally:
        app.dependency_overrides.clear()

    assert response_low.status_code == 200
    assert len(response_low.json()["items"]) == 1

    assert response_high.status_code == 200
    assert len(response_high.json()["items"]) == 100


@pytest.mark.asyncio
async def test_list_projects_top_default_window_excludes_old_projects(
    api_client, db_session
):
    owner = await _seed_user(db_session, "owner_api_top_window@ufl.edu", "Owner Top")
    now = datetime.now(timezone.utc)

    recent = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Recent API Top Project",
        is_published=True,
    )
    recent.created_at = now - timedelta(days=7)
    recent.updated_at = recent.created_at
    recent.published_at = recent.created_at

    old = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Old API Top Project",
        is_published=True,
    )
    old.created_at = now - timedelta(days=140)
    old.updated_at = old.created_at
    old.published_at = old.created_at
    old.vote_count = 999
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get("/api/v1/projects?sort=top")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [str(recent.id)]


@pytest.mark.asyncio
async def test_list_projects_top_cursor_range_mismatch_returns_400(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_api_range_mismatch@ufl.edu", "Owner Range Mismatch"
    )
    for title in ("Range Project A", "Range Project B"):
        await _seed_project(
            db_session,
            created_by_id=owner.id,
            title=title,
            is_published=True,
        )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        page_one = await api_client.get("/api/v1/projects?sort=top&limit=1")
        assert page_one.status_code == 200
        next_cursor = page_one.json()["next_cursor"]
        assert next_cursor is not None

        mismatch_response = await api_client.get(
            "/api/v1/projects?sort=top&limit=1"
            f"&published_from=2020-01-01&published_to=2020-12-31&cursor={next_cursor}"
        )
    finally:
        app.dependency_overrides.clear()

    assert mismatch_response.status_code == 400
    assert mismatch_response.json()["detail"] == "Invalid cursor"


@pytest.mark.asyncio
async def test_list_projects_cursor_sort_mismatch_returns_400(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_api_sort_mismatch@ufl.edu", "Owner Sort Mismatch"
    )
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Sort Mismatch Project A",
        is_published=True,
    )
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Sort Mismatch Project B",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        top_page = await api_client.get("/api/v1/projects?sort=top&limit=1")
        assert top_page.status_code == 200
        next_cursor = top_page.json()["next_cursor"]
        assert next_cursor is not None

        mismatch_response = await api_client.get(
            f"/api/v1/projects?sort=new&cursor={next_cursor}"
        )
    finally:
        app.dependency_overrides.clear()

    assert mismatch_response.status_code == 400
    assert mismatch_response.json()["detail"] == "Invalid cursor"
