from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.models.project import Project
from app.models.project import Vote
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
    unique = uuid4().hex[:8]
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, f"search-keyword-{unique}@ufl.edu")
    keyword = f"Gator-{unique}"
    title_match = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"{keyword} Search",
        short_description="Plain text",
        vote_count=10,
        created_at=now,
    )
    description_match = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="No keyword here",
        short_description=f"This uses {keyword} keyword in description",
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
        request=ProjectSearchRequest(q=f"  {keyword.upper()}  ", sort="new")
    )

    assert [item.id for item in response.items] == [
        title_match.id,
        description_match.id,
    ]


@pytest.mark.asyncio
async def test_search_projects_taxonomy_or_within_and_across_families(db_session):
    unique = uuid4().hex[:8]
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, f"search-taxonomy-{unique}@ufl.edu")
    c1 = f"AI-{unique}"
    t1 = f"Python-{unique}"
    t2 = f"TypeScript-{unique}"
    c3 = f"Web-{unique}"
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
        categories=[c1],
        tags=[t1],
        tech_stack=[],
        taxonomy_principal=owner,
    )
    await project_service._replace_project_taxonomy_assignments(
        project_id=_ai_only.id,
        categories=[c1],
        tags=[t2],
        tech_stack=[],
        taxonomy_principal=owner,
    )
    await project_service._replace_project_taxonomy_assignments(
        project_id=_python_only.id,
        categories=[c3],
        tags=[t1],
        tech_stack=[],
        taxonomy_principal=owner,
    )
    await db_session.flush()

    service = PostgresSearchService(db_session)
    response = await service.search_projects(
        request=ProjectSearchRequest(
            categories=[c1.lower()],
            tags=[t1.lower(), "not-real-tag"],
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
    unique = uuid4().hex[:8]
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, f"search-cursor-context-{unique}@ufl.edu")
    keyword = f"alpha-{unique}"
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"Context {keyword}",
        short_description="Alpha project",
        vote_count=5,
        created_at=now,
    )
    await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"Context {keyword} 2",
        short_description="Alpha project two",
        vote_count=4,
        created_at=now - timedelta(minutes=1),
    )

    service = PostgresSearchService(db_session)
    first_page = await service.search_projects(
        request=ProjectSearchRequest(q=keyword, sort="new", limit=1)
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
    unique = uuid4().hex[:8]
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, f"search-top-window-{unique}@ufl.edu")
    keyword = f"window search {unique}"
    recent = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"{keyword} Recent",
        short_description="Window result recent",
        vote_count=10,
        created_at=now - timedelta(days=5),
    )
    _old = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"{keyword} Old",
        short_description="Window result old",
        vote_count=999,
        created_at=now - timedelta(days=150),
    )

    service = PostgresSearchService(db_session)
    response = await service.search_projects(
        request=ProjectSearchRequest(q=keyword, sort="top")
    )

    assert [item.id for item in response.items] == [recent.id]


@pytest.mark.asyncio
async def test_search_projects_keyword_special_chars_are_treated_as_literals(
    db_session,
):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "search-keyword-literals@ufl.edu")
    literal_match = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="100% coverage _guide\\notes",
        short_description="Literal keyword symbols",
        vote_count=10,
        created_at=now,
    )
    _wildcard_candidate = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="1000 coverage xguideanotes",
        short_description="Should not match literal symbol query",
        vote_count=9,
        created_at=now - timedelta(minutes=1),
    )

    service = PostgresSearchService(db_session)
    response = await service.search_projects(
        request=ProjectSearchRequest(q="% coverage _guide\\", sort="new")
    )

    assert [item.id for item in response.items] == [literal_match.id]


@pytest.mark.asyncio
async def test_search_projects_top_cursor_continuity_and_range_mismatch(db_session):
    unique = uuid4().hex[:8]
    now = datetime.now(UTC)
    owner = await _seed_user(db_session, f"search-top-cursor-window-{unique}@ufl.edu")
    keyword = f"top cursor {unique}"
    first = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"{keyword} first",
        short_description="top cursor first",
        vote_count=20,
        created_at=now - timedelta(days=1),
    )
    second = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"{keyword} second",
        short_description="top cursor second",
        vote_count=10,
        created_at=now - timedelta(days=2),
    )
    _third = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"{keyword} third",
        short_description="top cursor third",
        vote_count=5,
        created_at=now - timedelta(days=3),
    )

    service = PostgresSearchService(db_session)
    page_one = await service.search_projects(
        request=ProjectSearchRequest(q=keyword, sort="top", limit=2)
    )
    assert [item.id for item in page_one.items] == [first.id, second.id]
    assert page_one.next_cursor is not None

    page_two = await service.search_projects(
        request=ProjectSearchRequest(
            q=keyword,
            sort="top",
            limit=2,
            cursor=page_one.next_cursor,
        )
    )
    assert len(page_two.items) == 1

    with pytest.raises(CursorError, match="Cursor does not match requested search"):
        await service.search_projects(
            request=ProjectSearchRequest(
                q=keyword,
                sort="top",
                limit=2,
                cursor=page_one.next_cursor,
                published_from=(now - timedelta(days=30)).date(),
                published_to=now.date(),
            )
        )


@pytest.mark.asyncio
async def test_search_projects_filter_truth_table_or_within_and_across_families(
    db_session,
):
    now = datetime.now(timezone.utc)
    unique = uuid4().hex[:8]
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, f"search-filter-matrix-{unique}@ufl.edu")
    keyword = f"Matrix-{unique}"
    p1 = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"{keyword} one",
        short_description="category ai tag python",
        vote_count=10,
        created_at=now,
    )
    p2 = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"{keyword} two",
        short_description="category web tag python",
        vote_count=9,
        created_at=now - timedelta(minutes=1),
    )
    _p3 = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"{keyword} three",
        short_description="category ai tag rust",
        vote_count=8,
        created_at=now - timedelta(minutes=2),
    )
    c1 = f"AI-{unique}"
    t1 = f"Python-{unique}"
    t2 = f"Rust-{unique}"
    c3 = f"Web-{unique}"
    project_service = ProjectService(db_session)
    await project_service._replace_project_taxonomy_assignments(
        project_id=p1.id,
        categories=[c1],
        tags=[t1],
        tech_stack=[],
        taxonomy_principal=owner,
    )
    await project_service._replace_project_taxonomy_assignments(
        project_id=p2.id,
        categories=[c3],
        tags=[t1],
        tech_stack=[],
        taxonomy_principal=owner,
    )
    await project_service._replace_project_taxonomy_assignments(
        project_id=_p3.id,
        categories=[c1],
        tags=[t2],
        tech_stack=[],
        taxonomy_principal=owner,
    )
    await db_session.flush()

    service = PostgresSearchService(db_session)
    tags_only = await service.search_projects(
        request=ProjectSearchRequest(tags=[t1.lower(), t2.lower()], sort="new")
    )
    assert [item.id for item in tags_only.items] == [p1.id, p2.id, _p3.id]

    tags_and_category = await service.search_projects(
        request=ProjectSearchRequest(
            tags=[t1.lower(), t2.lower()], categories=[c1.lower()], sort="new"
        )
    )
    assert [item.id for item in tags_and_category.items] == [p1.id, _p3.id]


@pytest.mark.asyncio
async def test_search_projects_unknown_term_mixed_filter_behavior(db_session):
    now = datetime.now(timezone.utc)
    unique = uuid4().hex[:8]
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, f"search-unknown-mixed-{unique}@ufl.edu")
    keyword = f"Unknown-{unique}"
    match = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"{keyword} mixed match",
        short_description="known tag only",
        vote_count=10,
        created_at=now,
    )
    c1 = f"AI-{unique}"
    t1 = f"Python-{unique}"
    project_service = ProjectService(db_session)
    await project_service._replace_project_taxonomy_assignments(
        project_id=match.id,
        categories=[c1],
        tags=[t1],
        tech_stack=[],
        taxonomy_principal=owner,
    )
    await db_session.flush()

    service = PostgresSearchService(db_session)
    mixed = await service.search_projects(
        request=ProjectSearchRequest(tags=[t1.lower(), "no-such-tag"], sort="new")
    )
    assert [item.id for item in mixed.items] == [match.id]

    cross_family_unknown = await service.search_projects(
        request=ProjectSearchRequest(
            tags=[t1.lower()],
            categories=["definitely-not-real"],
            sort="new",
        )
    )
    assert cross_family_unknown.items == []


@pytest.mark.asyncio
async def test_search_projects_viewer_has_voted_differs_for_authenticated_user(
    db_session,
):
    now = datetime.now(timezone.utc)
    unique = uuid4().hex[:8]
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, f"search-voted-owner-{unique}@ufl.edu")
    voter = await _seed_user(db_session, f"search-voted-viewer-{unique}@ufl.edu")
    keyword = f"vote-check-{unique}"
    voted = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"Voted project {unique}",
        short_description=keyword,
        vote_count=1,
        created_at=now,
    )
    unvoted = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"Unvoted project {unique}",
        short_description=keyword,
        vote_count=0,
        created_at=now - timedelta(minutes=1),
    )
    db_session.add(Vote(user_id=voter.id, project_id=voted.id, created_at=now))
    await db_session.flush()

    service = PostgresSearchService(db_session)
    anonymous = await service.search_projects(
        request=ProjectSearchRequest(q=keyword, sort="new")
    )
    authed = await service.search_projects(
        request=ProjectSearchRequest(q=keyword, sort="new"),
        current_user_id=voter.id,
    )

    anon_flags = {item.id: item.viewer_has_voted for item in anonymous.items}
    authed_flags = {item.id: item.viewer_has_voted for item in authed.items}
    assert anon_flags[voted.id] is False
    assert anon_flags[unvoted.id] is False
    assert authed_flags[voted.id] is True
    assert authed_flags[unvoted.id] is False


@pytest.mark.asyncio
async def test_search_projects_excludes_soft_deleted_matches(db_session):
    now = datetime.now(timezone.utc)
    unique = uuid4().hex[:8]
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, f"search-soft-delete-{unique}@ufl.edu")
    keyword = f"Deleted-{unique}"
    visible = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"{keyword} scope visible",
        short_description="visible record",
        vote_count=10,
        created_at=now,
    )
    deleted = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title=f"{keyword} scope deleted",
        short_description="should be excluded",
        vote_count=100,
        created_at=now - timedelta(minutes=1),
    )
    deleted.deleted_at = now
    db_session.add(deleted)
    await db_session.flush()

    service = PostgresSearchService(db_session)
    response = await service.search_projects(
        request=ProjectSearchRequest(q=keyword, sort="new")
    )

    assert [item.id for item in response.items] == [visible.id]
