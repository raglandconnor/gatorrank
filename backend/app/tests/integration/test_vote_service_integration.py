import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.project import Project, Vote
from app.models.user import User
from app.services.vote import VoteService, VoteTargetNotFoundError
from app.utils.pagination import CursorError


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
    vote_count: int = 0,
    is_published: bool = True,
    created_at: datetime | None = None,
) -> Project:
    now = created_at or datetime.now(timezone.utc)
    project = Project(
        created_by_id=created_by_id,
        title=title,
        short_description=f"{title} description",
        vote_count=vote_count,
        is_group_project=False,
        is_published=is_published,
        published_at=now if is_published else None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(project)
    await db_session.flush()
    return project


@pytest.mark.asyncio
async def test_add_vote_creates_vote_and_increments_count(db_session):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"vote-owner-{unique}@ufl.edu", "Owner")
    voter = await _seed_user(db_session, f"vote-voter-{unique}@ufl.edu", "Voter")
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="Vote Target"
    )

    service = VoteService(db_session)
    added = await service.add_vote(project_id=project.id, user_id=voter.id)

    assert added is True
    refreshed = await db_session.exec(select(Project).where(Project.id == project.id))
    updated_project = refreshed.one()
    assert updated_project.vote_count == 1

    vote_result = await db_session.exec(
        select(Vote).where(Vote.project_id == project.id, Vote.user_id == voter.id)
    )
    assert vote_result.one_or_none() is not None


@pytest.mark.asyncio
async def test_add_vote_duplicate_is_idempotent_and_does_not_increment_twice(
    db_session,
):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"vote-owner2-{unique}@ufl.edu", "Owner")
    voter = await _seed_user(db_session, f"vote-voter2-{unique}@ufl.edu", "Voter")
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="Duplicate Vote Target"
    )
    project_id = project.id
    service = VoteService(db_session)

    first_add = await service.add_vote(project_id=project_id, user_id=voter.id)
    second_add = await service.add_vote(project_id=project_id, user_id=voter.id)

    assert first_add is True
    assert second_add is False
    refreshed = await db_session.exec(select(Project).where(Project.id == project_id))
    updated_project = refreshed.one()
    assert updated_project.vote_count == 1


@pytest.mark.asyncio
async def test_add_vote_rejects_draft_project(db_session):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"vote-owner3-{unique}@ufl.edu", "Owner")
    voter = await _seed_user(db_session, f"vote-voter3-{unique}@ufl.edu", "Voter")
    draft = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Draft Target",
        is_published=False,
    )

    service = VoteService(db_session)
    with pytest.raises(VoteTargetNotFoundError, match="Project not found"):
        await service.add_vote(project_id=draft.id, user_id=voter.id)


@pytest.mark.asyncio
async def test_remove_vote_is_idempotent_and_never_goes_negative(db_session):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"vote-owner4-{unique}@ufl.edu", "Owner")
    voter = await _seed_user(db_session, f"vote-voter4-{unique}@ufl.edu", "Voter")
    project = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Remove Vote Target",
    )
    service = VoteService(db_session)
    await service.add_vote(project_id=project.id, user_id=voter.id)

    removed = await service.remove_vote(project_id=project.id, user_id=voter.id)
    removed_again = await service.remove_vote(project_id=project.id, user_id=voter.id)

    assert removed is True
    assert removed_again is False
    refreshed = await db_session.exec(select(Project).where(Project.id == project.id))
    updated_project = refreshed.one()
    assert updated_project.vote_count == 0


@pytest.mark.asyncio
async def test_list_my_voted_projects_orders_and_paginates(db_session):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"vote-owner5-{unique}@ufl.edu", "Owner")
    voter = await _seed_user(db_session, f"vote-voter5-{unique}@ufl.edu", "Voter")

    now = datetime.now(timezone.utc)
    oldest = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Oldest",
        created_at=now - timedelta(days=3),
    )
    middle = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Middle",
        created_at=now - timedelta(days=2),
    )
    newest = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Newest",
        created_at=now - timedelta(days=1),
    )
    draft = await _seed_project(
        db_session,
        created_by_id=owner.id,
        title="Hidden Draft",
        is_published=False,
    )
    service = VoteService(db_session)
    await service.add_vote(project_id=oldest.id, user_id=voter.id)
    await service.add_vote(project_id=middle.id, user_id=voter.id)
    await service.add_vote(project_id=newest.id, user_id=voter.id)
    now = datetime.now(timezone.utc)
    vote_cols = getattr(Vote, "__table__").c
    await db_session.exec(
        update(Vote)
        .where(vote_cols.project_id == oldest.id, vote_cols.user_id == voter.id)
        .values(created_at=now - timedelta(minutes=3))
    )
    await db_session.exec(
        update(Vote)
        .where(vote_cols.project_id == middle.id, vote_cols.user_id == voter.id)
        .values(created_at=now - timedelta(minutes=2))
    )
    await db_session.exec(
        update(Vote)
        .where(vote_cols.project_id == newest.id, vote_cols.user_id == voter.id)
        .values(created_at=now - timedelta(minutes=1))
    )
    await db_session.commit()

    # This should fail since drafts are ineligible vote targets.
    with pytest.raises(VoteTargetNotFoundError):
        await service.add_vote(project_id=draft.id, user_id=voter.id)

    first_page = await service.list_my_voted_projects(user_id=voter.id, limit=2)
    assert [item.id for item in first_page.items] == [newest.id, middle.id]
    assert first_page.next_cursor is not None

    second_page = await service.list_my_voted_projects(
        user_id=voter.id,
        limit=2,
        cursor=first_page.next_cursor,
    )
    assert [item.id for item in second_page.items] == [oldest.id]
    assert second_page.next_cursor is None


@pytest.mark.asyncio
async def test_list_my_voted_projects_invalid_cursor_raises(db_session):
    unique = uuid4().hex[:8]
    owner = await _seed_user(db_session, f"vote-owner6-{unique}@ufl.edu", "Owner")
    voter = await _seed_user(db_session, f"vote-voter6-{unique}@ufl.edu", "Voter")
    project = await _seed_project(
        db_session, created_by_id=owner.id, title="Cursor Target"
    )
    service = VoteService(db_session)
    await service.add_vote(project_id=project.id, user_id=voter.id)

    with pytest.raises(CursorError, match="Invalid cursor"):
        await service.list_my_voted_projects(user_id=voter.id, cursor="bad-cursor")


@pytest.mark.asyncio
async def test_add_vote_concurrent_duplicate_requests_one_effective_vote(
    async_engine: AsyncEngine,
):
    unique = uuid4().hex[:8]
    owner_email = f"vote-owner-race-{unique}@ufl.edu"
    voter_email = f"vote-voter-race-{unique}@ufl.edu"

    async with AsyncSession(async_engine, expire_on_commit=False) as seed_session:
        owner = await _seed_user(seed_session, owner_email, "Owner")
        voter = await _seed_user(seed_session, voter_email, "Voter")
        project = await _seed_project(
            seed_session,
            created_by_id=owner.id,
            title=f"Vote Race {unique}",
        )
        await seed_session.commit()
        voter_id = voter.id
        project_id = project.id

    async def attempt_vote() -> bool:
        async with AsyncSession(async_engine, expire_on_commit=False) as session:
            service = VoteService(session)
            return await service.add_vote(project_id=project_id, user_id=voter_id)

    first, second = await asyncio.gather(attempt_vote(), attempt_vote())
    assert sorted([first, second]) == [False, True]

    async with AsyncSession(async_engine, expire_on_commit=False) as verify_session:
        project_result = await verify_session.exec(
            select(Project).where(Project.id == project_id)
        )
        updated_project = project_result.one()
        assert updated_project.vote_count == 1

        votes_result = await verify_session.exec(
            select(Vote).where(Vote.project_id == project_id, Vote.user_id == voter_id)
        )
        all_votes = votes_result.all()
        assert len(all_votes) == 1
