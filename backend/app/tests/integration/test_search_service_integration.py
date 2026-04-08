from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.models.project import Project
from app.models.user import User
from app.schemas.search import ProjectSearchRequest
from app.services.project import CursorError, ProjectService
from app.services.search import PostgresSearchService


async def _seed_user(db_session, email: str) -> User:
    now = datetime.now(timezone.utc)
    user = User(
        email=email,
        username=f"user_{uuid4().hex[:10]}",
        password_hash="integration-password-hash",
        role="student",
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
    short_description: str,
    vote_count: int,
    created_at: datetime,
) -> Project:
    project = Project(
        created_by_id=created_by_id,
        title=title,
        slug=f"{title.lower().replace(' ', '-')}-{uuid4().hex[:8]}",
        short_description=short_description,
        long_description=None,
        demo_url=None,
        github_url=None,
        video_url=None,
        vote_count=vote_count,
        is_group_project=False,
        is_published=True,
        published_at=created_at,
        created_at=created_at,
        updated_at=created_at,
    )
    db_session.add(project)
    await db_session.flush()
    return project


@pytest.mark.asyncio
async def test_search_projects_keyword_matches_title_and_short_description(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "search-keyword@ufl.edu")
    title_match = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Gator Search",
        short_description="Plain text",
        vote_count=10,
        created_at=now,
    )
    description_match = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="No keyword here",
        short_description="This uses gAtOr keyword in description",
        vote_count=9,
        created_at=now - timedelta(minutes=1),
    )
    _non_match = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Different project",
        short_description="No overlap",
        vote_count=8,
        created_at=now - timedelta(minutes=2),
    )

    service = PostgresSearchService(db_session)
    response = await service.search_projects(
        request=ProjectSearchRequest(q="  GATOR  ", sort="new")
    )

    assert [item.id for item in response.items] == [
        title_match.id,
        description_match.id,
    ]


@pytest.mark.asyncio
async def test_search_projects_taxonomy_or_within_and_across_families(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "search-taxonomy@ufl.edu")
    match_all = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Search Taxonomy Match",
        short_description="Matches both families",
        vote_count=10,
        created_at=now,
    )
    _ai_only = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="AI only",
        short_description="Category only match",
        vote_count=9,
        created_at=now - timedelta(minutes=1),
    )
    _python_only = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Python only",
        short_description="Tag only match",
        vote_count=8,
        created_at=now - timedelta(minutes=2),
    )

    project_service = ProjectService(db_session)
    await project_service._replace_project_taxonomy_assignments(
        project_id=match_all.id,
        categories=["AI"],
        tags=["Python"],
        tech_stack=[],
    )
    await project_service._replace_project_taxonomy_assignments(
        project_id=_ai_only.id,
        categories=["AI"],
        tags=["TypeScript"],
        tech_stack=[],
    )
    await project_service._replace_project_taxonomy_assignments(
        project_id=_python_only.id,
        categories=["Web"],
        tags=["Python"],
        tech_stack=[],
    )
    await db_session.flush()

    service = PostgresSearchService(db_session)
    response = await service.search_projects(
        request=ProjectSearchRequest(
            categories=["ai"],
            tags=["python", "not-real-tag"],
            sort="new",
        )
    )
    assert [item.id for item in response.items] == [match_all.id]

    unknown_only = await service.search_projects(
        request=ProjectSearchRequest(tags=["definitely-not-real"], sort="new")
    )
    assert unknown_only.items == []


@pytest.mark.asyncio
async def test_search_projects_cursor_is_bound_to_search_context(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "search-cursor-context@ufl.edu")
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Context Alpha",
        short_description="Alpha project",
        vote_count=5,
        created_at=now,
    )
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Context Alpha 2",
        short_description="Alpha project two",
        vote_count=4,
        created_at=now - timedelta(minutes=1),
    )

    service = PostgresSearchService(db_session)
    first_page = await service.search_projects(
        request=ProjectSearchRequest(q="alpha", sort="new", limit=1)
    )
    assert first_page.next_cursor is not None

    with pytest.raises(CursorError, match="Cursor does not match requested search"):
        await service.search_projects(
            request=ProjectSearchRequest(
                q="different-query",
                sort="new",
                limit=1,
                cursor=first_page.next_cursor,
            )
        )


@pytest.mark.asyncio
async def test_search_projects_top_default_window_excludes_old_projects(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "search-top-window@ufl.edu")
    recent = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Window Search",
        short_description="Window result recent",
        vote_count=10,
        created_at=now - timedelta(days=5),
    )
    _old = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Window Search Old",
        short_description="Window result old",
        vote_count=999,
        created_at=now - timedelta(days=150),
    )

    service = PostgresSearchService(db_session)
    response = await service.search_projects(
        request=ProjectSearchRequest(q="window search", sort="top")
    )

    assert [item.id for item in response.items] == [recent.id]
