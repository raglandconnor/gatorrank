from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.models.project import Project, ProjectMember
from app.models.user import User
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
