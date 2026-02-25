from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from sqlmodel import select

from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.project import ProjectCreateRequest
from app.services.project import ProjectAccessForbiddenError, ProjectService


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
    vote_count: int,
    is_published: bool,
    created_at: datetime,
) -> Project:
    project = Project(
        created_by_id=created_by_id,
        title=title,
        description=f"{title} description",
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

    listing = await service.list_projects(sort="top", limit=10)
    listed = next((item for item in listing.items if item.id == project.id), None)
    assert listed is not None
    assert [m.user_id for m in listed.members] == [member_a.id, member_b.id]


@pytest.mark.asyncio
async def test_create_project_creates_draft_and_owner_membership_and_returns_detail(
    db_session,
):
    creator = await _seed_user(db_session, "creator@ufl.edu", "Creator")
    service = ProjectService(db_session)
    payload = ProjectCreateRequest(
        title="  Build GatorRank  ",
        description="  A project for ranking UF projects  ",
        github_url="https://github.com/example/gatorrank",
    )

    created = await service.create_project(created_by_id=creator.id, payload=payload)

    assert created.created_by_id == creator.id
    assert created.title == "Build GatorRank"
    assert created.description == "A project for ranking UF projects"
    assert created.is_published is False
    assert created.published_at is None
    assert created.vote_count == 0
    assert created.members
    assert created.members[0].user_id == creator.id
    assert created.members[0].role == "owner"

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
async def test_create_project_defaults_group_flag_and_persists_optional_urls(
    db_session,
):
    creator = await _seed_user(db_session, "creator2@ufl.edu", "Creator Two")
    service = ProjectService(db_session)
    payload = ProjectCreateRequest(
        title="Project URLs",
        description="Testing URL persistence",
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
        description="Normalization coverage",
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
        description="Rollback coverage",
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
