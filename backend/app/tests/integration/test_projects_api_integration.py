import asyncio
from datetime import date, datetime, timedelta, timezone
from time import perf_counter
from urllib.parse import quote
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from app.api.deps.auth import get_current_user, get_current_user_optional
from app.db.database import get_db
from app.main import app
from app.models.project import Project, ProjectMember, Vote
from app.models.taxonomy import (
    Category,
    ProjectCategory,
    ProjectTag,
    ProjectTechStack,
    Tag,
    TechStack,
)
from app.models.user import User


@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def _seed_user(db_session, email: str, name: str) -> User:
    now = datetime.now(timezone.utc)
    user = User(
        email=email,
        username=f"user_{uuid4().hex[:10]}",
        password_hash="integration-password-hash",
        full_name=name,
        created_at=now,
        updated_at=now,
    )
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
        slug=title.lower().replace(" ", "-"),
        short_description=f"{title} description",
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


async def _seed_vote(
    db_session,
    *,
    project_id,
    user_id,
    created_at: datetime | None = None,
) -> Vote:
    now = created_at or datetime.now(timezone.utc)
    vote = Vote(
        project_id=project_id,
        user_id=user_id,
        created_at=now,
    )
    db_session.add(vote)
    await db_session.flush()
    return vote


async def _seed_taxonomy_term(
    db_session,
    *,
    model: type[Category] | type[Tag] | type[TechStack],
    name: str,
):
    term = model(
        name=name,
        normalized_name=name.strip().lower(),
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(term)
    await db_session.flush()
    return term


def _create_project_payload(**overrides):
    payload = {
        "title": "  API Create Project  ",
        "short_description": "  API create project description  ",
        "github_url": "https://github.com/example/api-create",
    }
    payload.update(overrides)
    return payload


def _update_project_payload(**overrides):
    payload = {
        "title": "  Updated API Project  ",
        "short_description": "  Updated API description  ",
        "demo_url": "https://example.com/updated-demo",
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
    assert payload["slug"] == project.slug
    assert payload["is_published"] is True


@pytest.mark.asyncio
async def test_get_project_detail_by_slug_published_visible_anonymous(
    api_client, db_session
):
    owner = await _seed_user(db_session, "owner_api_slug_pub@ufl.edu", "Owner API Slug")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Published Slug API Project",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get(f"/api/v1/projects/slug/{project.slug}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(project.id)
    assert payload["slug"] == project.slug


@pytest.mark.asyncio
async def test_get_project_detail_by_slug_unpublished_hidden_anonymous(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_api_slug_hidden@ufl.edu", "Owner API Slug Hidden"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Hidden Slug API Project",
        is_published=False,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get(f"/api/v1/projects/slug/{project.slug}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


@pytest.mark.asyncio
async def test_get_project_detail_by_slug_normalizes_case_and_whitespace(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_api_slug_normalize@ufl.edu", "Owner API Slug Normalize"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Normalize Slug API Project",
        is_published=True,
    )
    slug_with_whitespace_and_case = quote(f"  {project.slug.upper()}  ", safe="")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get(
            f"/api/v1/projects/slug/{slug_with_whitespace_and_case}"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(project.id)
    assert payload["slug"] == project.slug


@pytest.mark.asyncio
async def test_get_project_detail_by_slug_soft_deleted_returns_404(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_api_slug_deleted@ufl.edu", "Owner API Slug Deleted"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Deleted Slug API Project",
        is_published=True,
    )
    project.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get(f"/api/v1/projects/slug/{project.slug}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


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
    assert payload["slug"] == "api-create-project"
    assert payload["short_description"] == "API create project description"
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
            json=_create_project_payload(short_description="   "),
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
async def test_create_project_rejects_timeline_end_without_start(
    api_client, db_session
):
    creator = await _seed_user(
        db_session, "creator_timeline_end_only@ufl.edu", "Creator Timeline End Only"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(
                timeline_start_date=None,
                timeline_end_date="2026-03-31",
            ),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_project_rejects_timeline_start_after_end(api_client, db_session):
    creator = await _seed_user(
        db_session, "creator_timeline_order@ufl.edu", "Creator Timeline Order"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(
                timeline_start_date="2026-04-01",
                timeline_end_date="2026-03-31",
            ),
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
async def test_patch_project_owner_can_update_published_project(api_client, db_session):
    owner = await _seed_user(db_session, "owner_patch_api@ufl.edu", "Owner Patch API")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Patch API Target",
        is_published=True,
    )
    project.demo_url = "https://example.com/original-demo"
    project.github_url = None
    project.video_url = None
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}",
            json=_update_project_payload(
                demo_url="", github_url="https://github.com/example/updated-api"
            ),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(project.id)
    assert payload["title"] == "Updated API Project"
    assert payload["short_description"] == "Updated API description"
    assert payload["demo_url"] is None
    assert payload["github_url"] == "https://github.com/example/updated-api"
    assert payload["is_published"] is True

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    updated = project_result.one()
    assert updated.title == "Updated API Project"
    assert updated.demo_url is None
    assert updated.github_url == "https://github.com/example/updated-api"


@pytest.mark.asyncio
async def test_patch_project_owner_updates_non_url_fields_with_existing_url(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_patch_non_url@ufl.edu", "Owner Patch Non URL"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Patch Non URL Target",
        is_published=False,
    )
    project.github_url = "https://github.com/example/existing-url"
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}",
            json={
                "title": "  Retitled Project  ",
                "short_description": "  Revised summary  ",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Retitled Project"
    assert payload["short_description"] == "Revised summary"
    assert payload["github_url"] == "https://github.com/example/existing-url"


@pytest.mark.asyncio
async def test_patch_project_title_does_not_mutate_slug(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_patch_slug_immutable@ufl.edu", "Owner Patch Immutable"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Immutable Slug Source Title",
        is_published=False,
    )
    project.github_url = "https://github.com/example/immutable-slug"
    await db_session.flush()
    original_slug = project.slug

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}",
            json={"title": "Completely Changed Title"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Completely Changed Title"
    assert payload["slug"] == original_slug

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    stored_project = project_result.one()
    assert stored_project.title == "Completely Changed Title"
    assert stored_project.slug == original_slug


@pytest.mark.asyncio
async def test_patch_project_unauthenticated_returns_401(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_patch_anon_api@ufl.edu", "Owner Patch Anonymous API"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Patch Anonymous API Target",
        is_published=False,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}",
            json=_update_project_payload(),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_patch_project_non_owner_returns_403(api_client, db_session):
    owner = await _seed_user(db_session, "owner_patch_403@ufl.edu", "Owner Patch 403")
    maintainer = await _seed_user(
        db_session, "maintainer_patch_403@ufl.edu", "Maintainer Patch 403"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Patch Forbidden API Project",
        is_published=False,
    )
    await _seed_member(
        db_session,
        project_id=project.id,
        user_id=maintainer.id,
        role="maintainer",
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(maintainer)
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}",
            json=_update_project_payload(),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project edit forbidden"


@pytest.mark.asyncio
async def test_patch_project_not_found_returns_404(api_client, db_session):
    owner = await _seed_user(db_session, "owner_patch_404@ufl.edu", "Owner Patch 404")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.patch(
            "/api/v1/projects/00000000-0000-0000-0000-000000000777",
            json=_update_project_payload(),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


@pytest.mark.asyncio
async def test_patch_project_empty_payload_returns_422(api_client, db_session):
    owner = await _seed_user(db_session, "owner_patch_422a@ufl.edu", "Owner Patch 422A")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Patch 422 Empty",
        is_published=False,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.patch(f"/api/v1/projects/{project.id}", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_project_rejects_is_group_project_field(api_client, db_session):
    owner = await _seed_user(db_session, "owner_patch_422b@ufl.edu", "Owner Patch 422B")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Patch 422 Group Flag",
        is_published=False,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}",
            json={"title": "Allowed", "is_group_project": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_project_invalid_url_returns_422(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_patch_invalid_url@ufl.edu", "Owner Patch Invalid URL"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Patch Invalid URL",
        is_published=False,
    )
    project.demo_url = "https://example.com/valid-demo"
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}",
            json={"github_url": "not-a-url"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_project_rejects_timeline_end_without_start(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_patch_timeline_end_only@ufl.edu", "Owner Patch Timeline End"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Patch Timeline End Without Start",
        is_published=False,
    )
    project.github_url = "https://github.com/example/patch-timeline-end"
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}",
            json={"timeline_end_date": "2026-03-31"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert (
        response.json()["detail"] == "timeline_end_date requires timeline_start_date."
    )


@pytest.mark.asyncio
async def test_patch_project_allows_clearing_timeline_end(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_patch_timeline_clear@ufl.edu", "Owner Patch Timeline Clear"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Patch Timeline Clear End",
        is_published=False,
    )
    project.github_url = "https://github.com/example/patch-timeline-clear"
    project.timeline_start_date = date(2026, 3, 1)
    project.timeline_end_date = date(2026, 3, 31)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}",
            json={"timeline_end_date": None},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["timeline_start_date"] == "2026-03-01"
    assert payload["timeline_end_date"] is None

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    updated = project_result.one()
    assert updated.timeline_start_date == date(2026, 3, 1)
    assert updated.timeline_end_date is None


@pytest.mark.asyncio
async def test_patch_project_rejects_clearing_last_url(api_client, db_session):
    owner = await _seed_user(db_session, "owner_patch_422c@ufl.edu", "Owner Patch 422C")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Patch 422 URL Rule",
        is_published=False,
    )
    project.github_url = "https://github.com/example/only-url"
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}",
            json={"github_url": None},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Provide at least one of demo_url, github_url, or video_url."
    )


@pytest.mark.asyncio
async def test_patch_project_rejects_null_title_and_description(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_patch_null_fields@ufl.edu", "Owner Patch Null Fields"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Patch Null Field Rule",
        is_published=False,
    )
    project.video_url = "https://example.com/video"
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        null_title = await api_client.patch(
            f"/api/v1/projects/{project.id}",
            json={"title": None},
        )
        null_description = await api_client.patch(
            f"/api/v1/projects/{project.id}",
            json={"short_description": None},
        )
    finally:
        app.dependency_overrides.clear()

    assert null_title.status_code == 422
    assert null_description.status_code == 422


@pytest.mark.asyncio
async def test_patch_project_updates_updated_at_timestamp(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_patch_updated_at@ufl.edu", "Owner Patch Updated At"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Patch Updated At",
        is_published=False,
    )
    project.demo_url = "https://example.com/demo"
    original_updated_at = datetime.now(timezone.utc) - timedelta(days=2)
    project.updated_at = original_updated_at
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}",
            json={"title": "Timestamp Updated"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = project_result.one()
    assert refreshed.updated_at > original_updated_at


@pytest.mark.asyncio
async def test_publish_project_owner_can_publish(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_publish_api@ufl.edu", "Owner Publish API"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Publish API Target",
        is_published=False,
    )
    project.github_url = "https://github.com/example/publish-api"
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.post(f"/api/v1/projects/{project.id}/publish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(project.id)
    assert payload["is_published"] is True
    assert payload["published_at"] is not None

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = project_result.one()
    assert refreshed.is_published is True
    assert refreshed.published_at is not None


@pytest.mark.asyncio
async def test_publish_project_makes_draft_visible_to_anonymous(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_publish_public@ufl.edu", "Owner Publish Public"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Publish Public API",
        is_published=False,
    )
    project.github_url = "https://github.com/example/publish-public"
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        publish_response = await api_client.post(
            f"/api/v1/projects/{project.id}/publish"
        )
    finally:
        app.dependency_overrides.clear()

    assert publish_response.status_code == 200

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        detail_response = await api_client.get(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert detail_response.status_code == 200
    payload = detail_response.json()
    assert payload["id"] == str(project.id)
    assert payload["is_published"] is True
    assert payload["published_at"] is not None


@pytest.mark.asyncio
async def test_publish_project_unauthenticated_returns_401(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_publish_auth@ufl.edu", "Owner Publish Auth"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Publish Auth API",
        is_published=False,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.post(f"/api/v1/projects/{project.id}/publish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_unpublish_project_unauthenticated_returns_401(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_unpublish_auth@ufl.edu", "Owner Unpublish Auth"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unpublish Auth API",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.post(f"/api/v1/projects/{project.id}/unpublish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_publish_project_is_idempotent(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_publish_idem@ufl.edu", "Owner Publish Idempotent"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Publish Idempotent API",
        is_published=True,
    )
    original_published_at = project.published_at
    assert original_published_at is not None

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.post(f"/api/v1/projects/{project.id}/publish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_published"] is True
    response_published_at = datetime.fromisoformat(
        payload["published_at"].replace("Z", "+00:00")
    )
    assert response_published_at == original_published_at

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = project_result.one()
    assert refreshed.published_at == original_published_at


@pytest.mark.asyncio
async def test_publish_project_not_found_returns_404(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_publish_404@ufl.edu", "Owner Publish 404"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.post(
            "/api/v1/projects/00000000-0000-0000-0000-000000000777/publish"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


@pytest.mark.asyncio
async def test_publish_project_non_owner_returns_403(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_publish_403@ufl.edu", "Owner Publish 403"
    )
    maintainer = await _seed_user(
        db_session, "maintainer_publish_403@ufl.edu", "Maintainer Publish 403"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Publish Forbidden API",
        is_published=False,
    )
    await _seed_member(
        db_session,
        project_id=project.id,
        user_id=maintainer.id,
        role="maintainer",
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(maintainer)
    try:
        response = await api_client.post(f"/api/v1/projects/{project.id}/publish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project publish forbidden"


@pytest.mark.asyncio
async def test_publish_project_authenticated_non_member_returns_403(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_publish_stranger@ufl.edu", "Owner Publish Stranger"
    )
    stranger = await _seed_user(
        db_session, "stranger_publish_403@ufl.edu", "Stranger Publish 403"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Publish Stranger Forbidden",
        is_published=False,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(stranger)
    try:
        response = await api_client.post(f"/api/v1/projects/{project.id}/publish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project publish forbidden"


@pytest.mark.asyncio
async def test_unpublish_project_owner_can_unpublish_and_hide_from_public(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_unpublish_api@ufl.edu", "Owner Unpublish API"
    )
    stranger = await _seed_user(
        db_session, "stranger_unpublish_api@ufl.edu", "Stranger Unpublish API"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unpublish API Target",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        unpublish_response = await api_client.post(
            f"/api/v1/projects/{project.id}/unpublish"
        )
    finally:
        app.dependency_overrides.clear()

    assert unpublish_response.status_code == 200
    unpublish_payload = unpublish_response.json()
    assert unpublish_payload["is_published"] is False
    assert unpublish_payload["published_at"] is None

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = project_result.one()
    assert refreshed.is_published is False
    assert refreshed.published_at is None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        anonymous_detail = await api_client.get(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert anonymous_detail.status_code == 404
    assert anonymous_detail.json()["detail"] == "Project not found"

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: stranger
    try:
        non_member_detail = await api_client.get(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert non_member_detail.status_code == 403
    assert non_member_detail.json()["detail"] == "Project access forbidden"


@pytest.mark.asyncio
async def test_unpublish_project_preserves_owner_and_member_visibility(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_unpublish_member@ufl.edu", "Owner Unpublish Member"
    )
    member = await _seed_user(
        db_session, "member_unpublish_member@ufl.edu", "Member Unpublish Member"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unpublish Member Visibility",
        is_published=True,
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
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        unpublish_response = await api_client.post(
            f"/api/v1/projects/{project.id}/unpublish"
        )
    finally:
        app.dependency_overrides.clear()

    assert unpublish_response.status_code == 200
    payload = unpublish_response.json()
    assert payload["is_published"] is False
    assert payload["published_at"] is None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: owner
    try:
        owner_detail = await api_client.get(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert owner_detail.status_code == 200

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: member
    try:
        member_detail = await api_client.get(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert member_detail.status_code == 200
    member_payload = member_detail.json()
    assert member_payload["is_published"] is False
    assert member_payload["published_at"] is None


@pytest.mark.asyncio
async def test_unpublish_project_is_idempotent(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_unpublish_idem@ufl.edu", "Owner Unpublish Idempotent"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unpublish Idempotent API",
        is_published=False,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.post(f"/api/v1/projects/{project.id}/unpublish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_published"] is False
    assert payload["published_at"] is None


@pytest.mark.asyncio
async def test_unpublish_project_not_found_returns_404(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_unpublish_404@ufl.edu", "Owner Unpublish 404"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.post(
            "/api/v1/projects/00000000-0000-0000-0000-000000000778/unpublish"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


@pytest.mark.asyncio
async def test_unpublish_project_non_owner_returns_403(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_unpublish_403@ufl.edu", "Owner Unpublish 403"
    )
    maintainer = await _seed_user(
        db_session, "maintainer_unpublish_403@ufl.edu", "Maintainer Unpublish 403"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unpublish Forbidden API",
        is_published=True,
    )
    await _seed_member(
        db_session,
        project_id=project.id,
        user_id=maintainer.id,
        role="maintainer",
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(maintainer)
    try:
        response = await api_client.post(f"/api/v1/projects/{project.id}/unpublish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project unpublish forbidden"


@pytest.mark.asyncio
async def test_unpublish_project_authenticated_non_member_returns_403(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_unpublish_stranger@ufl.edu", "Owner Unpublish Stranger"
    )
    stranger = await _seed_user(
        db_session, "stranger_unpublish_403@ufl.edu", "Stranger Unpublish 403"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unpublish Stranger Forbidden",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(stranger)
    try:
        response = await api_client.post(f"/api/v1/projects/{project.id}/unpublish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project unpublish forbidden"


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
async def test_list_projects_updates_visibility_after_publish_and_unpublish(
    api_client, db_session
):
    owner = await _seed_user(db_session, "owner_api_feed_toggle@ufl.edu", "Owner Feed")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Feed Toggle Project",
        is_published=False,
    )
    project.github_url = "https://github.com/example/feed-toggle"
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        initial_feed = await api_client.get("/api/v1/projects")
    finally:
        app.dependency_overrides.clear()

    assert initial_feed.status_code == 200
    initial_ids = [item["id"] for item in initial_feed.json()["items"]]
    assert str(project.id) not in initial_ids

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        publish_response = await api_client.post(
            f"/api/v1/projects/{project.id}/publish"
        )
    finally:
        app.dependency_overrides.clear()

    assert publish_response.status_code == 200

    app.dependency_overrides[get_db] = override_get_db
    try:
        after_publish_feed = await api_client.get("/api/v1/projects")
    finally:
        app.dependency_overrides.clear()

    assert after_publish_feed.status_code == 200
    after_publish_ids = [item["id"] for item in after_publish_feed.json()["items"]]
    assert str(project.id) in after_publish_ids

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        unpublish_response = await api_client.post(
            f"/api/v1/projects/{project.id}/unpublish"
        )
    finally:
        app.dependency_overrides.clear()

    assert unpublish_response.status_code == 200

    app.dependency_overrides[get_db] = override_get_db
    try:
        after_unpublish_feed = await api_client.get("/api/v1/projects")
    finally:
        app.dependency_overrides.clear()

    assert after_unpublish_feed.status_code == 200
    after_unpublish_ids = [item["id"] for item in after_unpublish_feed.json()["items"]]
    assert str(project.id) not in after_unpublish_ids


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


@pytest.mark.asyncio
async def test_search_projects_combines_keyword_and_taxonomy_filters(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_api_search_combo@ufl.edu", "Owner Search"
    )
    now = datetime.now(timezone.utc)

    matching = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Gator Search Match",
        is_published=True,
    )
    matching.created_at = now
    matching.updated_at = now
    matching.published_at = now

    keyword_only = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Gator Search Wrong Taxonomy",
        is_published=True,
    )
    keyword_only.created_at = now - timedelta(minutes=1)
    keyword_only.updated_at = keyword_only.created_at
    keyword_only.published_at = keyword_only.created_at

    taxonomy_only = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unrelated Title",
        is_published=True,
    )
    taxonomy_only.short_description = "No keyword overlap"
    taxonomy_only.created_at = now - timedelta(minutes=2)
    taxonomy_only.updated_at = taxonomy_only.created_at
    taxonomy_only.published_at = taxonomy_only.created_at

    ai = await _seed_taxonomy_term(db_session, model=Category, name="AI")
    python = await _seed_taxonomy_term(db_session, model=Tag, name="Python")
    javascript = await _seed_taxonomy_term(db_session, model=Tag, name="JavaScript")
    join_now = datetime.now(timezone.utc)

    db_session.add(
        ProjectCategory(
            project_id=matching.id,
            category_id=ai.id,
            position=0,
            created_at=join_now,
        )
    )
    db_session.add(
        ProjectTag(
            project_id=matching.id,
            tag_id=python.id,
            position=0,
            created_at=join_now,
        )
    )
    db_session.add(
        ProjectCategory(
            project_id=keyword_only.id,
            category_id=ai.id,
            position=0,
            created_at=join_now,
        )
    )
    db_session.add(
        ProjectTag(
            project_id=keyword_only.id,
            tag_id=javascript.id,
            position=0,
            created_at=join_now,
        )
    )
    db_session.add(
        ProjectCategory(
            project_id=taxonomy_only.id,
            category_id=ai.id,
            position=0,
            created_at=join_now,
        )
    )
    db_session.add(
        ProjectTag(
            project_id=taxonomy_only.id,
            tag_id=python.id,
            position=0,
            created_at=join_now,
        )
    )
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get(
            "/api/v1/projects/search?q=gator&categories=ai&tags=python&sort=new"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [str(matching.id)]


@pytest.mark.asyncio
async def test_search_projects_rejects_cursor_reuse_across_different_query_context(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_api_search_cursor@ufl.edu", "Owner Search Cursor"
    )
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Cursor Context Alpha One",
        is_published=True,
    )
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Cursor Context Alpha Two",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        page_one = await api_client.get(
            "/api/v1/projects/search?q=alpha&sort=new&limit=1"
        )
        assert page_one.status_code == 200
        next_cursor = page_one.json()["next_cursor"]
        assert next_cursor is not None

        mismatch = await api_client.get(
            f"/api/v1/projects/search?q=different&sort=new&limit=1&cursor={quote(next_cursor)}"
        )
    finally:
        app.dependency_overrides.clear()

    assert mismatch.status_code == 400
    assert mismatch.json()["detail"] == "Cursor does not match requested search"


@pytest.mark.asyncio
async def test_search_projects_accepts_bracketed_taxonomy_alias_params(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_api_search_alias@ufl.edu", "Owner Search Alias"
    )
    matching = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Alias Filter Match",
        is_published=True,
    )
    non_matching = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Alias Filter Non Match",
        is_published=True,
    )

    ai = await _seed_taxonomy_term(db_session, model=Category, name="AI")
    python = await _seed_taxonomy_term(db_session, model=Tag, name="Python")
    rust = await _seed_taxonomy_term(db_session, model=Tag, name="Rust")
    postgres = await _seed_taxonomy_term(db_session, model=TechStack, name="Postgres")
    mysql = await _seed_taxonomy_term(db_session, model=TechStack, name="MySQL")
    join_now = datetime.now(timezone.utc)

    db_session.add(
        ProjectCategory(
            project_id=matching.id,
            category_id=ai.id,
            position=0,
            created_at=join_now,
        )
    )
    db_session.add(
        ProjectTag(
            project_id=matching.id,
            tag_id=python.id,
            position=0,
            created_at=join_now,
        )
    )
    db_session.add(
        ProjectTechStack(
            project_id=matching.id,
            tech_stack_id=postgres.id,
            position=0,
            created_at=join_now,
        )
    )

    db_session.add(
        ProjectCategory(
            project_id=non_matching.id,
            category_id=ai.id,
            position=0,
            created_at=join_now,
        )
    )
    db_session.add(
        ProjectTag(
            project_id=non_matching.id,
            tag_id=rust.id,
            position=0,
            created_at=join_now,
        )
    )
    db_session.add(
        ProjectTechStack(
            project_id=non_matching.id,
            tech_stack_id=mysql.id,
            position=0,
            created_at=join_now,
        )
    )
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get(
            "/api/v1/projects/search?categories[]=ai&tags[]=python&tech_stack[]=postgres"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [str(matching.id)]


@pytest.mark.asyncio
async def test_search_projects_top_default_window_excludes_old_projects(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_api_search_top_window@ufl.edu", "Owner Search Top Window"
    )
    now = datetime.now(timezone.utc)

    recent = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Search Window Recent",
        is_published=True,
    )
    recent.created_at = now - timedelta(days=7)
    recent.updated_at = recent.created_at
    recent.published_at = recent.created_at
    recent.vote_count = 1

    old = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Search Window Old",
        is_published=True,
    )
    old.created_at = now - timedelta(days=140)
    old.updated_at = old.created_at
    old.published_at = old.created_at
    old.vote_count = 500
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get("/api/v1/projects/search?sort=top")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [str(recent.id)]


@pytest.mark.asyncio
async def test_search_projects_cursor_sort_mismatch_returns_400(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_api_search_sort_mismatch@ufl.edu", "Owner Search Sort"
    )
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Search Sort Mismatch A",
        is_published=True,
    )
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Search Sort Mismatch B",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        top_page = await api_client.get("/api/v1/projects/search?sort=top&limit=1")
        assert top_page.status_code == 200
        next_cursor = top_page.json()["next_cursor"]
        assert next_cursor is not None

        mismatch_response = await api_client.get(
            f"/api/v1/projects/search?sort=new&cursor={quote(next_cursor)}"
        )
    finally:
        app.dependency_overrides.clear()

    assert mismatch_response.status_code == 400
    assert mismatch_response.json()["detail"] == "Invalid cursor"


@pytest.mark.asyncio
async def test_search_projects_top_cursor_range_mismatch_returns_400(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_api_search_range_mismatch@ufl.edu", "Owner Search Range"
    )
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Search Range Project A",
        is_published=True,
    )
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Search Range Project B",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        page_one = await api_client.get("/api/v1/projects/search?sort=top&limit=1")
        assert page_one.status_code == 200
        next_cursor = page_one.json()["next_cursor"]
        assert next_cursor is not None

        mismatch_response = await api_client.get(
            "/api/v1/projects/search?sort=top&limit=1"
            f"&published_from=2020-01-01&published_to=2020-12-31&cursor={quote(next_cursor)}"
        )
    finally:
        app.dependency_overrides.clear()

    assert mismatch_response.status_code == 400
    assert (
        mismatch_response.json()["detail"] == "Cursor does not match requested search"
    )


@pytest.mark.asyncio
async def test_search_projects_unknown_taxonomy_terms_behavior(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_api_search_unknown_terms@ufl.edu", "Owner Search Unknown"
    )
    matching = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unknown Terms Match",
        is_published=True,
    )
    non_matching = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unknown Terms Non Match",
        is_published=True,
    )

    python = await _seed_taxonomy_term(db_session, model=Tag, name="Python")
    rust = await _seed_taxonomy_term(db_session, model=Tag, name="Rust")
    join_now = datetime.now(timezone.utc)
    db_session.add(
        ProjectTag(
            project_id=matching.id, tag_id=python.id, position=0, created_at=join_now
        )
    )
    db_session.add(
        ProjectTag(
            project_id=non_matching.id, tag_id=rust.id, position=0, created_at=join_now
        )
    )
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        unknown_only = await api_client.get(
            "/api/v1/projects/search?tags=definitely-not-real&sort=new"
        )
        mixed = await api_client.get(
            "/api/v1/projects/search?tags=python&tags=definitely-not-real&sort=new"
        )
    finally:
        app.dependency_overrides.clear()

    assert unknown_only.status_code == 200
    assert unknown_only.json()["items"] == []

    assert mixed.status_code == 200
    assert [item["id"] for item in mixed.json()["items"]] == [str(matching.id)]


@pytest.mark.asyncio
async def test_search_projects_excludes_soft_deleted_matches(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_api_search_soft_delete@ufl.edu", "Owner Search Soft Delete"
    )
    now = datetime.now(timezone.utc)
    visible = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Soft Delete Search Visible",
        is_published=True,
    )
    hidden = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Soft Delete Search Hidden",
        is_published=True,
    )
    hidden.deleted_at = now
    hidden.vote_count = 999
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get("/api/v1/projects/search?q=soft delete search")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [str(visible.id)]


@pytest.mark.asyncio
async def test_search_projects_whitespace_query_is_treated_as_omitted(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_api_search_whitespace@ufl.edu", "Owner Search Whitespace"
    )
    now = datetime.now(timezone.utc)

    first = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Whitespace Query First",
        is_published=True,
    )
    first.created_at = now - timedelta(minutes=1)
    first.updated_at = first.created_at
    first.published_at = first.created_at

    second = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Whitespace Query Second",
        is_published=True,
    )
    second.created_at = now
    second.updated_at = second.created_at
    second.published_at = second.created_at
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get("/api/v1/projects/search?q=%20%20%20&sort=new")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [str(second.id), str(first.id)]


@pytest.mark.asyncio
async def test_search_projects_viewer_has_voted_anonymous_vs_authenticated(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_api_search_viewer_vote@ufl.edu", "Owner Search Viewer Vote"
    )
    voter = await _seed_user(
        db_session, "voter_api_search_viewer_vote@ufl.edu", "Voter Search Viewer Vote"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Viewer Vote Search Project",
        is_published=True,
    )
    await _seed_vote(db_session, project_id=project.id, user_id=voter.id)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        anonymous = await api_client.get(
            "/api/v1/projects/search?q=viewer vote search project&sort=new"
        )
    finally:
        app.dependency_overrides.clear()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = _override_authed_user(voter)
    try:
        authed = await api_client.get(
            "/api/v1/projects/search?q=viewer vote search project&sort=new"
        )
    finally:
        app.dependency_overrides.clear()

    assert anonymous.status_code == 200
    assert anonymous.json()["items"][0]["viewer_has_voted"] is False

    assert authed.status_code == 200
    assert authed.json()["items"][0]["viewer_has_voted"] is True


@pytest.mark.asyncio
async def test_search_projects_invalid_top_date_range_returns_400(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_api_search_date_range@ufl.edu", "Owner Search Date Range"
    )
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Search Date Range Project",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get(
            "/api/v1/projects/search?sort=top&published_from=2025-03-01&published_to=2025-01-01"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid date range"


@pytest.mark.asyncio
async def test_search_projects_mixed_duplicate_plain_and_alias_params(
    api_client, db_session
):
    owner = await _seed_user(
        db_session,
        "owner_api_search_duplicate_params@ufl.edu",
        "Owner Search Duplicate",
    )
    matching = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Duplicate Param Match",
        is_published=True,
    )
    non_matching = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Duplicate Param Non Match",
        is_published=True,
    )

    python = await _seed_taxonomy_term(db_session, model=Tag, name="Python")
    rust = await _seed_taxonomy_term(db_session, model=Tag, name="Rust")
    join_now = datetime.now(timezone.utc)
    db_session.add(
        ProjectTag(
            project_id=matching.id, tag_id=python.id, position=0, created_at=join_now
        )
    )
    db_session.add(
        ProjectTag(
            project_id=non_matching.id, tag_id=rust.id, position=0, created_at=join_now
        )
    )
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get(
            "/api/v1/projects/search?tags=python&tags[]=PYTHON&sort=new"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [str(matching.id)]


@pytest.mark.asyncio
async def test_search_projects_invalid_limit_returns_422(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_api_search_invalid_limit@ufl.edu", "Owner Search Limit"
    )
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Search Invalid Limit Project",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get("/api/v1/projects/search?limit=0")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"]
    assert any(
        "greater than or equal to 1" in item["msg"] for item in payload["detail"]
    )


@pytest.mark.asyncio
async def test_get_project_members_published_visible_anonymous(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_members_pub@ufl.edu", "Owner Members Pub"
    )
    member = await _seed_user(
        db_session, "member_members_pub@ufl.edu", "Member Members Pub"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Members Published",
        is_published=True,
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=member.id, role="contributor"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get(f"/api/v1/projects/{project.id}/members")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["user_id"] for item in payload] == [str(member.id)]


@pytest.mark.asyncio
async def test_get_project_members_draft_rejects_non_member(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_members_draft@ufl.edu", "Owner Members Draft"
    )
    outsider = await _seed_user(
        db_session, "outsider_members_draft@ufl.edu", "Outsider Members Draft"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Members Draft",
        is_published=False,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = _override_authed_user(
        outsider
    )
    try:
        response = await api_client.get(f"/api/v1/projects/{project.id}/members")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project members access forbidden"


@pytest.mark.asyncio
async def test_add_project_member_owner_only_case_insensitive_email_and_group_flag(
    api_client, db_session
):
    owner = await _seed_user(db_session, "owner_add_member@ufl.edu", "Owner Add Member")
    target = await _seed_user(
        db_session, "target_add_member@ufl.edu", "Target Add Member"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Add Member Project",
        is_published=False,
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )
    project.is_group_project = False
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.post(
            f"/api/v1/projects/{project.id}/members",
            json={"email": "  TARGET_ADD_MEMBER@UFL.EDU ", "role": "maintainer"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["user_id"] == str(target.id)
    assert payload["role"] == "maintainer"

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = project_result.one()
    assert refreshed.is_group_project is True


@pytest.mark.asyncio
async def test_add_project_member_rejects_duplicate_membership(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_add_dup_member@ufl.edu", "Owner Add Dup Member"
    )
    target = await _seed_user(
        db_session, "target_add_dup_member@ufl.edu", "Target Add Dup Member"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Add Duplicate Member Project",
        is_published=False,
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )
    await _seed_member(
        db_session,
        project_id=project.id,
        user_id=target.id,
        role="contributor",
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.post(
            f"/api/v1/projects/{project.id}/members",
            json={"email": "target_add_dup_member@ufl.edu", "role": "contributor"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == "User is already a member of this project"


@pytest.mark.asyncio
async def test_remove_project_member_updates_group_flag(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_remove_member@ufl.edu", "Owner Remove Member"
    )
    target = await _seed_user(
        db_session, "target_remove_member@ufl.edu", "Target Remove Member"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Remove Member Project",
        is_published=False,
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )
    await _seed_member(
        db_session,
        project_id=project.id,
        user_id=target.id,
        role="contributor",
    )
    project.is_group_project = True
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.delete(
            f"/api/v1/projects/{project.id}/members/{target.id}"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = project_result.one()
    assert refreshed.is_group_project is False


@pytest.mark.asyncio
async def test_leave_project_last_owner_returns_409(api_client, db_session):
    owner = await _seed_user(db_session, "owner_leave_last@ufl.edu", "Owner Leave Last")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Last Owner Leave",
        is_published=False,
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.post(f"/api/v1/projects/{project.id}/leave")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == "Last owner cannot leave the project"


@pytest.mark.asyncio
async def test_add_project_member_non_owner_returns_403(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_add_forbidden@ufl.edu", "Owner Add Forbidden"
    )
    non_owner = await _seed_user(
        db_session, "non_owner_add_forbidden@ufl.edu", "Non Owner Add Forbidden"
    )
    target = await _seed_user(
        db_session, "target_add_forbidden@ufl.edu", "Target Add Forbidden"
    )
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="Add Forbidden", is_published=False
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=non_owner.id, role="maintainer"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(non_owner)
    try:
        response = await api_client.post(
            f"/api/v1/projects/{project.id}/members",
            json={"email": target.email, "role": "contributor"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project member management forbidden"


@pytest.mark.asyncio
async def test_add_project_member_missing_target_user_returns_404(
    api_client, db_session
):
    owner = await _seed_user(db_session, "owner_add_404@ufl.edu", "Owner Add 404")
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="Add Missing User", is_published=False
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.post(
            f"/api/v1/projects/{project.id}/members",
            json={"email": "missing_user@ufl.edu", "role": "contributor"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_update_project_member_non_owner_returns_403(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_patch_forbidden@ufl.edu", "Owner Patch Forbidden"
    )
    non_owner = await _seed_user(
        db_session, "non_owner_patch_forbidden@ufl.edu", "Non Owner Patch Forbidden"
    )
    target = await _seed_user(
        db_session, "target_patch_forbidden@ufl.edu", "Target Patch Forbidden"
    )
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="Patch Forbidden", is_published=False
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=non_owner.id, role="maintainer"
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=target.id, role="contributor"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(non_owner)
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}/members/{target.id}",
            json={"role": "maintainer"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project member management forbidden"


@pytest.mark.asyncio
async def test_update_project_member_owner_role_returns_409(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_patch_owner@ufl.edu", "Owner Patch Owner"
    )
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="Patch Owner", is_published=False
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}/members/{owner.id}",
            json={"role": "contributor"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == "Owner role cannot be modified"


@pytest.mark.asyncio
async def test_remove_project_member_non_owner_returns_403(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_remove_forbidden@ufl.edu", "Owner Remove Forbidden"
    )
    non_owner = await _seed_user(
        db_session, "non_owner_remove_forbidden@ufl.edu", "Non Owner Remove Forbidden"
    )
    target = await _seed_user(
        db_session, "target_remove_forbidden@ufl.edu", "Target Remove Forbidden"
    )
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="Remove Forbidden", is_published=False
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=non_owner.id, role="maintainer"
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=target.id, role="contributor"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(non_owner)
    try:
        response = await api_client.delete(
            f"/api/v1/projects/{project.id}/members/{target.id}"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project member management forbidden"


@pytest.mark.asyncio
async def test_remove_project_member_owner_membership_returns_409(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_remove_owner@ufl.edu", "Owner Remove Owner Membership"
    )
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="Remove Owner", is_published=False
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.delete(
            f"/api/v1/projects/{project.id}/members/{owner.id}"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == "Owner membership cannot be removed"


@pytest.mark.asyncio
async def test_leave_project_member_success_updates_group_flag(api_client, db_session):
    owner = await _seed_user(db_session, "owner_leave_ok@ufl.edu", "Owner Leave OK")
    member = await _seed_user(db_session, "member_leave_ok@ufl.edu", "Member Leave OK")
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="Leave OK", is_published=False
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=member.id, role="contributor"
    )
    project.is_group_project = True
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(member)
    try:
        response = await api_client.post(f"/api/v1/projects/{project.id}/leave")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204

    member_result = await db_session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == member.id,
        )
    )
    assert member_result.first() is None

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = project_result.one()
    assert refreshed.is_group_project is False


@pytest.mark.asyncio
async def test_member_write_endpoints_require_authentication(api_client):
    project_id = uuid4()
    user_id = uuid4()
    member_payload = {"email": "target_requires_auth@ufl.edu", "role": "contributor"}

    post_response = await api_client.post(
        f"/api/v1/projects/{project_id}/members",
        json=member_payload,
    )
    patch_response = await api_client.patch(
        f"/api/v1/projects/{project_id}/members/{user_id}",
        json={"role": "maintainer"},
    )
    delete_response = await api_client.delete(
        f"/api/v1/projects/{project_id}/members/{user_id}"
    )
    leave_response = await api_client.post(f"/api/v1/projects/{project_id}/leave")

    assert post_response.status_code == 401
    assert patch_response.status_code == 401
    assert delete_response.status_code == 401
    assert leave_response.status_code == 401
    assert post_response.json()["detail"] == "Not authenticated"
    assert patch_response.json()["detail"] == "Not authenticated"
    assert delete_response.json()["detail"] == "Not authenticated"
    assert leave_response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_project_members_draft_anonymous_returns_404(api_client, db_session):
    owner = await _seed_user(
        db_session, "owner_members_draft_anon@ufl.edu", "Owner Members Draft Anon"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Members Draft Anonymous",
        is_published=False,
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        response = await api_client.get(f"/api/v1/projects/{project.id}/members")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


@pytest.mark.asyncio
async def test_delete_project_owner_returns_204_and_hides_project_everywhere(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, f"owner_api_delete_{uuid4().hex[:8]}@ufl.edu", "Owner Delete API"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Delete Me API Project",
        is_published=True,
    )
    project.github_url = "https://github.com/example/delete-me-api"
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    app.dependency_overrides[get_current_user_optional] = lambda: owner
    try:
        delete_response = await api_client.delete(f"/api/v1/projects/{project.id}")
        detail_response = await api_client.get(f"/api/v1/projects/{project.id}")
        list_response = await api_client.get("/api/v1/projects")
        user_projects_response = await api_client.get(
            f"/api/v1/users/{owner.id}/projects"
        )
        members_response = await api_client.get(
            f"/api/v1/projects/{project.id}/members"
        )
    finally:
        app.dependency_overrides.clear()

    assert delete_response.status_code == 204
    assert detail_response.status_code == 404
    assert list_response.status_code == 200
    assert list_response.json()["items"] == []
    assert user_projects_response.status_code == 200
    assert user_projects_response.json()["items"] == []
    assert members_response.status_code == 404
    assert members_response.json()["detail"] == "Project not found"

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    stored_project = project_result.one()
    assert stored_project.deleted_at is not None


@pytest.mark.asyncio
async def test_delete_project_is_idempotent_for_owner(api_client, db_session):
    owner = await _seed_user(
        db_session, f"owner_api_delete_twice_{uuid4().hex[:8]}@ufl.edu", "Owner Twice"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Delete Twice API Project",
        is_published=True,
    )
    project.github_url = "https://github.com/example/delete-twice-api"
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        first_response = await api_client.delete(f"/api/v1/projects/{project.id}")
        second_response = await api_client.delete(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert first_response.status_code == 204
    assert second_response.status_code == 204


@pytest.mark.asyncio
async def test_delete_project_non_owner_returns_403(api_client, db_session):
    owner = await _seed_user(
        db_session,
        f"owner_api_delete_forbid_{uuid4().hex[:8]}@ufl.edu",
        "Owner Forbid",
    )
    stranger = await _seed_user(
        db_session,
        f"stranger_api_delete_forbid_{uuid4().hex[:8]}@ufl.edu",
        "Stranger Forbid",
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Forbidden Delete API Project",
        is_published=True,
    )
    project.github_url = "https://github.com/example/delete-forbidden-api"
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(stranger)
    try:
        response = await api_client.delete(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project access forbidden"

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    assert project_result.one().deleted_at is None


@pytest.mark.asyncio
async def test_delete_project_missing_returns_404(api_client, db_session):
    owner = await _seed_user(
        db_session,
        f"owner_api_delete_missing_{uuid4().hex[:8]}@ufl.edu",
        "Owner Missing",
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.delete(f"/api/v1/projects/{uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


@pytest.mark.asyncio
async def test_add_vote_soft_deleted_project_returns_404(api_client, db_session):
    owner = await _seed_user(
        db_session, f"owner_api_vote_del_{uuid4().hex[:8]}@ufl.edu", "Owner Vote Del"
    )
    voter = await _seed_user(
        db_session, f"voter_api_vote_del_{uuid4().hex[:8]}@ufl.edu", "Voter Vote Del"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Deleted Vote API Target",
        is_published=True,
    )
    project.github_url = "https://github.com/example/deleted-vote-api"
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        delete_response = await api_client.delete(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert delete_response.status_code == 204

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(voter)
    try:
        vote_response = await api_client.post(f"/api/v1/projects/{project.id}/vote")
    finally:
        app.dependency_overrides.clear()

    assert vote_response.status_code == 404
    assert vote_response.json()["detail"] == "Project not found"


@pytest.mark.asyncio
async def test_remove_vote_soft_deleted_project_returns_404(api_client, db_session):
    owner = await _seed_user(
        db_session,
        f"owner_api_unvote_del_{uuid4().hex[:8]}@ufl.edu",
        "Owner Unvote Del",
    )
    voter = await _seed_user(
        db_session,
        f"voter_api_unvote_del_{uuid4().hex[:8]}@ufl.edu",
        "Voter Unvote Del",
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Deleted Unvote API Target",
        is_published=True,
    )
    project.github_url = "https://github.com/example/deleted-unvote-api"
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(voter)
    try:
        add_vote_response = await api_client.post(f"/api/v1/projects/{project.id}/vote")
    finally:
        app.dependency_overrides.clear()
    assert add_vote_response.status_code == 204

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        delete_response = await api_client.delete(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()
    assert delete_response.status_code == 204

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(voter)
    try:
        remove_vote_response = await api_client.delete(
            f"/api/v1/projects/{project.id}/vote"
        )
    finally:
        app.dependency_overrides.clear()

    assert remove_vote_response.status_code == 404
    assert remove_vote_response.json()["detail"] == "Project not found"

    vote_result = await db_session.exec(
        select(Vote).where(Vote.project_id == project.id, Vote.user_id == voter.id)
    )
    assert vote_result.one_or_none() is not None


@pytest.mark.asyncio
async def test_add_project_member_concurrent_duplicate_requests_one_success_one_conflict(
    api_client, async_engine
):
    now = datetime.now(timezone.utc)
    unique = uuid4().hex
    short_unique = unique[:8]
    owner_email = f"owner_race_{unique}@ufl.edu"
    target_email = f"target_race_{unique}@ufl.edu"
    session_factory = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        class_=SQLModelAsyncSession,
    )

    async with session_factory() as setup_session:
        owner = User(
            email=owner_email,
            username=f"owner_{short_unique}",
            password_hash="integration-password-hash",
            full_name="Owner Race",
            created_at=now,
            updated_at=now,
        )
        target = User(
            email=target_email,
            username=f"target_{short_unique}",
            password_hash="integration-password-hash",
            full_name="Target Race",
            created_at=now,
            updated_at=now,
        )
        setup_session.add(owner)
        setup_session.add(target)
        await setup_session.flush()

        project = Project(
            created_by_id=owner.id,
            title="Concurrent Member Add",
            slug="concurrent-member-add",
            short_description="Concurrent add coverage",
            vote_count=0,
            is_group_project=False,
            is_published=False,
            published_at=None,
            created_at=now,
            updated_at=now,
        )
        setup_session.add(project)
        await setup_session.flush()
        setup_session.add(
            ProjectMember(
                project_id=project.id,
                user_id=owner.id,
                role="owner",
                added_at=now,
            )
        )
        await setup_session.commit()
        project_id = project.id
        owner_id = owner.id
        target_id = target.id

    async def override_get_db():
        async with session_factory() as session:
            yield session

    class CurrentUser:
        id = owner_id
        email = owner_email

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: CurrentUser()
    project_member_cols = getattr(ProjectMember, "__table__").c
    project_cols = getattr(Project, "__table__").c
    user_cols = getattr(User, "__table__").c
    try:
        try:
            first_response, second_response = await asyncio.gather(
                api_client.post(
                    f"/api/v1/projects/{project_id}/members",
                    json={"email": target_email, "role": "contributor"},
                ),
                api_client.post(
                    f"/api/v1/projects/{project_id}/members",
                    json={"email": target_email, "role": "contributor"},
                ),
            )
        finally:
            app.dependency_overrides.clear()

        status_codes = sorted([first_response.status_code, second_response.status_code])
        assert status_codes == [201, 409]
    finally:
        async with session_factory() as cleanup_session:
            await cleanup_session.exec(
                delete(ProjectMember).where(
                    project_member_cols.project_id == project_id
                )
            )
            await cleanup_session.exec(
                delete(Project).where(project_cols.id == project_id)
            )
            await cleanup_session.exec(
                delete(User).where(user_cols.id.in_([owner_id, target_id]))
            )
            await cleanup_session.commit()


@pytest.mark.asyncio
async def test_update_project_member_role_does_not_change_group_flag(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_patch_group_stable@ufl.edu", "Owner Patch Group Stable"
    )
    member = await _seed_user(
        db_session, "member_patch_group_stable@ufl.edu", "Member Patch Group Stable"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Role Patch Group Stability",
        is_published=False,
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=member.id, role="contributor"
    )
    project.is_group_project = True
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        response = await api_client.patch(
            f"/api/v1/projects/{project.id}/members/{member.id}",
            json={"role": "maintainer"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["role"] == "maintainer"

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = project_result.one()
    assert refreshed.is_group_project is True


@pytest.mark.asyncio
async def test_get_project_members_smoke_with_large_member_count(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_members_smoke@ufl.edu", "Owner Members Smoke"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Members Smoke Test",
        is_published=True,
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )

    total_members = 160
    for idx in range(total_members):
        user = await _seed_user(
            db_session,
            f"members_smoke_{idx}_{uuid4().hex[:8]}@ufl.edu",
            f"Members Smoke {idx}",
        )
        await _seed_member(
            db_session,
            project_id=project.id,
            user_id=user.id,
            role="contributor",
        )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        start = perf_counter()
        response = await api_client.get(f"/api/v1/projects/{project.id}/members")
        elapsed = perf_counter() - start
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == total_members + 1
    # Smoke bound to catch obvious regressions, not strict benchmarking.
    assert elapsed < 2.5


@pytest.mark.asyncio
async def test_add_project_vote_idempotent_and_count_consistent(api_client, db_session):
    owner = await _seed_user(db_session, "owner_vote_add@ufl.edu", "Owner Vote Add")
    voter = await _seed_user(db_session, "voter_vote_add@ufl.edu", "Voter Vote Add")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Vote Add Target",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(voter)
    try:
        first = await api_client.post(f"/api/v1/projects/{project.id}/vote")
        second = await api_client.post(f"/api/v1/projects/{project.id}/vote")
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 204
    assert second.status_code == 204

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = project_result.one()
    assert refreshed.vote_count == 1

    votes_result = await db_session.exec(
        select(Vote).where(Vote.project_id == project.id, Vote.user_id == voter.id)
    )
    assert len(votes_result.all()) == 1


@pytest.mark.asyncio
async def test_remove_project_vote_idempotent_and_count_consistent(
    api_client, db_session
):
    owner = await _seed_user(
        db_session, "owner_vote_remove@ufl.edu", "Owner Vote Remove"
    )
    voter = await _seed_user(
        db_session, "voter_vote_remove@ufl.edu", "Voter Vote Remove"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Vote Remove Target",
        is_published=True,
    )
    project.vote_count = 1
    await _seed_vote(db_session, project_id=project.id, user_id=voter.id)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(voter)
    try:
        first = await api_client.delete(f"/api/v1/projects/{project.id}/vote")
        second = await api_client.delete(f"/api/v1/projects/{project.id}/vote")
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 204
    assert second.status_code == 204

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = project_result.one()
    assert refreshed.vote_count == 0

    votes_result = await db_session.exec(
        select(Vote).where(Vote.project_id == project.id, Vote.user_id == voter.id)
    )
    assert len(votes_result.all()) == 0


@pytest.mark.asyncio
async def test_vote_endpoints_draft_project_returns_404(api_client, db_session):
    owner = await _seed_user(db_session, "owner_vote_draft@ufl.edu", "Owner Vote Draft")
    voter = await _seed_user(db_session, "voter_vote_draft@ufl.edu", "Voter Vote Draft")
    draft_project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Draft Vote Target",
        is_published=False,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(voter)
    try:
        add_response = await api_client.post(
            f"/api/v1/projects/{draft_project.id}/vote"
        )
        remove_response = await api_client.delete(
            f"/api/v1/projects/{draft_project.id}/vote"
        )
    finally:
        app.dependency_overrides.clear()

    assert add_response.status_code == 404
    assert remove_response.status_code == 404
    assert add_response.json()["detail"] == "Project not found"
    assert remove_response.json()["detail"] == "Project not found"


@pytest.mark.asyncio
async def test_vote_endpoints_and_my_votes_require_auth_integration(
    api_client, db_session
):
    owner = await _seed_user(db_session, "owner_vote_auth@ufl.edu", "Owner Vote Auth")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Vote Auth Target",
        is_published=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        add_response = await api_client.post(f"/api/v1/projects/{project.id}/vote")
        remove_response = await api_client.delete(f"/api/v1/projects/{project.id}/vote")
        my_votes_response = await api_client.get("/api/v1/users/me/votes")
    finally:
        app.dependency_overrides.clear()

    assert add_response.status_code == 401
    assert remove_response.status_code == 401
    assert my_votes_response.status_code == 401
    assert add_response.json()["detail"] == "Not authenticated"
    assert remove_response.json()["detail"] == "Not authenticated"
    assert my_votes_response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_my_votes_contract_order_cursor_and_filtering(api_client, db_session):
    owner = await _seed_user(db_session, "owner_my_votes@ufl.edu", "Owner My Votes")
    voter = await _seed_user(db_session, "voter_my_votes@ufl.edu", "Voter My Votes")
    now = datetime.now(timezone.utc)

    oldest = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Oldest Voted Project",
        is_published=True,
    )
    middle = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Middle Voted Project",
        is_published=True,
    )
    newest = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Newest Voted Project",
        is_published=True,
    )
    draft = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Draft Voted Project",
        is_published=False,
    )

    await _seed_vote(
        db_session,
        project_id=oldest.id,
        user_id=voter.id,
        created_at=now - timedelta(minutes=3),
    )
    await _seed_vote(
        db_session,
        project_id=middle.id,
        user_id=voter.id,
        created_at=now - timedelta(minutes=2),
    )
    await _seed_vote(
        db_session,
        project_id=newest.id,
        user_id=voter.id,
        created_at=now - timedelta(minutes=1),
    )
    # Simulate stale data edge case: voted draft should still be excluded.
    await _seed_vote(
        db_session,
        project_id=draft.id,
        user_id=voter.id,
        created_at=now,
    )
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(voter)
    try:
        page_one = await api_client.get("/api/v1/users/me/votes?limit=2")
        assert page_one.status_code == 200
        payload_one = page_one.json()
        assert [item["id"] for item in payload_one["items"]] == [
            str(newest.id),
            str(middle.id),
        ]
        assert [item["viewer_has_voted"] for item in payload_one["items"]] == [
            True,
            True,
        ]
        assert payload_one["next_cursor"] is not None

        page_two = await api_client.get(
            f"/api/v1/users/me/votes?limit=2&cursor={payload_one['next_cursor']}"
        )
        assert page_two.status_code == 200
        payload_two = page_two.json()
    finally:
        app.dependency_overrides.clear()

    assert [item["id"] for item in payload_two["items"]] == [str(oldest.id)]
    assert [item["viewer_has_voted"] for item in payload_two["items"]] == [True]
    assert payload_two["next_cursor"] is None
    combined_ids = [item["id"] for item in payload_one["items"]] + [
        item["id"] for item in payload_two["items"]
    ]
    assert str(draft.id) not in combined_ids


@pytest.mark.asyncio
async def test_viewer_has_voted_project_endpoints_authenticated_vs_anonymous(
    api_client, db_session
):
    owner = await _seed_user(db_session, "owner_viewer_state@ufl.edu", "Owner Viewer")
    viewer = await _seed_user(db_session, "viewer_viewer_state@ufl.edu", "Viewer State")
    voted_project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Viewer Voted Project",
        is_published=True,
    )
    unvoted_project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Viewer Unvoted Project",
        is_published=True,
    )
    await _seed_vote(db_session, project_id=voted_project.id, user_id=viewer.id)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = _override_authed_user(viewer)
    try:
        list_response = await api_client.get("/api/v1/projects?sort=new&limit=10")
        voted_detail = await api_client.get(f"/api/v1/projects/{voted_project.id}")
        unvoted_detail = await api_client.get(f"/api/v1/projects/{unvoted_project.id}")
        user_projects = await api_client.get(
            f"/api/v1/users/{owner.id}/projects?sort=new&limit=10"
        )
    finally:
        app.dependency_overrides.clear()

    assert list_response.status_code == 200
    list_items = {item["id"]: item for item in list_response.json()["items"]}
    assert list_items[str(voted_project.id)]["viewer_has_voted"] is True
    assert list_items[str(unvoted_project.id)]["viewer_has_voted"] is False

    assert voted_detail.status_code == 200
    assert voted_detail.json()["viewer_has_voted"] is True
    assert unvoted_detail.status_code == 200
    assert unvoted_detail.json()["viewer_has_voted"] is False

    assert user_projects.status_code == 200
    user_items = {item["id"]: item for item in user_projects.json()["items"]}
    assert user_items[str(voted_project.id)]["viewer_has_voted"] is True
    assert user_items[str(unvoted_project.id)]["viewer_has_voted"] is False

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        anonymous_list = await api_client.get("/api/v1/projects?sort=new&limit=10")
        anonymous_detail = await api_client.get(f"/api/v1/projects/{voted_project.id}")
        anonymous_user_projects = await api_client.get(
            f"/api/v1/users/{owner.id}/projects?sort=new&limit=10"
        )
    finally:
        app.dependency_overrides.clear()

    assert anonymous_list.status_code == 200
    anonymous_list_items = {item["id"]: item for item in anonymous_list.json()["items"]}
    assert anonymous_list_items[str(voted_project.id)]["viewer_has_voted"] is False
    assert anonymous_list_items[str(unvoted_project.id)]["viewer_has_voted"] is False

    assert anonymous_detail.status_code == 200
    assert anonymous_detail.json()["viewer_has_voted"] is False

    assert anonymous_user_projects.status_code == 200
    anonymous_user_items = {
        item["id"]: item for item in anonymous_user_projects.json()["items"]
    }
    assert anonymous_user_items[str(voted_project.id)]["viewer_has_voted"] is False
    assert anonymous_user_items[str(unvoted_project.id)]["viewer_has_voted"] is False


@pytest.mark.asyncio
async def test_team_size_in_detail_feed_user_projects_and_my_votes(
    api_client, db_session
):
    owner = await _seed_user(db_session, "owner_team_size@ufl.edu", "Owner Team Size")
    viewer = await _seed_user(
        db_session, "viewer_team_size@ufl.edu", "Viewer Team Size"
    )
    teammate = await _seed_user(
        db_session, "teammate_team_size@ufl.edu", "Teammate Team Size"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Team Size Project",
        is_published=True,
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )
    await _seed_member(
        db_session,
        project_id=project.id,
        user_id=teammate.id,
        role="contributor",
    )
    await _seed_vote(db_session, project_id=project.id, user_id=viewer.id)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = _override_authed_user(viewer)
    app.dependency_overrides[get_current_user] = _override_authed_user(viewer)
    try:
        detail_response = await api_client.get(f"/api/v1/projects/{project.id}")
        list_response = await api_client.get("/api/v1/projects?sort=new&limit=10")
        user_projects_response = await api_client.get(
            f"/api/v1/users/{owner.id}/projects?sort=new&limit=10"
        )
        my_votes_response = await api_client.get("/api/v1/users/me/votes?limit=10")
    finally:
        app.dependency_overrides.clear()

    assert detail_response.status_code == 200
    assert list_response.status_code == 200
    assert user_projects_response.status_code == 200
    assert my_votes_response.status_code == 200

    assert detail_response.json()["team_size"] == 2
    list_items = {item["id"]: item for item in list_response.json()["items"]}
    assert list_items[str(project.id)]["team_size"] == 2
    user_items = {item["id"]: item for item in user_projects_response.json()["items"]}
    assert user_items[str(project.id)]["team_size"] == 2
    vote_items = {item["id"]: item for item in my_votes_response.json()["items"]}
    assert vote_items[str(project.id)]["team_size"] == 2


@pytest.mark.asyncio
async def test_team_size_updates_after_add_and_remove_member(api_client, db_session):
    owner = await _seed_user(db_session, "owner_team_flow@ufl.edu", "Owner Team Flow")
    teammate = await _seed_user(
        db_session, "teammate_team_flow@ufl.edu", "Teammate Team Flow"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Team Flow Project",
        is_published=True,
    )
    await _seed_member(
        db_session, project_id=project.id, user_id=owner.id, role="owner"
    )
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    app.dependency_overrides[get_current_user_optional] = _override_authed_user(owner)
    try:
        before = await api_client.get(f"/api/v1/projects/{project.id}")
        add_response = await api_client.post(
            f"/api/v1/projects/{project.id}/members",
            json={"email": teammate.email, "role": "contributor"},
        )
        after_add = await api_client.get(f"/api/v1/projects/{project.id}")
        remove_response = await api_client.delete(
            f"/api/v1/projects/{project.id}/members/{teammate.id}"
        )
        after_remove = await api_client.get(f"/api/v1/projects/{project.id}")
    finally:
        app.dependency_overrides.clear()

    assert before.status_code == 200
    assert add_response.status_code == 201
    assert after_add.status_code == 200
    assert remove_response.status_code == 204
    assert after_remove.status_code == 200

    assert before.json()["team_size"] == 1
    assert after_add.json()["team_size"] == 2
    assert after_remove.json()["team_size"] == 1


@pytest.mark.asyncio
async def test_add_project_vote_concurrent_requests_one_effective_vote(
    api_client, async_engine
):
    now = datetime.now(timezone.utc)
    unique = uuid4().hex[:8]
    owner_email = f"owner_vote_concurrent_{unique}@ufl.edu"
    voter_email = f"voter_vote_concurrent_{unique}@ufl.edu"
    session_factory = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        class_=SQLModelAsyncSession,
    )

    async with session_factory() as setup_session:
        owner = User(
            email=owner_email,
            username=f"owner_{unique}",
            password_hash="integration-password-hash",
            full_name="Owner Vote Concurrent",
            created_at=now,
            updated_at=now,
        )
        voter = User(
            email=voter_email,
            username=f"voter_{unique}",
            password_hash="integration-password-hash",
            full_name="Voter Vote Concurrent",
            created_at=now,
            updated_at=now,
        )
        setup_session.add(owner)
        setup_session.add(voter)
        await setup_session.flush()

        project = Project(
            created_by_id=owner.id,
            title="Concurrent Vote API",
            slug="concurrent-vote-api",
            short_description="Concurrent vote endpoint coverage",
            vote_count=0,
            is_group_project=False,
            is_published=True,
            published_at=now,
            created_at=now,
            updated_at=now,
        )
        setup_session.add(project)
        await setup_session.commit()
        project_id = project.id
        owner_id = owner.id
        voter_id = voter.id

    async def override_get_db():
        async with session_factory() as session:
            yield session

    class CurrentUser:
        id = voter_id
        email = voter_email

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: CurrentUser()
    project_cols = getattr(Project, "__table__").c
    vote_cols = getattr(Vote, "__table__").c
    user_cols = getattr(User, "__table__").c
    try:
        try:
            first_response, second_response = await asyncio.gather(
                api_client.post(f"/api/v1/projects/{project_id}/vote"),
                api_client.post(f"/api/v1/projects/{project_id}/vote"),
            )
        finally:
            app.dependency_overrides.clear()

        assert first_response.status_code == 204
        assert second_response.status_code == 204

        async with session_factory() as verify_session:
            project_result = await verify_session.exec(
                select(Project).where(project_cols.id == project_id)
            )
            refreshed = project_result.one()
            assert refreshed.vote_count == 1

            votes_result = await verify_session.exec(
                select(Vote).where(
                    vote_cols.project_id == project_id,
                    vote_cols.user_id == voter_id,
                )
            )
            assert len(votes_result.all()) == 1
    finally:
        async with session_factory() as cleanup_session:
            await cleanup_session.exec(
                delete(Vote).where(vote_cols.project_id == project_id)
            )
            await cleanup_session.exec(
                delete(Project).where(project_cols.id == project_id)
            )
            await cleanup_session.exec(
                delete(User).where(user_cols.id.in_([owner_id, voter_id]))
            )
            await cleanup_session.commit()


@pytest.mark.asyncio
async def test_create_project_with_taxonomy_create_on_miss_and_canonical_reuse(
    api_client, db_session
):
    creator = await _seed_user(
        db_session, "creator_taxonomy_create@ufl.edu", "Creator Taxonomy Create"
    )
    existing_category = Category(
        name="React",
        normalized_name="react",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(existing_category)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(
                categories=[" react ", "AI"],
                tags=["API"],
                tech_stack=["FastAPI"],
            ),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert [term["name"] for term in payload["categories"]] == ["React", "AI"]
    assert [term["name"] for term in payload["tags"]] == ["API"]
    assert [term["name"] for term in payload["tech_stack"]] == ["FastAPI"]

    project_id = payload["id"]
    project_category_cols = getattr(ProjectCategory, "__table__").c
    project_tag_cols = getattr(ProjectTag, "__table__").c
    project_tech_stack_cols = getattr(ProjectTechStack, "__table__").c
    category_cols = getattr(Category, "__table__").c
    tag_cols = getattr(Tag, "__table__").c
    tech_stack_cols = getattr(TechStack, "__table__").c

    categories_result = await db_session.exec(
        select(ProjectCategory, Category)
        .join(Category, category_cols.id == project_category_cols.category_id)
        .where(project_category_cols.project_id == project_id)
        .order_by(project_category_cols.position.asc())
    )
    category_rows = categories_result.all()
    assert [category.name for _, category in category_rows] == ["React", "AI"]

    tags_result = await db_session.exec(
        select(ProjectTag, Tag)
        .join(Tag, tag_cols.id == project_tag_cols.tag_id)
        .where(project_tag_cols.project_id == project_id)
        .order_by(project_tag_cols.position.asc())
    )
    tag_rows = tags_result.all()
    assert [tag.name for _, tag in tag_rows] == ["API"]

    tech_stack_result = await db_session.exec(
        select(ProjectTechStack, TechStack)
        .join(
            TechStack,
            tech_stack_cols.id == project_tech_stack_cols.tech_stack_id,
        )
        .where(project_tech_stack_cols.project_id == project_id)
        .order_by(project_tech_stack_cols.position.asc())
    )
    tech_stack_rows = tech_stack_result.all()
    assert [tech_stack.name for _, tech_stack in tech_stack_rows] == ["FastAPI"]


@pytest.mark.asyncio
async def test_update_project_taxonomy_omitted_replace_and_clear_semantics(
    api_client, db_session
):
    creator = await _seed_user(
        db_session, "creator_taxonomy_update@ufl.edu", "Creator Taxonomy Update"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        create_response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(
                categories=["Web", "AI"],
                tags=["Backend"],
                tech_stack=["FastAPI"],
            ),
        )
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        replace_response = await api_client.patch(
            f"/api/v1/projects/{project_id}",
            json={"categories": ["ML"], "demo_url": "https://example.com/demo"},
        )
    finally:
        app.dependency_overrides.clear()

    assert replace_response.status_code == 200
    replaced = replace_response.json()
    assert [term["name"] for term in replaced["categories"]] == ["ML"]
    assert [term["name"] for term in replaced["tags"]] == ["Backend"]
    assert [term["name"] for term in replaced["tech_stack"]] == ["FastAPI"]

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        clear_response = await api_client.patch(
            f"/api/v1/projects/{project_id}",
            json={"tags": [], "demo_url": "https://example.com/demo2"},
        )
    finally:
        app.dependency_overrides.clear()

    assert clear_response.status_code == 200
    cleared = clear_response.json()
    assert [term["name"] for term in cleared["categories"]] == ["ML"]
    assert cleared["tags"] == []
    assert [term["name"] for term in cleared["tech_stack"]] == ["FastAPI"]


@pytest.mark.asyncio
async def test_create_project_rejects_duplicate_taxonomy_terms(api_client, db_session):
    creator = await _seed_user(
        db_session, "creator_taxonomy_dup@ufl.edu", "Creator Taxonomy Dup"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(categories=["AI", " ai "]),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_project_rejects_taxonomy_limit_exceeded(api_client, db_session):
    creator = await _seed_user(
        db_session, "creator_taxonomy_limit@ufl.edu", "Creator Taxonomy Limit"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(
                categories=["A1", "A2", "A3", "A4"],
            ),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_project_taxonomy_rewrites_position_order_on_replace(
    api_client, db_session
):
    creator = await _seed_user(
        db_session, "creator_taxonomy_order@ufl.edu", "Creator Taxonomy Order"
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        create_response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(categories=["Aaa", "Bbb", "Ccc"]),
        )
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(creator)
    try:
        update_response = await api_client.patch(
            f"/api/v1/projects/{project_id}",
            json={
                "categories": ["Ccc", "Aaa"],
                "demo_url": "https://example.com/reorder",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert update_response.status_code == 200
    updated_payload = update_response.json()
    assert [term["name"] for term in updated_payload["categories"]] == ["Ccc", "Aaa"]

    project_category_cols = getattr(ProjectCategory, "__table__").c
    category_cols = getattr(Category, "__table__").c
    rows_result = await db_session.exec(
        select(ProjectCategory, Category)
        .join(Category, category_cols.id == project_category_cols.category_id)
        .where(project_category_cols.project_id == project_id)
        .order_by(project_category_cols.position.asc())
    )
    rows = rows_result.all()
    assert [row.position for row, _ in rows] == [0, 1]
    assert [category.name for _, category in rows] == ["Ccc", "Aaa"]


@pytest.mark.asyncio
async def test_list_endpoints_include_taxonomy_payloads(api_client, db_session):
    owner = await _seed_user(
        db_session, "creator_taxonomy_list@ufl.edu", "Creator Taxonomy List"
    )
    created_project_id: str | None = None
    created_project_slug: str | None = None

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        create_response = await api_client.post(
            "/api/v1/projects",
            json=_create_project_payload(
                categories=["Zoology", "AI"],
                tags=["Backend", "API"],
                tech_stack=["React", "Bun"],
            ),
        )
        assert create_response.status_code == 201
        created_project_id = create_response.json()["id"]
        created_project_slug = create_response.json()["slug"]

        publish_response = await api_client.post(
            f"/api/v1/projects/{created_project_id}/publish"
        )
        assert publish_response.status_code == 200

        vote_response = await api_client.post(
            f"/api/v1/projects/{created_project_id}/vote"
        )
        assert vote_response.status_code == 204
    finally:
        app.dependency_overrides.clear()

    assert created_project_id is not None
    assert created_project_slug is not None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = _override_authed_user(owner)
    app.dependency_overrides[get_current_user] = _override_authed_user(owner)
    try:
        detail_response = await api_client.get(f"/api/v1/projects/{created_project_id}")
        detail_by_slug_response = await api_client.get(
            f"/api/v1/projects/slug/{created_project_slug}"
        )
        feed_response = await api_client.get("/api/v1/projects")
        user_projects_response = await api_client.get(
            f"/api/v1/users/{owner.id}/projects"
        )
        username_projects_response = await api_client.get(
            f"/api/v1/users/by-username/{owner.username}/projects"
        )
        my_votes_response = await api_client.get("/api/v1/users/me/votes")
    finally:
        app.dependency_overrides.clear()

    assert detail_response.status_code == 200
    assert detail_by_slug_response.status_code == 200
    assert feed_response.status_code == 200
    assert user_projects_response.status_code == 200
    assert username_projects_response.status_code == 200
    assert my_votes_response.status_code == 200

    expected_categories = ["Zoology", "AI"]
    expected_tags = ["Backend", "API"]
    expected_tech_stack = ["React", "Bun"]

    detail_payload = detail_response.json()
    assert [
        term["name"] for term in detail_payload["categories"]
    ] == expected_categories
    assert [term["name"] for term in detail_payload["tags"]] == expected_tags
    assert [
        term["name"] for term in detail_payload["tech_stack"]
    ] == expected_tech_stack

    detail_by_slug_payload = detail_by_slug_response.json()
    assert [
        term["name"] for term in detail_by_slug_payload["categories"]
    ] == expected_categories
    assert [term["name"] for term in detail_by_slug_payload["tags"]] == expected_tags
    assert [
        term["name"] for term in detail_by_slug_payload["tech_stack"]
    ] == expected_tech_stack

    feed_items = feed_response.json()["items"]
    assert len(feed_items) >= 1
    feed_item = next(item for item in feed_items if item["id"] == created_project_id)
    assert [term["name"] for term in feed_item["categories"]] == expected_categories
    assert [term["name"] for term in feed_item["tags"]] == expected_tags
    assert [term["name"] for term in feed_item["tech_stack"]] == expected_tech_stack

    user_items = user_projects_response.json()["items"]
    assert len(user_items) >= 1
    user_item = next(item for item in user_items if item["id"] == created_project_id)
    assert [term["name"] for term in user_item["categories"]] == expected_categories
    assert [term["name"] for term in user_item["tags"]] == expected_tags
    assert [term["name"] for term in user_item["tech_stack"]] == expected_tech_stack

    username_items = username_projects_response.json()["items"]
    assert len(username_items) >= 1
    username_item = next(
        item for item in username_items if item["id"] == created_project_id
    )
    assert [term["name"] for term in username_item["categories"]] == expected_categories
    assert [term["name"] for term in username_item["tags"]] == expected_tags
    assert [term["name"] for term in username_item["tech_stack"]] == expected_tech_stack

    voted_items = my_votes_response.json()["items"]
    assert len(voted_items) >= 1
    voted_item = next(item for item in voted_items if item["id"] == created_project_id)
    assert [term["name"] for term in voted_item["categories"]] == expected_categories
    assert [term["name"] for term in voted_item["tags"]] == expected_tags
    assert [term["name"] for term in voted_item["tech_stack"]] == expected_tech_stack


@pytest.mark.asyncio
async def test_create_project_taxonomy_create_on_miss_concurrency_converges_one_term(
    api_client, async_engine
):
    now = datetime.now(timezone.utc)
    unique = uuid4().hex[:8]
    owner_email = f"owner_taxonomy_create_race_{unique}@ufl.edu"
    category_term = f"GraphQL {unique}"
    normalized_term = f"graphql {unique}"
    session_factory = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        class_=SQLModelAsyncSession,
    )

    async with session_factory() as setup_session:
        owner = User(
            email=owner_email,
            username=f"owner_{unique}",
            password_hash="integration-password-hash",
            full_name="Owner Taxonomy Create Race",
            created_at=now,
            updated_at=now,
        )
        setup_session.add(owner)
        await setup_session.commit()
        owner_id = owner.id

    async def override_get_db():
        async with session_factory() as session:
            yield session

    class CurrentUser:
        id = owner_id
        email = owner_email

    category_cols = getattr(Category, "__table__").c
    project_category_cols = getattr(ProjectCategory, "__table__").c
    project_member_cols = getattr(ProjectMember, "__table__").c
    project_cols = getattr(Project, "__table__").c
    user_cols = getattr(User, "__table__").c
    created_project_ids: list[str] = []

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: CurrentUser()
    try:
        try:
            first_response, second_response = await asyncio.gather(
                api_client.post(
                    "/api/v1/projects",
                    json=_create_project_payload(
                        title=f"Create Race A {unique}",
                        categories=[category_term],
                    ),
                ),
                api_client.post(
                    "/api/v1/projects",
                    json=_create_project_payload(
                        title=f"Create Race B {unique}",
                        categories=[f"  {category_term.lower()}  "],
                    ),
                ),
            )
        finally:
            app.dependency_overrides.clear()

        assert first_response.status_code == 201
        assert second_response.status_code == 201
        created_project_ids = [
            first_response.json()["id"],
            second_response.json()["id"],
        ]

        async with session_factory() as verify_session:
            categories_result = await verify_session.exec(
                select(Category).where(category_cols.normalized_name == normalized_term)
            )
            categories = categories_result.all()
            assert len(categories) == 1
            category_id = categories[0].id

            assignment_result = await verify_session.exec(
                select(ProjectCategory).where(
                    project_category_cols.project_id.in_(created_project_ids)
                )
            )
            assignments = assignment_result.all()
            assert len(assignments) == 2
            assert {row.category_id for row in assignments} == {category_id}
    finally:
        async with session_factory() as cleanup_session:
            if created_project_ids:
                await cleanup_session.exec(
                    delete(ProjectCategory).where(
                        project_category_cols.project_id.in_(created_project_ids)
                    )
                )
                await cleanup_session.exec(
                    delete(ProjectMember).where(
                        project_member_cols.project_id.in_(created_project_ids)
                    )
                )
                await cleanup_session.exec(
                    delete(Project).where(project_cols.id.in_(created_project_ids))
                )
            await cleanup_session.exec(
                delete(Category).where(category_cols.normalized_name == normalized_term)
            )
            await cleanup_session.exec(delete(User).where(user_cols.id == owner_id))
            await cleanup_session.commit()


@pytest.mark.asyncio
async def test_update_project_taxonomy_create_on_miss_concurrency_converges_one_term(
    api_client, async_engine
):
    now = datetime.now(timezone.utc)
    unique = uuid4().hex[:8]
    owner_email = f"owner_taxonomy_update_race_{unique}@ufl.edu"
    category_term = f"Supabase {unique}"
    normalized_term = f"supabase {unique}"
    session_factory = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        class_=SQLModelAsyncSession,
    )

    async with session_factory() as setup_session:
        owner = User(
            email=owner_email,
            username=f"owner_{unique}",
            password_hash="integration-password-hash",
            full_name="Owner Taxonomy Update Race",
            created_at=now,
            updated_at=now,
        )
        setup_session.add(owner)
        await setup_session.flush()
        first_project = Project(
            created_by_id=owner.id,
            title=f"Update Race A {unique}",
            slug=f"update-race-a-{unique}",
            short_description="Update race A",
            vote_count=0,
            is_group_project=False,
            is_published=False,
            published_at=None,
            created_at=now,
            updated_at=now,
            github_url=f"https://github.com/example/update-race-a-{unique}",
        )
        second_project = Project(
            created_by_id=owner.id,
            title=f"Update Race B {unique}",
            slug=f"update-race-b-{unique}",
            short_description="Update race B",
            vote_count=0,
            is_group_project=False,
            is_published=False,
            published_at=None,
            created_at=now,
            updated_at=now,
            github_url=f"https://github.com/example/update-race-b-{unique}",
        )
        setup_session.add(first_project)
        setup_session.add(second_project)
        await setup_session.commit()
        owner_id = owner.id
        first_project_id = first_project.id
        second_project_id = second_project.id

    async def override_get_db():
        async with session_factory() as session:
            yield session

    class CurrentUser:
        id = owner_id
        email = owner_email

    category_cols = getattr(Category, "__table__").c
    project_category_cols = getattr(ProjectCategory, "__table__").c
    project_cols = getattr(Project, "__table__").c
    user_cols = getattr(User, "__table__").c
    try:
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: CurrentUser()
        try:
            first_response, second_response = await asyncio.gather(
                api_client.patch(
                    f"/api/v1/projects/{first_project_id}",
                    json={
                        "categories": [category_term],
                        "demo_url": f"https://example.com/update-race-a-{unique}",
                    },
                ),
                api_client.patch(
                    f"/api/v1/projects/{second_project_id}",
                    json={
                        "categories": [f"  {category_term.lower()}  "],
                        "demo_url": f"https://example.com/update-race-b-{unique}",
                    },
                ),
            )
        finally:
            app.dependency_overrides.clear()

        assert first_response.status_code == 200
        assert second_response.status_code == 200

        async with session_factory() as verify_session:
            categories_result = await verify_session.exec(
                select(Category).where(category_cols.normalized_name == normalized_term)
            )
            categories = categories_result.all()
            assert len(categories) == 1
            category_id = categories[0].id

            assignment_result = await verify_session.exec(
                select(ProjectCategory).where(
                    project_category_cols.project_id.in_(
                        [first_project_id, second_project_id]
                    )
                )
            )
            assignments = assignment_result.all()
            assert len(assignments) == 2
            assert {row.category_id for row in assignments} == {category_id}
    finally:
        async with session_factory() as cleanup_session:
            await cleanup_session.exec(
                delete(ProjectCategory).where(
                    project_category_cols.project_id.in_(
                        [first_project_id, second_project_id]
                    )
                )
            )
            await cleanup_session.exec(
                delete(Project).where(
                    project_cols.id.in_([first_project_id, second_project_id])
                )
            )
            await cleanup_session.exec(
                delete(Category).where(category_cols.normalized_name == normalized_term)
            )
            await cleanup_session.exec(delete(User).where(user_cols.id == owner_id))
            await cleanup_session.commit()


@pytest.mark.asyncio
async def test_concurrent_create_normalization_variants_share_single_taxonomy_term(
    api_client, async_engine
):
    now = datetime.now(timezone.utc)
    unique = uuid4().hex[:8]
    owner_email = f"owner_taxonomy_norm_race_{unique}@ufl.edu"
    normalized_term = f"ai {unique}"
    raw_variant_a = f"AI {unique}"
    raw_variant_b = f"  ai {unique}  "
    session_factory = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        class_=SQLModelAsyncSession,
    )

    async with session_factory() as setup_session:
        owner = User(
            email=owner_email,
            username=f"owner_{unique}",
            password_hash="integration-password-hash",
            full_name="Owner Taxonomy Norm Race",
            created_at=now,
            updated_at=now,
        )
        setup_session.add(owner)
        await setup_session.commit()
        owner_id = owner.id

    async def override_get_db():
        async with session_factory() as session:
            yield session

    class CurrentUser:
        id = owner_id
        email = owner_email

    category_cols = getattr(Category, "__table__").c
    project_category_cols = getattr(ProjectCategory, "__table__").c
    project_member_cols = getattr(ProjectMember, "__table__").c
    project_cols = getattr(Project, "__table__").c
    user_cols = getattr(User, "__table__").c
    created_project_ids: list[str] = []
    try:
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: CurrentUser()
        try:
            first_response, second_response = await asyncio.gather(
                api_client.post(
                    "/api/v1/projects",
                    json=_create_project_payload(
                        title=f"Normalization Race A {unique}",
                        categories=[raw_variant_a],
                    ),
                ),
                api_client.post(
                    "/api/v1/projects",
                    json=_create_project_payload(
                        title=f"Normalization Race B {unique}",
                        categories=[raw_variant_b],
                    ),
                ),
            )
        finally:
            app.dependency_overrides.clear()

        assert first_response.status_code == 201
        assert second_response.status_code == 201
        created_project_ids = [
            first_response.json()["id"],
            second_response.json()["id"],
        ]

        async with session_factory() as verify_session:
            categories_result = await verify_session.exec(
                select(Category).where(category_cols.normalized_name == normalized_term)
            )
            categories = categories_result.all()
            assert len(categories) == 1
            category_id = categories[0].id

            assignment_result = await verify_session.exec(
                select(ProjectCategory).where(
                    project_category_cols.project_id.in_(created_project_ids)
                )
            )
            assignments = assignment_result.all()
            assert len(assignments) == 2
            assert {row.category_id for row in assignments} == {category_id}
    finally:
        async with session_factory() as cleanup_session:
            if created_project_ids:
                await cleanup_session.exec(
                    delete(ProjectCategory).where(
                        project_category_cols.project_id.in_(created_project_ids)
                    )
                )
                await cleanup_session.exec(
                    delete(ProjectMember).where(
                        project_member_cols.project_id.in_(created_project_ids)
                    )
                )
                await cleanup_session.exec(
                    delete(Project).where(project_cols.id.in_(created_project_ids))
                )
            await cleanup_session.exec(
                delete(Category).where(category_cols.normalized_name == normalized_term)
            )
            await cleanup_session.exec(delete(User).where(user_cols.id == owner_id))
            await cleanup_session.commit()


@pytest.mark.asyncio
async def test_concurrent_cross_vocabulary_create_on_miss_is_independent(
    api_client, async_engine
):
    now = datetime.now(timezone.utc)
    unique = uuid4().hex[:8]
    owner_email = f"owner_taxonomy_vocab_race_{unique}@ufl.edu"
    shared_term = f"Platform {unique}"
    normalized_term = f"platform {unique}"
    session_factory = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        class_=SQLModelAsyncSession,
    )

    async with session_factory() as setup_session:
        owner = User(
            email=owner_email,
            username=f"owner_{unique}",
            password_hash="integration-password-hash",
            full_name="Owner Taxonomy Vocab Race",
            created_at=now,
            updated_at=now,
        )
        setup_session.add(owner)
        await setup_session.commit()
        owner_id = owner.id

    async def override_get_db():
        async with session_factory() as session:
            yield session

    class CurrentUser:
        id = owner_id
        email = owner_email

    category_cols = getattr(Category, "__table__").c
    tag_cols = getattr(Tag, "__table__").c
    tech_stack_cols = getattr(TechStack, "__table__").c
    project_category_cols = getattr(ProjectCategory, "__table__").c
    project_tag_cols = getattr(ProjectTag, "__table__").c
    project_tech_stack_cols = getattr(ProjectTechStack, "__table__").c
    project_member_cols = getattr(ProjectMember, "__table__").c
    project_cols = getattr(Project, "__table__").c
    user_cols = getattr(User, "__table__").c
    created_project_ids: list[str] = []
    try:
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: CurrentUser()
        try:
            category_response, tag_response, stack_response = await asyncio.gather(
                api_client.post(
                    "/api/v1/projects",
                    json=_create_project_payload(
                        title=f"Vocab Race Category {unique}",
                        categories=[shared_term],
                    ),
                ),
                api_client.post(
                    "/api/v1/projects",
                    json=_create_project_payload(
                        title=f"Vocab Race Tag {unique}",
                        tags=[shared_term],
                    ),
                ),
                api_client.post(
                    "/api/v1/projects",
                    json=_create_project_payload(
                        title=f"Vocab Race Stack {unique}",
                        tech_stack=[shared_term],
                    ),
                ),
            )
        finally:
            app.dependency_overrides.clear()

        assert category_response.status_code == 201
        assert tag_response.status_code == 201
        assert stack_response.status_code == 201
        created_project_ids = [
            category_response.json()["id"],
            tag_response.json()["id"],
            stack_response.json()["id"],
        ]

        async with session_factory() as verify_session:
            category_result = await verify_session.exec(
                select(Category).where(category_cols.normalized_name == normalized_term)
            )
            tag_result = await verify_session.exec(
                select(Tag).where(tag_cols.normalized_name == normalized_term)
            )
            stack_result = await verify_session.exec(
                select(TechStack).where(
                    tech_stack_cols.normalized_name == normalized_term
                )
            )

            categories = category_result.all()
            tags = tag_result.all()
            stacks = stack_result.all()
            assert len(categories) == 1
            assert len(tags) == 1
            assert len(stacks) == 1
            assert categories[0].id != tags[0].id
            assert categories[0].id != stacks[0].id
            assert tags[0].id != stacks[0].id

            category_assignment_result = await verify_session.exec(
                select(ProjectCategory).where(
                    project_category_cols.project_id == created_project_ids[0]
                )
            )
            tag_assignment_result = await verify_session.exec(
                select(ProjectTag).where(
                    project_tag_cols.project_id == created_project_ids[1]
                )
            )
            stack_assignment_result = await verify_session.exec(
                select(ProjectTechStack).where(
                    project_tech_stack_cols.project_id == created_project_ids[2]
                )
            )

            assert len(category_assignment_result.all()) == 1
            assert len(tag_assignment_result.all()) == 1
            assert len(stack_assignment_result.all()) == 1
    finally:
        async with session_factory() as cleanup_session:
            if created_project_ids:
                await cleanup_session.exec(
                    delete(ProjectCategory).where(
                        project_category_cols.project_id.in_(created_project_ids)
                    )
                )
                await cleanup_session.exec(
                    delete(ProjectTag).where(
                        project_tag_cols.project_id.in_(created_project_ids)
                    )
                )
                await cleanup_session.exec(
                    delete(ProjectTechStack).where(
                        project_tech_stack_cols.project_id.in_(created_project_ids)
                    )
                )
                await cleanup_session.exec(
                    delete(ProjectMember).where(
                        project_member_cols.project_id.in_(created_project_ids)
                    )
                )
                await cleanup_session.exec(
                    delete(Project).where(project_cols.id.in_(created_project_ids))
                )
            await cleanup_session.exec(
                delete(Category).where(category_cols.normalized_name == normalized_term)
            )
            await cleanup_session.exec(
                delete(Tag).where(tag_cols.normalized_name == normalized_term)
            )
            await cleanup_session.exec(
                delete(TechStack).where(
                    tech_stack_cols.normalized_name == normalized_term
                )
            )
            await cleanup_session.exec(delete(User).where(user_cols.id == owner_id))
            await cleanup_session.commit()
