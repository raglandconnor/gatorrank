import pytest
import pytest_asyncio
from uuid import uuid4
from httpx import ASGITransport, AsyncClient
import sqlalchemy as sa
import jwt
from datetime import UTC, datetime, timedelta

from app.main import app
from app.db.database import get_db
from app.models.user import User
from app.models.project import Project, Vote
from app.services.project import ProjectService
from app.core.config import get_settings
from app.services.vote import VoteService

settings = get_settings()


@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


def generate_token(user_id, email, jwt_secret):
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "email": email,
            "aud": "authenticated",
            "iat": int(now.timestamp()),
            "exp": now + timedelta(minutes=5),
        },
        jwt_secret,
        algorithm="HS256",
    )


async def seed_auth_user(
    db_session, *, user_id, email: str, username: str | None = None
) -> None:
    resolved_username = username or f"user_{uuid4().hex[:10]}"
    user = User(  # pyright: ignore[reportCallIssue]
        id=user_id,
        email=email,
        username=resolved_username,
        password_hash="integration-password-hash",
        role="student",
    )
    db_session.add(user)
    await db_session.commit()


async def _seed_owned_project(
    db_session,
    *,
    created_by_id,
    title: str,
    slug: str,
    is_published: bool,
    created_at: datetime,
    vote_count: int = 0,
    deleted_at: datetime | None = None,
) -> Project:
    project = Project(
        id=uuid4(),
        created_by_id=created_by_id,
        title=title,
        slug=slug,
        short_description=f"{title} description",
        vote_count=vote_count,
        is_group_project=False,
        is_published=is_published,
        published_at=created_at if is_published else None,
        created_at=created_at,
        updated_at=created_at,
        deleted_at=deleted_at,
    )  # pyright: ignore[reportCallIssue]
    db_session.add(project)
    await db_session.commit()
    return project


@pytest.mark.asyncio
async def test_get_current_user_profile(api_client, db_session, monkeypatch):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    username = "profile_user"
    await seed_auth_user(db_session, user_id=user_id, email=email, username=username)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(user_id)
        assert data["email"] == email
        assert data["username"] == username
        assert data["full_name"] is None
        assert "updated_at" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_current_user_profile(api_client, db_session, monkeypatch):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "New Integration Name",
                "profile_picture_url": "https://example.com/pic.jpg",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "New Integration Name"
        assert data["profile_picture_url"] == "https://example.com/pic.jpg"

        # Verify DB
        db_user = await db_session.exec(sa.select(User).where(User.id == user_id))  # pyright: ignore[reportArgumentType]
        user_record = db_user.scalars().one()
        assert user_record.full_name == "New Integration Name"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_current_user_profile_partial_update(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "profile_picture_url": "https://example.com/partial.jpg",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] is None
        assert data["profile_picture_url"] == "https://example.com/partial.jpg"

        db_user = await db_session.exec(sa.select(User).where(User.id == user_id))  # pyright: ignore[reportArgumentType]
        user_record = db_user.scalars().one()
        assert user_record.full_name is None
        assert user_record.profile_picture_url == "https://example.com/partial.jpg"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_current_user_profile_empty_payload_returns_422(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_current_user_profile_invalid_url_returns_422(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"profile_picture_url": "invalid-url"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_current_user_profile_rejects_null_full_name(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        setup_response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Will Be Cleared"},
        )
        assert setup_response.status_code == 200

        response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": None},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_patch_current_user_profile_rejects_username_update(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"username": "new_username"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_current_user_profile_unknown_user_returns_401(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    token = generate_token(user_id, email, jwt_secret)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_user_profile(api_client, db_session, monkeypatch):
    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"

    # Pre-insert user
    user = User(  # pyright: ignore[reportCallIssue]
        id=user_id,
        email=email,
        username="public_user",
        password_hash="integration-password-hash",
        full_name="Public User",
        role="student",
    )
    db_session.add(user)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(user_id)
        assert data["username"] == "public_user"
        assert data["full_name"] == "Public User"
        assert "email" not in data  # Public info
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_user_profile_by_username_case_insensitive(api_client, db_session):
    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    username = "public_lookup_user"

    user = User(  # pyright: ignore[reportCallIssue]
        id=user_id,
        email=email,
        username=username,
        password_hash="integration-password-hash",
        full_name="Public User",
        role="student",
    )
    db_session.add(user)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(f"/api/v1/users/by-username/{username.upper()}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(user_id)
        assert data["username"] == username
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_user_projects(api_client, db_session):
    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"

    # Pre-insert user and some projects
    user = User(  # pyright: ignore[reportCallIssue]
        id=user_id,
        email=email,
        username="author_user",
        password_hash="integration-password-hash",
        full_name="Author",
        role="student",
    )
    db_session.add(user)
    await db_session.commit()

    from datetime import datetime

    now = datetime.now(UTC)

    # Published project
    p1 = Project(
        id=uuid4(),
        title="Published Project",
        slug="published-project",
        short_description="Desc",
        is_published=True,
        published_at=now,
        created_by_id=user_id,
    )  # pyright: ignore[reportCallIssue]
    # Draft project (should not be returned)
    p2 = Project(
        id=uuid4(),
        title="Draft Project",
        slug="draft-project",
        short_description="Desc",
        is_published=False,
        created_by_id=user_id,
    )  # pyright: ignore[reportCallIssue]
    db_session.add_all([p1, p2])
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(f"/api/v1/users/{user_id}/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(p1.id)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_user_projects_by_username(api_client, db_session):
    user_id = uuid4()
    email = f"user-{uuid4().hex[:8]}@ufl.edu"
    username = "author_lookup_user"

    user = User(  # pyright: ignore[reportCallIssue]
        id=user_id,
        email=email,
        username=username,
        password_hash="integration-password-hash",
        full_name="Author",
        role="student",
    )
    db_session.add(user)
    await db_session.commit()

    now = datetime.now(UTC)
    p1 = Project(
        id=uuid4(),
        title="Published Project",
        slug="published-project",
        short_description="Desc",
        is_published=True,
        published_at=now,
        created_by_id=user_id,
    )  # pyright: ignore[reportCallIssue]
    p2 = Project(
        id=uuid4(),
        title="Draft Project",
        slug="draft-project",
        short_description="Desc",
        is_published=False,
        created_by_id=user_id,
    )  # pyright: ignore[reportCallIssue]
    db_session.add_all([p1, p2])
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            f"/api/v1/users/by-username/{username.upper()}/projects"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(p1.id)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_my_projects_default_includes_drafts_and_published_excludes_deleted(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    owner_id = uuid4()
    email = f"my-projects-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(
        db_session, user_id=owner_id, email=email, username="my_projects_owner"
    )
    token = generate_token(owner_id, email, jwt_secret)

    now = datetime.now(UTC)
    published = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Visible Published",
        slug="visible-published",
        is_published=True,
        created_at=now - timedelta(hours=2),
        vote_count=4,
    )
    draft = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Visible Draft",
        slug="visible-draft",
        is_published=False,
        created_at=now - timedelta(hours=1),
    )
    _deleted = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Deleted Draft",
        slug="deleted-draft",
        is_published=False,
        created_at=now - timedelta(minutes=30),
        deleted_at=now - timedelta(minutes=5),
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/api/v1/users/me/projects",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [
        str(draft.id),
        str(published.id),
    ]


@pytest.mark.asyncio
async def test_list_my_projects_visibility_filters_and_taxonomy_order(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    owner_id = uuid4()
    email = f"my-projects-taxonomy-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(
        db_session, user_id=owner_id, email=email, username="my_projects_taxonomy"
    )
    token = generate_token(owner_id, email, jwt_secret)

    now = datetime.now(UTC)
    published = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Published Taxonomy",
        slug="published-taxonomy",
        is_published=True,
        created_at=now - timedelta(days=1),
        vote_count=2,
    )
    draft = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Draft Taxonomy",
        slug="draft-taxonomy",
        is_published=False,
        created_at=now,
    )

    service = ProjectService(db_session)
    await service._replace_project_taxonomy_assignments(  # type: ignore[attr-defined]
        project_id=draft.id,
        categories=["Backend", "AI"],
        tags=["FastAPI", "Python"],
        tech_stack=["SQLModel", "Supabase"],
    )
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        draft_response = await api_client.get(
            "/api/v1/users/me/projects?visibility=draft",
            headers={"Authorization": f"Bearer {token}"},
        )
        published_response = await api_client.get(
            "/api/v1/users/me/projects?visibility=published",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert draft_response.status_code == 200
    draft_payload = draft_response.json()
    assert [item["id"] for item in draft_payload["items"]] == [str(draft.id)]
    assert [term["name"] for term in draft_payload["items"][0]["categories"]] == [
        "Backend",
        "AI",
    ]
    assert [term["name"] for term in draft_payload["items"][0]["tags"]] == [
        "FastAPI",
        "Python",
    ]
    assert [term["name"] for term in draft_payload["items"][0]["tech_stack"]] == [
        "SQLModel",
        "Supabase",
    ]

    assert published_response.status_code == 200
    published_payload = published_response.json()
    assert [item["id"] for item in published_payload["items"]] == [str(published.id)]


@pytest.mark.asyncio
async def test_list_my_projects_sort_new_paginates_mixed_results(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    owner_id = uuid4()
    email = f"my-projects-new-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(
        db_session, user_id=owner_id, email=email, username="my_projects_new"
    )
    token = generate_token(owner_id, email, jwt_secret)

    now = datetime.now(UTC)
    newest = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Newest Draft",
        slug="newest-draft",
        is_published=False,
        created_at=now,
    )
    middle = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Middle Published",
        slug="middle-published",
        is_published=True,
        created_at=now - timedelta(minutes=1),
        vote_count=1,
    )
    oldest = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Oldest Draft",
        slug="oldest-draft",
        is_published=False,
        created_at=now - timedelta(minutes=2),
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        first_page = await api_client.get(
            "/api/v1/users/me/projects?sort=new&limit=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert first_page.status_code == 200
        first_payload = first_page.json()
        assert [item["id"] for item in first_payload["items"]] == [
            str(newest.id),
            str(middle.id),
        ]
        assert first_payload["next_cursor"] is not None

        second_page = await api_client.get(
            f"/api/v1/users/me/projects?sort=new&limit=2&cursor={first_payload['next_cursor']}",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert second_page.status_code == 200
    second_payload = second_page.json()
    assert [item["id"] for item in second_payload["items"]] == [str(oldest.id)]
    assert second_payload["next_cursor"] is None


@pytest.mark.asyncio
async def test_list_my_projects_sort_top_published_matches_top_window(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    owner_id = uuid4()
    email = f"my-projects-top-pub-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(
        db_session, user_id=owner_id, email=email, username="my_projects_top_pub"
    )
    token = generate_token(owner_id, email, jwt_secret)

    now = datetime.now(UTC)
    high = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="High Vote Published",
        slug="high-vote-published",
        is_published=True,
        created_at=now - timedelta(days=2),
        vote_count=50,
    )
    low = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Low Vote Published",
        slug="low-vote-published",
        is_published=True,
        created_at=now - timedelta(days=1),
        vote_count=10,
    )
    _old = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Old Published",
        slug="old-published",
        is_published=True,
        created_at=now - timedelta(days=150),
        vote_count=999,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/api/v1/users/me/projects?sort=top&visibility=published",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [str(high.id), str(low.id)]


@pytest.mark.asyncio
async def test_list_my_projects_sort_top_all_transitions_from_published_to_drafts(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    owner_id = uuid4()
    email = f"my-projects-top-all-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(
        db_session, user_id=owner_id, email=email, username="my_projects_top_all"
    )
    token = generate_token(owner_id, email, jwt_secret)

    now = datetime.now(UTC)
    published_one = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Published One",
        slug="published-one",
        is_published=True,
        created_at=now - timedelta(hours=3),
        vote_count=20,
    )
    published_two = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Published Two",
        slug="published-two",
        is_published=True,
        created_at=now - timedelta(hours=2),
        vote_count=10,
    )
    draft_newest = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Draft Newest",
        slug="draft-newest",
        is_published=False,
        created_at=now - timedelta(hours=1),
    )
    draft_oldest = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Draft Oldest",
        slug="draft-oldest",
        is_published=False,
        created_at=now - timedelta(hours=4),
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        first_page = await api_client.get(
            "/api/v1/users/me/projects?sort=top&visibility=all&limit=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert first_page.status_code == 200
        first_payload = first_page.json()
        assert [item["id"] for item in first_payload["items"]] == [
            str(published_one.id),
            str(published_two.id),
        ]
        assert first_payload["next_cursor"] is not None

        second_page = await api_client.get(
            f"/api/v1/users/me/projects?sort=top&visibility=all&limit=2&cursor={first_payload['next_cursor']}",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert second_page.status_code == 200
    second_payload = second_page.json()
    assert [item["id"] for item in second_payload["items"]] == [
        str(draft_newest.id),
        str(draft_oldest.id),
    ]
    assert second_payload["next_cursor"] is None


@pytest.mark.asyncio
async def test_list_my_projects_sort_top_draft_returns_newest_first_and_ignores_dates(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    owner_id = uuid4()
    email = f"my-projects-top-draft-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(
        db_session, user_id=owner_id, email=email, username="my_projects_top_draft"
    )
    token = generate_token(owner_id, email, jwt_secret)

    now = datetime.now(UTC)
    newest = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Draft Newest Top",
        slug="draft-newest-top",
        is_published=False,
        created_at=now,
    )
    oldest = await _seed_owned_project(
        db_session,
        created_by_id=owner_id,
        title="Draft Oldest Top",
        slug="draft-oldest-top",
        is_published=False,
        created_at=now - timedelta(days=120),
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/api/v1/users/me/projects"
            "?sort=top&visibility=draft&published_from=2020-01-01&published_to=2020-12-31",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [str(newest.id), str(oldest.id)]


@pytest.mark.asyncio
async def test_list_my_voted_projects_excludes_soft_deleted_projects(
    api_client, db_session, monkeypatch
):
    jwt_secret = "integration-test-jwt-secret-at-least-32b"
    monkeypatch.setattr(settings, "DATABASE_JWT_SECRET", jwt_secret)

    user_id = uuid4()
    email = f"user-votes-{uuid4().hex[:8]}@ufl.edu"
    await seed_auth_user(db_session, user_id=user_id, email=email)
    token = generate_token(user_id, email, jwt_secret)

    now = datetime.now(UTC)
    visible = Project(
        id=uuid4(),
        title="Visible Voted Project",
        slug="visible-voted-project",
        short_description="Visible voted project description",
        is_published=True,
        published_at=now,
        created_by_id=user_id,
    )  # pyright: ignore[reportCallIssue]
    deleted = Project(
        id=uuid4(),
        title="Deleted Voted Project",
        slug="deleted-voted-project",
        short_description="Deleted voted project description",
        is_published=True,
        published_at=now,
        created_by_id=user_id,
        deleted_at=now,
    )  # pyright: ignore[reportCallIssue]
    db_session.add_all([visible, deleted])
    await db_session.commit()

    vote_service = VoteService(db_session)
    await vote_service.add_vote(project_id=visible.id, user_id=user_id)
    db_session.add(Vote(user_id=user_id, project_id=deleted.id, created_at=now))
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await api_client.get(
            "/api/v1/users/me/votes",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [str(visible.id)]
