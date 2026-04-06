from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from sqlmodel import select
from sqlalchemy.sql.dml import Update

from app.models.project import Project, ProjectMember, Vote
from app.models.taxonomy import Category
from app.models.user import User
from app.schemas.project import ProjectCreateRequest, ProjectUpdateRequest
from app.services.project import (
    ProjectAccessForbiddenError,
    ProjectService,
    ProjectValidationError,
)


async def _seed_user(db_session, email: str, name: str) -> User:
    now = datetime.now(timezone.utc)
    user = User(
        email=email,
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
    vote_count: int,
    is_published: bool,
    created_at: datetime,
) -> Project:
    project = Project(
        created_by_id=created_by_id,
        title=title,
        slug=title.lower().replace(" ", "-"),
        short_description=f"{title} description",
        vote_count=vote_count,
        is_group_project=False,
        is_published=is_published,
        published_at=created_at if is_published else None,
        created_at=created_at,
        updated_at=created_at,
    )
    db_session.add(project)
    await db_session.flush()
    return project


async def _seed_member(
    db_session, *, project_id, user_id, role: str, added_at: datetime
):
    member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role=role,
        added_at=added_at,
    )
    db_session.add(member)
    await db_session.flush()


async def _seed_vote(
    db_session, *, project_id, user_id, created_at: datetime | None = None
) -> None:
    now = created_at or datetime.now(timezone.utc)
    vote = Vote(
        user_id=user_id,
        project_id=project_id,
        created_at=now,
    )
    db_session.add(vote)
    await db_session.flush()


@pytest.mark.asyncio
async def test_get_project_detail_visibility(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner@ufl.edu", "Owner")
    member = await _seed_user(db_session, "member@ufl.edu", "Member")
    stranger = await _seed_user(db_session, "stranger@ufl.edu", "Stranger")

    published = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Published",
        vote_count=5,
        is_published=True,
        created_at=now - timedelta(minutes=1),
    )
    unpublished = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unpublished",
        vote_count=8,
        is_published=False,
        created_at=now,
    )
    await _seed_member(
        db_session,
        project_id=unpublished.id,
        user_id=member.id,
        role="contributor",
        added_at=now,
    )

    service = ProjectService(db_session)

    assert await service.get_project_detail(published.id, None) is not None
    assert await service.get_project_detail(unpublished.id, None) is None
    assert await service.get_project_detail(unpublished.id, owner.id) is not None
    member_view = await service.get_project_detail(unpublished.id, member.id)
    assert member_view is not None
    assert [m.user_id for m in member_view.members] == [member.id]
    assert member_view.team_size == 1
    with pytest.raises(ProjectAccessForbiddenError):
        await service.get_project_detail(unpublished.id, stranger.id)


@pytest.mark.asyncio
async def test_list_projects_top_sort_and_published_filter(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner2@ufl.edu", "Owner2")

    p1 = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Top 1",
        vote_count=100,
        is_published=True,
        created_at=now - timedelta(hours=1),
    )
    p2 = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Top 2",
        vote_count=90,
        is_published=True,
        created_at=now - timedelta(hours=2),
    )
    _draft = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Draft Hidden",
        vote_count=999,
        is_published=False,
        created_at=now - timedelta(hours=3),
    )

    service = ProjectService(db_session)
    result = await service.list_projects(sort="top", limit=10)

    assert [item.id for item in result.items] == [p1.id, p2.id]


@pytest.mark.asyncio
async def test_list_projects_top_default_window_excludes_old_published_projects(
    db_session,
):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner-window@ufl.edu", "Owner Window")

    recent = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Recent Top",
        vote_count=10,
        is_published=True,
        created_at=now - timedelta(days=10),
    )
    _old = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Old Top",
        vote_count=999,
        is_published=True,
        created_at=now - timedelta(days=150),
    )

    service = ProjectService(db_session)
    result = await service.list_projects(sort="top", limit=10)

    assert [item.id for item in result.items] == [recent.id]


@pytest.mark.asyncio
async def test_get_project_detail_returns_none_for_missing_project(db_session):
    service = ProjectService(db_session)
    random_project_id = UUID("00000000-0000-0000-0000-000000000001")
    assert await service.get_project_detail(random_project_id, None) is None


@pytest.mark.asyncio
async def test_get_project_detail_sets_viewer_has_voted(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner-voted-detail@ufl.edu", "Owner")
    voter = await _seed_user(db_session, "voter-voted-detail@ufl.edu", "Voter")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Detail Voted",
        vote_count=1,
        is_published=True,
        created_at=now,
    )
    await _seed_vote(
        db_session, project_id=project.id, user_id=voter.id, created_at=now
    )

    service = ProjectService(db_session)
    authed_detail = await service.get_project_detail(project.id, voter.id)
    anonymous_detail = await service.get_project_detail(project.id, None)

    assert authed_detail is not None
    assert authed_detail.viewer_has_voted is True
    assert anonymous_detail is not None
    assert anonymous_detail.viewer_has_voted is False


@pytest.mark.asyncio
async def test_list_projects_top_sort_tiebreakers(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner4@ufl.edu", "Owner4")

    newest = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Tie Newest",
        vote_count=42,
        is_published=True,
        created_at=now,
    )
    older = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Tie Older",
        vote_count=42,
        is_published=True,
        created_at=now - timedelta(minutes=5),
    )

    service = ProjectService(db_session)
    result = await service.list_projects(sort="top", limit=10)

    assert [item.id for item in result.items][:2] == [newest.id, older.id]


@pytest.mark.asyncio
async def test_list_projects_new_sort_cursor_pagination(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner3@ufl.edu", "Owner3")

    newest = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Newest",
        vote_count=1,
        is_published=True,
        created_at=now,
    )
    middle = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Middle",
        vote_count=1,
        is_published=True,
        created_at=now - timedelta(minutes=1),
    )
    oldest = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Oldest",
        vote_count=1,
        is_published=True,
        created_at=now - timedelta(minutes=2),
    )

    service = ProjectService(db_session)

    page_one = await service.list_projects(sort="new", limit=2)
    assert [item.id for item in page_one.items] == [newest.id, middle.id]
    assert page_one.next_cursor is not None

    page_two = await service.list_projects(
        sort="new", limit=2, cursor=page_one.next_cursor
    )
    assert [item.id for item in page_two.items] == [oldest.id]
    assert page_two.next_cursor is None


@pytest.mark.asyncio
async def test_list_projects_sets_viewer_has_voted_for_authenticated_user(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner-vote-list@ufl.edu", "Owner")
    voter = await _seed_user(db_session, "voter-vote-list@ufl.edu", "Voter")

    voted_project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Voted Project",
        vote_count=1,
        is_published=True,
        created_at=now,
    )
    unvoted_project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unvoted Project",
        vote_count=0,
        is_published=True,
        created_at=now - timedelta(minutes=1),
    )
    await _seed_vote(
        db_session,
        project_id=voted_project.id,
        user_id=voter.id,
        created_at=now,
    )

    service = ProjectService(db_session)
    result = await service.list_projects(
        sort="new",
        limit=10,
        current_user_id=voter.id,
    )

    by_id = {item.id: item for item in result.items}
    assert by_id[voted_project.id].viewer_has_voted is True
    assert by_id[unvoted_project.id].viewer_has_voted is False


@pytest.mark.asyncio
async def test_members_included_and_ordered_for_list_and_detail(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner5@ufl.edu", "Owner5")
    member_a = await _seed_user(db_session, "membera@ufl.edu", "Member A")
    member_b = await _seed_user(db_session, "memberb@ufl.edu", "Member B")

    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Members Project",
        vote_count=7,
        is_published=True,
        created_at=now,
    )

    await _seed_member(
        db_session,
        project_id=project.id,
        user_id=member_b.id,
        role="contributor",
        added_at=now + timedelta(seconds=30),
    )
    await _seed_member(
        db_session,
        project_id=project.id,
        user_id=member_a.id,
        role="maintainer",
        added_at=now,
    )

    service = ProjectService(db_session)

    detail = await service.get_project_detail(project.id, None)
    assert detail is not None
    assert [m.user_id for m in detail.members] == [member_a.id, member_b.id]
    assert detail.team_size == 2

    listing = await service.list_projects(sort="top", limit=10)
    listed = next((item for item in listing.items if item.id == project.id), None)
    assert listed is not None
    assert [m.user_id for m in listed.members] == [member_a.id, member_b.id]
    assert listed.team_size == 2


@pytest.mark.asyncio
async def test_create_project_creates_draft_and_owner_membership_and_returns_detail(
    db_session,
):
    creator = await _seed_user(db_session, "creator@ufl.edu", "Creator")
    service = ProjectService(db_session)
    payload = ProjectCreateRequest(
        title="  Build GatorRank  ",
        short_description="  A project for ranking UF projects  ",
        github_url="https://github.com/example/gatorrank",
    )

    created = await service.create_project(created_by_id=creator.id, payload=payload)

    assert created.created_by_id == creator.id
    assert created.title == "Build GatorRank"
    assert created.short_description == "A project for ranking UF projects"
    assert created.is_published is False
    assert created.published_at is None
    assert created.vote_count == 0
    assert created.members
    assert created.members[0].user_id == creator.id
    assert created.members[0].role == "owner"
    assert created.team_size == 1

    project_result = await db_session.exec(
        select(Project).where(Project.id == created.id)
    )
    project = project_result.one()
    assert project.created_by_id == creator.id
    assert project.is_published is False
    assert project.published_at is None
    assert project.vote_count == 0

    member_result = await db_session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == created.id,
            ProjectMember.user_id == creator.id,
        )
    )
    owner_member = member_result.one()
    assert owner_member.role == "owner"


@pytest.mark.asyncio
async def test_create_project_generates_transliterated_slug_and_collision_suffix(
    db_session,
):
    creator = await _seed_user(db_session, "slug-creator@ufl.edu", "Slug Creator")
    service = ProjectService(db_session)

    first = await service.create_project(
        created_by_id=creator.id,
        payload=ProjectCreateRequest(
            title="  Café Déjà Vu!  ",
            short_description="Slug transliteration coverage A",
            github_url="https://github.com/example/slug-a",
        ),
    )
    second = await service.create_project(
        created_by_id=creator.id,
        payload=ProjectCreateRequest(
            title="Cafe Deja Vu",
            short_description="Slug transliteration coverage B",
            github_url="https://github.com/example/slug-b",
        ),
    )

    assert first.slug == "cafe-deja-vu"
    assert second.slug == "cafe-deja-vu-2"


@pytest.mark.asyncio
async def test_create_project_slug_fallback_for_empty_normalized_base(db_session):
    creator = await _seed_user(
        db_session, "slug-fallback-creator@ufl.edu", "Slug Fallback Creator"
    )
    service = ProjectService(db_session)

    first = await service.create_project(
        created_by_id=creator.id,
        payload=ProjectCreateRequest(
            title="🔥🔥🔥",
            short_description="Fallback slug coverage A",
            github_url="https://github.com/example/fallback-a",
        ),
    )
    second = await service.create_project(
        created_by_id=creator.id,
        payload=ProjectCreateRequest(
            title="!!!",
            short_description="Fallback slug coverage B",
            github_url="https://github.com/example/fallback-b",
        ),
    )

    assert first.slug == "project"
    assert second.slug == "project-2"


@pytest.mark.asyncio
async def test_get_project_detail_by_slug_resolves_existing_project(db_session):
    creator = await _seed_user(db_session, "slug-detail-owner@ufl.edu", "Slug Owner")
    service = ProjectService(db_session)
    created = await service.create_project(
        created_by_id=creator.id,
        payload=ProjectCreateRequest(
            title="Slug Lookup Detail",
            short_description="Slug lookup coverage",
            github_url="https://github.com/example/slug-lookup",
        ),
    )

    by_slug = await service.get_project_detail_by_slug(created.slug, creator.id)
    assert by_slug is not None
    assert by_slug.id == created.id
    assert by_slug.slug == created.slug


@pytest.mark.asyncio
async def test_create_project_defaults_group_flag_and_persists_optional_urls(
    db_session,
):
    creator = await _seed_user(db_session, "creator2@ufl.edu", "Creator Two")
    service = ProjectService(db_session)
    payload = ProjectCreateRequest(
        title="Project URLs",
        short_description="Testing URL persistence",
        demo_url="https://example.com/demo",
        video_url="http://example.com/video",
    )

    created = await service.create_project(created_by_id=creator.id, payload=payload)

    assert created.is_group_project is False
    assert created.demo_url == "https://example.com/demo"
    assert created.github_url is None
    assert created.video_url == "http://example.com/video"

    project_result = await db_session.exec(
        select(Project).where(Project.id == created.id)
    )
    project = project_result.one()
    assert project.is_group_project is False
    assert project.demo_url == "https://example.com/demo"
    assert project.github_url is None
    assert project.video_url == "http://example.com/video"


@pytest.mark.asyncio
async def test_create_project_normalizes_empty_optional_urls_to_none(db_session):
    creator = await _seed_user(db_session, "creator3@ufl.edu", "Creator Three")
    service = ProjectService(db_session)
    payload = ProjectCreateRequest(
        title="Project Normalize",
        short_description="Normalization coverage",
        demo_url="   ",
        github_url="https://github.com/example/normalized",
        video_url="",
    )

    created = await service.create_project(created_by_id=creator.id, payload=payload)

    assert created.demo_url is None
    assert created.github_url == "https://github.com/example/normalized"
    assert created.video_url is None

    project_result = await db_session.exec(
        select(Project).where(Project.id == created.id)
    )
    project = project_result.one()
    assert project.demo_url is None
    assert project.github_url == "https://github.com/example/normalized"
    assert project.video_url is None


@pytest.mark.asyncio
async def test_create_project_rolls_back_when_commit_fails(db_session, monkeypatch):
    creator = await _seed_user(db_session, "creator4@ufl.edu", "Creator Four")
    service = ProjectService(db_session)
    payload = ProjectCreateRequest(
        title="Rollback Project",
        short_description="Rollback coverage",
        github_url="https://github.com/example/rollback",
    )

    rollback_spy = AsyncMock(return_value=None)

    async def failing_commit():
        raise RuntimeError("db commit failed")

    monkeypatch.setattr(db_session, "commit", failing_commit)
    monkeypatch.setattr(db_session, "rollback", rollback_spy)

    with pytest.raises(RuntimeError, match="db commit failed"):
        await service.create_project(created_by_id=creator.id, payload=payload)

    assert rollback_spy.await_count == 1


@pytest.mark.asyncio
async def test_create_project_rolls_back_taxonomy_term_when_assignment_fails(
    async_engine, monkeypatch
):
    unique = uuid4().hex[:8]
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

    session_factory = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        class_=SQLModelAsyncSession,
    )
    term = f"Rollback Term {unique}"
    normalized_term = f"rollback term {unique}"
    creator_email = f"creator-taxonomy-rollback-{unique}@ufl.edu"
    payload_title = f"Rollback Taxonomy {unique}"

    async with session_factory() as session:
        creator = await _seed_user(session, creator_email, "Creator Rollback")
        service = ProjectService(session)
        payload = ProjectCreateRequest(
            title=payload_title,
            short_description="Rollback taxonomy assignment coverage",
            github_url=f"https://github.com/example/rollback-taxonomy-{unique}",
            categories=[term],
        )

        async def fail_replace_join_assignments(*args, **kwargs):
            raise RuntimeError("taxonomy join insert failed")

        monkeypatch.setattr(
            service, "_replace_join_assignments", fail_replace_join_assignments
        )

        with pytest.raises(RuntimeError, match="taxonomy join insert failed"):
            await service.create_project(created_by_id=creator.id, payload=payload)

    async with session_factory() as verify_session:
        created_project_result = await verify_session.exec(
            select(Project).where(Project.title == payload_title)
        )
        assert created_project_result.one_or_none() is None

        category_result = await verify_session.exec(
            select(Category).where(Category.normalized_name == normalized_term)
        )
        assert category_result.one_or_none() is None

        user_result = await verify_session.exec(
            select(User).where(User.email == creator_email)
        )
        creator = user_result.one_or_none()
        if creator is not None:
            await verify_session.delete(creator)
            await verify_session.commit()


@pytest.mark.asyncio
async def test_update_project_owner_can_edit_published_project(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner-update@ufl.edu", "Owner Update")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Update Target",
        vote_count=5,
        is_published=True,
        created_at=now,
    )
    project.demo_url = "https://example.com/original-demo"
    project.github_url = None
    project.video_url = None
    await db_session.flush()

    service = ProjectService(db_session)
    payload = ProjectUpdateRequest(
        title="  Updated Title  ",
        github_url=" https://github.com/example/updated ",
        demo_url="",
    )

    updated = await service.update_project(
        project_id=project.id,
        current_user_id=owner.id,
        payload=payload,
    )

    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.github_url == "https://github.com/example/updated"
    assert updated.demo_url is None
    assert updated.is_published is True

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = project_result.one()
    assert refreshed.title == "Updated Title"
    assert refreshed.github_url == "https://github.com/example/updated"
    assert refreshed.demo_url is None
    assert refreshed.is_published is True


@pytest.mark.asyncio
async def test_update_project_rejects_non_owner(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner-update-2@ufl.edu", "Owner Update 2")
    maintainer = await _seed_user(
        db_session, "maintainer-update@ufl.edu", "Maintainer Update"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Owner Only Edit",
        vote_count=0,
        is_published=False,
        created_at=now,
    )
    await _seed_member(
        db_session,
        project_id=project.id,
        user_id=maintainer.id,
        role="maintainer",
        added_at=now,
    )

    service = ProjectService(db_session)
    payload = ProjectUpdateRequest(title="Blocked Update")

    with pytest.raises(ProjectAccessForbiddenError):
        await service.update_project(
            project_id=project.id,
            current_user_id=maintainer.id,
            payload=payload,
        )


@pytest.mark.asyncio
async def test_update_project_requires_at_least_one_resulting_url(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner-update-3@ufl.edu", "Owner Update 3")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="URL Rule",
        vote_count=0,
        is_published=False,
        created_at=now,
    )
    project.demo_url = "https://example.com/demo"
    project.github_url = None
    project.video_url = None
    await db_session.flush()

    service = ProjectService(db_session)
    payload = ProjectUpdateRequest(demo_url=None)

    with pytest.raises(
        ProjectValidationError,
        match="Provide at least one of demo_url, github_url, or video_url.",
    ):
        await service.update_project(
            project_id=project.id,
            current_user_id=owner.id,
            payload=payload,
        )


@pytest.mark.asyncio
async def test_update_project_rejects_timeline_end_without_start(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(
        db_session, "owner-update-timeline-1@ufl.edu", "Owner Timeline 1"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Timeline Rule 1",
        vote_count=0,
        is_published=False,
        created_at=now,
    )
    project.github_url = "https://github.com/example/timeline-rule-1"
    await db_session.flush()

    service = ProjectService(db_session)
    payload = ProjectUpdateRequest(timeline_end_date=date(2026, 4, 1))

    with pytest.raises(
        ProjectValidationError,
        match="timeline_end_date requires timeline_start_date.",
    ):
        await service.update_project(
            project_id=project.id,
            current_user_id=owner.id,
            payload=payload,
        )


@pytest.mark.asyncio
async def test_update_project_allows_clearing_timeline_end_for_in_progress(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(
        db_session, "owner-update-timeline-2@ufl.edu", "Owner Timeline 2"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Timeline Rule 2",
        vote_count=0,
        is_published=False,
        created_at=now,
    )
    project.github_url = "https://github.com/example/timeline-rule-2"
    project.timeline_start_date = date(2026, 3, 1)
    project.timeline_end_date = date(2026, 3, 31)
    await db_session.flush()

    service = ProjectService(db_session)
    payload = ProjectUpdateRequest(timeline_end_date=None)
    updated = await service.update_project(
        project_id=project.id,
        current_user_id=owner.id,
        payload=payload,
    )

    assert updated is not None
    assert updated.timeline_start_date == date(2026, 3, 1)
    assert updated.timeline_end_date is None

    refreshed_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = refreshed_result.one()
    assert refreshed.timeline_start_date == date(2026, 3, 1)
    assert refreshed.timeline_end_date is None


@pytest.mark.asyncio
async def test_update_project_returns_none_when_project_missing(db_session):
    service = ProjectService(db_session)
    owner = await _seed_user(db_session, "owner-update-4@ufl.edu", "Owner Update 4")
    payload = ProjectUpdateRequest(title="No Project")

    updated = await service.update_project(
        project_id=UUID("00000000-0000-0000-0000-000000000099"),
        current_user_id=owner.id,
        payload=payload,
    )

    assert updated is None


@pytest.mark.asyncio
async def test_update_project_rolls_back_when_commit_fails(db_session, monkeypatch):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(
        db_session, "owner-update-rollback@ufl.edu", "Owner Update Rollback"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Rollback Update Target",
        vote_count=0,
        is_published=False,
        created_at=now,
    )
    project.demo_url = "https://example.com/demo"
    await db_session.flush()

    service = ProjectService(db_session)
    payload = ProjectUpdateRequest(title="Updated Then Rollback")

    rollback_spy = AsyncMock(return_value=None)

    async def failing_commit():
        raise RuntimeError("db commit failed")

    monkeypatch.setattr(db_session, "commit", failing_commit)
    monkeypatch.setattr(db_session, "rollback", rollback_spy)

    with pytest.raises(RuntimeError, match="db commit failed"):
        await service.update_project(
            project_id=project.id,
            current_user_id=owner.id,
            payload=payload,
        )

    assert rollback_spy.await_count == 1


@pytest.mark.asyncio
async def test_publish_project_owner_can_publish_and_is_idempotent(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner-publish@ufl.edu", "Owner Publish")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Publish Target",
        vote_count=0,
        is_published=False,
        created_at=now,
    )
    project.github_url = "https://github.com/example/publish"
    await db_session.flush()

    service = ProjectService(db_session)
    first = await service.publish_project(
        project_id=project.id, current_user_id=owner.id
    )
    second = await service.publish_project(
        project_id=project.id, current_user_id=owner.id
    )

    assert first is not None
    assert second is not None
    assert first.is_published is True
    assert first.published_at is not None
    assert second.is_published is True
    assert second.published_at == first.published_at

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = project_result.one()
    assert refreshed.is_published is True
    assert refreshed.published_at == first.published_at


@pytest.mark.asyncio
async def test_publish_project_rejects_non_owner(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner-publish-2@ufl.edu", "Owner Publish 2")
    maintainer = await _seed_user(
        db_session, "maintainer-publish@ufl.edu", "Maintainer Publish"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Publish Forbidden",
        vote_count=0,
        is_published=False,
        created_at=now,
    )
    await _seed_member(
        db_session,
        project_id=project.id,
        user_id=maintainer.id,
        role="maintainer",
        added_at=now,
    )

    service = ProjectService(db_session)
    with pytest.raises(ProjectAccessForbiddenError, match="Project publish forbidden"):
        await service.publish_project(
            project_id=project.id, current_user_id=maintainer.id
        )


@pytest.mark.asyncio
async def test_unpublish_project_owner_can_unpublish_and_is_idempotent(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner-unpublish@ufl.edu", "Owner Unpublish")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unpublish Target",
        vote_count=0,
        is_published=True,
        created_at=now,
    )
    original_published_at = project.published_at

    service = ProjectService(db_session)
    first = await service.unpublish_project(
        project_id=project.id,
        current_user_id=owner.id,
    )
    second = await service.unpublish_project(
        project_id=project.id,
        current_user_id=owner.id,
    )

    assert first is not None
    assert second is not None
    assert first.is_published is False
    assert first.published_at is None
    assert second.is_published is False
    assert second.published_at is None
    assert original_published_at is not None

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    refreshed = project_result.one()
    assert refreshed.is_published is False
    assert refreshed.published_at is None


@pytest.mark.asyncio
async def test_unpublish_project_rejects_non_owner(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(
        db_session, "owner-unpublish-2@ufl.edu", "Owner Unpublish 2"
    )
    maintainer = await _seed_user(
        db_session, "maintainer-unpublish@ufl.edu", "Maintainer Unpublish"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unpublish Forbidden",
        vote_count=0,
        is_published=True,
        created_at=now,
    )
    await _seed_member(
        db_session,
        project_id=project.id,
        user_id=maintainer.id,
        role="maintainer",
        added_at=now,
    )

    service = ProjectService(db_session)
    with pytest.raises(
        ProjectAccessForbiddenError, match="Project unpublish forbidden"
    ):
        await service.unpublish_project(
            project_id=project.id,
            current_user_id=maintainer.id,
        )


@pytest.mark.asyncio
async def test_publish_then_unpublish_then_publish_sets_new_published_at(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(
        db_session, "owner-publish-republish@ufl.edu", "Owner Publish Republish"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Republish Timestamp",
        vote_count=0,
        is_published=True,
        created_at=now - timedelta(days=1),
    )
    original_published_at = project.published_at
    assert original_published_at is not None

    service = ProjectService(db_session)
    unpublished = await service.unpublish_project(
        project_id=project.id,
        current_user_id=owner.id,
    )
    assert unpublished is not None
    assert unpublished.is_published is False
    assert unpublished.published_at is None

    republished = await service.publish_project(
        project_id=project.id,
        current_user_id=owner.id,
    )
    assert republished is not None
    assert republished.is_published is True
    assert republished.published_at is not None
    assert republished.published_at > original_published_at
    assert republished.published_at != original_published_at


@pytest.mark.asyncio
async def test_publish_project_rolls_back_when_commit_fails(db_session, monkeypatch):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(
        db_session, "owner-publish-rollback@ufl.edu", "Owner Publish Rollback"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Publish Rollback Target",
        vote_count=0,
        is_published=False,
        created_at=now,
    )
    project.github_url = "https://github.com/example/publish-rollback"
    await db_session.flush()

    service = ProjectService(db_session)
    rollback_spy = AsyncMock(return_value=None)

    async def failing_commit():
        raise RuntimeError("db commit failed")

    monkeypatch.setattr(db_session, "commit", failing_commit)
    monkeypatch.setattr(db_session, "rollback", rollback_spy)

    with pytest.raises(RuntimeError, match="db commit failed"):
        await service.publish_project(project_id=project.id, current_user_id=owner.id)

    assert rollback_spy.await_count == 1


@pytest.mark.asyncio
async def test_publish_project_does_not_overwrite_published_at_after_race(
    db_session, monkeypatch
):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(
        db_session, "owner-publish-race@ufl.edu", "Owner Publish Race"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Publish Race Target",
        vote_count=0,
        is_published=False,
        created_at=now,
    )
    project.github_url = "https://github.com/example/publish-race"
    await db_session.flush()

    service = ProjectService(db_session)
    raced_published_at = now - timedelta(minutes=10)
    race_applied = False
    original_exec = db_session.exec

    async def exec_with_race(statement, *args, **kwargs):
        nonlocal race_applied
        table_name = getattr(getattr(statement, "table", None), "name", None)
        if (
            not race_applied
            and isinstance(statement, Update)
            and table_name == "projects"
        ):
            race_applied = True
            project.is_published = True
            project.published_at = raced_published_at
            await db_session.flush()
        return await original_exec(statement, *args, **kwargs)

    monkeypatch.setattr(db_session, "exec", exec_with_race)

    published = await service.publish_project(
        project_id=project.id, current_user_id=owner.id
    )
    assert race_applied is True
    assert published is not None
    assert published.is_published is True
    assert published.published_at == raced_published_at


@pytest.mark.asyncio
async def test_unpublish_project_rolls_back_when_commit_fails(db_session, monkeypatch):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(
        db_session, "owner-unpublish-rollback@ufl.edu", "Owner Unpublish Rollback"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Unpublish Rollback Target",
        vote_count=0,
        is_published=True,
        created_at=now,
    )

    service = ProjectService(db_session)
    rollback_spy = AsyncMock(return_value=None)

    async def failing_commit():
        raise RuntimeError("db commit failed")

    monkeypatch.setattr(db_session, "commit", failing_commit)
    monkeypatch.setattr(db_session, "rollback", rollback_spy)

    with pytest.raises(RuntimeError, match="db commit failed"):
        await service.unpublish_project(
            project_id=project.id,
            current_user_id=owner.id,
        )

    assert rollback_spy.await_count == 1


@pytest.mark.asyncio
async def test_soft_delete_project_marks_deleted_and_hides_detail_and_listings(
    db_session,
):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(db_session, "owner-soft-delete@ufl.edu", "Owner Delete")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Soft Delete Project",
        vote_count=25,
        is_published=True,
        created_at=now,
    )
    project.github_url = "https://github.com/example/soft-delete"
    await db_session.flush()

    service = ProjectService(db_session)

    deleted = await service.soft_delete_project(project.id, owner.id)
    assert deleted is True

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    stored_project = project_result.one()
    assert stored_project.deleted_at is not None

    assert await service.get_project_detail(project.id, None) is None

    listing = await service.list_projects(sort="new", limit=10)
    assert [item.id for item in listing.items] == []


@pytest.mark.asyncio
async def test_soft_delete_project_is_idempotent_for_owner(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(
        db_session, "owner-soft-delete-repeat@ufl.edu", "Owner Delete Repeat"
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Soft Delete Repeat Project",
        vote_count=3,
        is_published=True,
        created_at=now,
    )
    project.github_url = "https://github.com/example/soft-delete-repeat"
    await db_session.flush()

    service = ProjectService(db_session)

    assert await service.soft_delete_project(project.id, owner.id) is True
    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    first_deleted_at = project_result.one().deleted_at
    assert first_deleted_at is not None

    assert await service.soft_delete_project(project.id, owner.id) is True
    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    second_deleted_at = project_result.one().deleted_at
    assert second_deleted_at == first_deleted_at


@pytest.mark.asyncio
async def test_soft_delete_project_forbids_non_owner(db_session):
    now = datetime.now(timezone.utc)
    owner = await _seed_user(
        db_session, f"owner-soft-delete-forbid-{uuid4().hex[:8]}@ufl.edu", "Owner"
    )
    stranger = await _seed_user(
        db_session,
        f"stranger-soft-delete-forbid-{uuid4().hex[:8]}@ufl.edu",
        "Stranger",
    )
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Soft Delete Forbidden Project",
        vote_count=4,
        is_published=True,
        created_at=now,
    )
    project.github_url = "https://github.com/example/soft-delete-forbidden"
    await db_session.flush()

    service = ProjectService(db_session)

    with pytest.raises(ProjectAccessForbiddenError):
        await service.soft_delete_project(project.id, stranger.id)

    project_result = await db_session.exec(
        select(Project).where(Project.id == project.id)
    )
    assert project_result.one().deleted_at is None
