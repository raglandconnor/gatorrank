"""Seed frontend-realistic mock data directly in the database (dev-only).

Usage:
  PYTHONPATH=. uv run python app/scripts/seed_mock_data.py
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import delete
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import AsyncSessionLocal
from app.models.auth import RefreshSession
from app.models.project import Project, ProjectMember, Vote
from app.models.user import User
from app.services.auth import AuthService


@dataclass
class SeedConfig:
    email_domain: str
    mock_password: str
    total_users: int
    total_projects: int
    published_projects: int
    group_projects: int
    total_votes: int
    random_seed: int
    reset_mock: bool


def log(message: str) -> None:
    print(message, flush=True)


def parse_args() -> SeedConfig:
    parser = argparse.ArgumentParser(
        description="Seed mock database data for local frontend/dev workflows."
    )
    parser.add_argument("--email-domain", default="ufl.edu")
    parser.add_argument("--mock-password", default="mock-password-12345")
    parser.add_argument("--total-users", type=int, default=24)
    parser.add_argument("--total-projects", type=int, default=36)
    parser.add_argument("--published-projects", type=int, default=30)
    parser.add_argument("--group-projects", type=int, default=12)
    parser.add_argument("--total-votes", type=int, default=140)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument(
        "--reset-mock",
        action="store_true",
        help="Delete existing mock-scoped rows first, then reseed.",
    )
    args = parser.parse_args()

    if args.total_users <= 0:
        raise SystemExit("--total-users must be > 0")
    if args.total_projects <= 0:
        raise SystemExit("--total-projects must be > 0")
    if args.published_projects < 0 or args.published_projects > args.total_projects:
        raise SystemExit("--published-projects must be within [0, total-projects]")
    if args.group_projects < 0 or args.group_projects > args.total_projects:
        raise SystemExit("--group-projects must be within [0, total-projects]")
    if args.total_votes < 0:
        raise SystemExit("--total-votes must be >= 0")

    return SeedConfig(
        email_domain=args.email_domain,
        mock_password=args.mock_password,
        total_users=args.total_users,
        total_projects=args.total_projects,
        published_projects=args.published_projects,
        group_projects=args.group_projects,
        total_votes=args.total_votes,
        random_seed=args.random_seed,
        reset_mock=args.reset_mock,
    )


def email_for_index(index: int, domain: str) -> str:
    return f"mock_user_{index:03d}@{domain}".lower()


def username_for_index(index: int) -> str:
    return f"mock_user_{index:03d}"


def _lorem_sentence(rng: random.Random, min_words: int = 8, max_words: int = 18) -> str:
    words = [
        "lorem",
        "ipsum",
        "dolor",
        "sit",
        "amet",
        "consectetur",
        "adipiscing",
        "elit",
        "integer",
        "facilisis",
        "turpis",
        "sed",
        "ultrices",
        "mattis",
        "vehicula",
        "egestas",
        "aliquam",
        "commodo",
        "phasellus",
        "lectus",
        "dictum",
        "fringilla",
        "condimentum",
        "tristique",
        "porta",
        "viverra",
        "gravida",
        "suscipit",
        "vulputate",
        "elementum",
    ]
    count = rng.randint(min_words, max_words)
    chosen = [rng.choice(words) for _ in range(count)]
    sentence = " ".join(chosen)
    return sentence.capitalize() + "."


def _lorem_paragraph(
    rng: random.Random, min_sentences: int = 2, max_sentences: int = 4
) -> str:
    sentence_count = rng.randint(min_sentences, max_sentences)
    return " ".join(_lorem_sentence(rng) for _ in range(sentence_count))


def full_name_for_index(index: int, rng: random.Random) -> str:
    first_names = [
        "Avery",
        "Jordan",
        "Taylor",
        "Parker",
        "Riley",
        "Casey",
        "Morgan",
        "Reese",
        "Quinn",
        "Cameron",
        "Skyler",
        "Elliot",
    ]
    last_names = [
        "Nguyen",
        "Patel",
        "Hernandez",
        "Kim",
        "Martinez",
        "Johnson",
        "Williams",
        "Thompson",
        "Garcia",
        "Davis",
        "Allen",
        "Rivera",
    ]
    first = first_names[(index - 1) % len(first_names)]
    last = last_names[(rng.randint(0, 999) + index) % len(last_names)]
    return f"{first} {last}"


def project_title_for_index(index: int) -> str:
    words = [
        "lorem",
        "ipsum",
        "dolor",
        "sit",
        "amet",
        "consectetur",
        "adipiscing",
        "elit",
        "integer",
        "facilisis",
        "turpis",
        "ultrices",
        "mattis",
        "vehicula",
        "egestas",
        "aliquam",
        "commodo",
        "phasellus",
        "dictum",
        "fringilla",
        "gravida",
        "suscipit",
        "vulputate",
        "elementum",
    ]
    # Deterministic mixed-radix mapping keeps titles stable and avoids collisions
    # for realistic seed sizes while staying in the requested 1-5 word range.
    word_count = 1 + ((index - 1) % 5)
    value = index - 1
    chosen: list[str] = []
    for offset in range(word_count):
        base = len(words) ** offset
        word_index = (value // base) % len(words)
        chosen.append(words[word_index])
    title = " ".join(word.capitalize() for word in chosen)
    if len(title) > 50:
        title = title[:50].rstrip()
    return title


def project_short_description(index: int, rng: random.Random) -> str:
    starts = [
        "A focused platform that helps teams",
        "A lightweight tool that lets students",
        "An integrated experience designed to",
        "A practical app that supports",
        "A collaboration surface that enables",
    ]
    endings = [
        "plan milestones and share updates quickly.",
        "organize tasks and ship faster with less friction.",
        "track progress, feedback, and outcomes in one place.",
        "coordinate delivery while keeping communication clear.",
        "prototype ideas and validate them with real users.",
    ]
    start = starts[(index - 1) % len(starts)]
    end = endings[(rng.randint(0, 999) + index) % len(endings)]
    sentence = f"{start} {end}"
    if len(sentence) > 280:
        sentence = sentence[:277] + "..."
    return sentence


def project_long_description(index: int, rng: random.Random) -> str:
    p1 = _lorem_paragraph(rng)
    p2 = _lorem_paragraph(rng)
    return (
        f"Project {index:03d} explores a realistic product direction for student builders. "
        f"{p1}\n\n{p2}"
    )


def project_urls(index: int) -> tuple[str | None, str | None, str | None]:
    demo = f"https://demo.gatorrank.mock/project-{index}"
    github = f"https://github.com/gatorrank/mock-project-{index}"
    video = "https://www.youtube.com/watch?v=ZeP6Y8xd644"

    mode = index % 5
    if mode == 0:
        return demo, github, video
    if mode == 1:
        return demo, github, video
    if mode == 2:
        return demo, None, video
    if mode == 3:
        return None, github, video
    return None, github, video


def project_timeline(index: int, now_date: date) -> tuple[date | None, date | None]:
    mode = index % 3
    if mode == 0:
        return None, None
    start = now_date - timedelta(days=120 + index)
    if mode == 1:
        end = start + timedelta(days=60 + (index % 45))
        return start, end
    return start, None


async def reset_mock_data(session: AsyncSession, *, email_domain: str) -> None:
    user_cols = getattr(User, "__table__").c
    project_cols = getattr(Project, "__table__").c
    vote_cols = getattr(Vote, "__table__").c
    member_cols = getattr(ProjectMember, "__table__").c
    refresh_session_cols = getattr(RefreshSession, "__table__").c

    email_pattern = f"mock_user_%@{email_domain.lower()}"

    users_result = await session.exec(
        select(User).where(sa.func.lower(user_cols.email).like(email_pattern))
    )
    mock_users = users_result.all()
    user_ids = [u.id for u in mock_users]

    project_filters: list[sa.ColumnElement[bool]] = [
        project_cols.title.like("[MOCK] %")
    ]
    if user_ids:
        project_filters.append(project_cols.created_by_id.in_(user_ids))
    projects_result = await session.exec(
        select(Project).where(sa.or_(*project_filters))
    )
    mock_projects = projects_result.all()
    project_ids = [p.id for p in mock_projects]

    if user_ids or project_ids:
        vote_filters: list[sa.ColumnElement[bool]] = []
        member_filters: list[sa.ColumnElement[bool]] = []
        if user_ids:
            vote_filters.append(vote_cols.user_id.in_(user_ids))
            member_filters.append(member_cols.user_id.in_(user_ids))
        if project_ids:
            vote_filters.append(vote_cols.project_id.in_(project_ids))
            member_filters.append(member_cols.project_id.in_(project_ids))

        if vote_filters:
            await session.exec(delete(Vote).where(sa.or_(*vote_filters)))
        if member_filters:
            await session.exec(delete(ProjectMember).where(sa.or_(*member_filters)))
        if project_ids:
            await session.exec(delete(Project).where(project_cols.id.in_(project_ids)))
        if user_ids:
            await session.exec(
                delete(RefreshSession).where(refresh_session_cols.user_id.in_(user_ids))
            )
            await session.exec(delete(User).where(user_cols.id.in_(user_ids)))


async def get_or_create_mock_user(
    session: AsyncSession,
    *,
    index: int,
    email_domain: str,
    password_hash: str,
    rng: random.Random,
) -> User:
    user_cols = getattr(User, "__table__").c
    email = email_for_index(index, email_domain)

    result = await session.exec(
        select(User).where(sa.func.lower(user_cols.email) == email)
    )
    existing = result.first()
    if existing is not None:
        existing.username = username_for_index(index)
        existing.full_name = full_name_for_index(index, rng)
        existing.profile_picture_url = f"https://avatar.gatorrank.mock/user-{index}.png"
        session.add(existing)
        return existing

    user = User(  # pyright: ignore[reportCallIssue]
        email=email,
        username=username_for_index(index),
        password_hash=password_hash,
        role="student",
        full_name=full_name_for_index(index, rng),
        profile_picture_url=f"https://avatar.gatorrank.mock/user-{index}.png",
    )
    session.add(user)
    await session.flush()
    return user


async def get_or_create_project(
    session: AsyncSession,
    *,
    index: int,
    owner_user_id: UUID,
    rng: random.Random,
    is_published: bool,
    now: datetime,
) -> Project:
    project_cols = getattr(Project, "__table__").c
    title = project_title_for_index(index)

    result = await session.exec(select(Project).where(project_cols.title == title))
    existing = result.first()

    demo_url, github_url, video_url = project_urls(index)
    timeline_start, timeline_end = project_timeline(index, now.date())

    if existing is None:
        project = Project(  # pyright: ignore[reportCallIssue]
            created_by_id=owner_user_id,
            title=title,
            short_description=project_short_description(index, rng),
            long_description=project_long_description(index, rng),
            demo_url=demo_url,
            github_url=github_url,
            video_url=video_url,
            timeline_start_date=timeline_start,
            timeline_end_date=timeline_end,
            vote_count=0,
            is_group_project=False,
            is_published=is_published,
            published_at=(now - timedelta(days=index)) if is_published else None,
        )
        session.add(project)
        await session.flush()
        return project

    existing.created_by_id = owner_user_id
    existing.short_description = project_short_description(index, rng)
    existing.long_description = project_long_description(index, rng)
    existing.demo_url = demo_url
    existing.github_url = github_url
    existing.video_url = video_url
    existing.timeline_start_date = timeline_start
    existing.timeline_end_date = timeline_end
    existing.is_published = is_published
    if is_published:
        existing.published_at = existing.published_at or (now - timedelta(days=index))
    else:
        existing.published_at = None
    session.add(existing)
    return existing


async def ensure_owner_membership(
    session: AsyncSession,
    *,
    project_id: UUID,
    owner_user_id: UUID,
) -> None:
    member_cols = getattr(ProjectMember, "__table__").c
    result = await session.exec(
        select(ProjectMember).where(
            member_cols.project_id == project_id,
            member_cols.user_id == owner_user_id,
        )
    )
    member = result.first()
    if member is None:
        member = ProjectMember(  # pyright: ignore[reportCallIssue]
            project_id=project_id,
            user_id=owner_user_id,
            role="owner",
        )
        session.add(member)
        return

    member.role = "owner"
    session.add(member)


async def upsert_collaborators(
    session: AsyncSession,
    *,
    project: Project,
    all_users: list[User],
    owner_index: int,
    project_index: int,
    rng: random.Random,
) -> None:
    member_cols = getattr(ProjectMember, "__table__").c

    extra_count = 1 + (project_index % 4)
    target_user_ids: list[UUID] = []
    while len(target_user_ids) < extra_count:
        offset = 1 + rng.randint(0, len(all_users) - 2)
        candidate = all_users[(owner_index + offset) % len(all_users)]
        if candidate.id == project.created_by_id:
            continue
        if candidate.id in target_user_ids:
            continue
        target_user_ids.append(candidate.id)

    existing_members_result = await session.exec(
        select(ProjectMember).where(member_cols.project_id == project.id)
    )
    existing_members = existing_members_result.all()

    existing_by_user: dict[UUID, ProjectMember] = {
        member.user_id: member for member in existing_members
    }

    for idx, user_id in enumerate(target_user_ids):
        role = "maintainer" if idx == 0 else "contributor"
        member = existing_by_user.get(user_id)
        if member is None:
            session.add(
                ProjectMember(  # pyright: ignore[reportCallIssue]
                    project_id=project.id,
                    user_id=user_id,
                    role=role,
                )
            )
        else:
            member.role = role
            session.add(member)


def _target_vote_counts(
    *,
    total_votes: int,
    published_project_ids: list[UUID],
) -> dict[UUID, int]:
    counts = {project_id: 0 for project_id in published_project_ids}
    if not published_project_ids or total_votes <= 0:
        return counts

    for idx in range(total_votes):
        bucket = (idx * 11 + (idx // 7)) % len(published_project_ids)
        if idx % 3 == 0:
            bucket = bucket // 2
        counts[published_project_ids[bucket]] += 1

    return counts


async def apply_votes(
    session: AsyncSession,
    *,
    users: list[User],
    projects: list[Project],
    published_projects: int,
    total_votes: int,
) -> None:
    vote_cols = getattr(Vote, "__table__").c

    mock_user_ids = [u.id for u in users]
    published_project_ids = [project.id for project in projects[:published_projects]]

    if mock_user_ids and published_project_ids:
        await session.exec(
            delete(Vote).where(
                vote_cols.user_id.in_(mock_user_ids),
                vote_cols.project_id.in_(published_project_ids),
            )
        )

    target_counts = _target_vote_counts(
        total_votes=total_votes,
        published_project_ids=published_project_ids,
    )

    for project_idx, project in enumerate(projects[:published_projects], start=1):
        target = target_counts[project.id]
        voter_order: list[User] = []
        for i in range(len(users)):
            voter_order.append(users[(project_idx * 3 + i * 5) % len(users)])

        unique_voters = voter_order[: min(target, len(voter_order))]
        for voter in unique_voters:
            session.add(
                Vote(  # pyright: ignore[reportCallIssue]
                    user_id=voter.id,
                    project_id=project.id,
                )
            )

    await session.flush()

    for project in projects:
        if not project.is_published:
            project.vote_count = 0
            session.add(project)
            continue

        count_result = await session.exec(
            select(sa.func.count())
            .select_from(Vote)
            .where(vote_cols.project_id == project.id)
        )
        vote_count = int(count_result.one())
        project.vote_count = vote_count
        session.add(project)

        member_count_result = await session.exec(
            select(sa.func.count())
            .select_from(ProjectMember)
            .where(getattr(ProjectMember, "__table__").c.project_id == project.id)
        )
        member_count = int(member_count_result.one())
        project.is_group_project = member_count > 1
        session.add(project)

    published_ids = {p.id for p in projects[:published_projects]}
    for project in projects[published_projects:]:
        if project.id in published_ids:
            continue
        project.vote_count = 0
        project.is_published = False
        project.published_at = None
        session.add(project)


async def seed_mock_data(cfg: SeedConfig) -> None:
    rng = random.Random(cfg.random_seed)
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as session:
        if cfg.reset_mock:
            log("Resetting existing mock-scoped rows...")
            await reset_mock_data(session, email_domain=cfg.email_domain)
            await session.commit()

        auth_service = AuthService(session)
        password_hash = auth_service.hash_password(cfg.mock_password)

        log(f"Seeding {cfg.total_users} users...")
        users: list[User] = []
        for i in range(1, cfg.total_users + 1):
            user = await get_or_create_mock_user(
                session,
                index=i,
                email_domain=cfg.email_domain,
                password_hash=password_hash,
                rng=rng,
            )
            users.append(user)
            log(f"  users: {i}/{cfg.total_users}")

        log(
            f"Seeding {cfg.total_projects} projects "
            f"({cfg.published_projects} published)..."
        )
        projects: list[Project] = []
        for i in range(1, cfg.total_projects + 1):
            owner_index = (i - 1) % cfg.total_users
            owner = users[owner_index]
            project = await get_or_create_project(
                session,
                index=i,
                owner_user_id=owner.id,
                rng=rng,
                is_published=i <= cfg.published_projects,
                now=now,
            )
            projects.append(project)
            await ensure_owner_membership(
                session,
                project_id=project.id,
                owner_user_id=owner.id,
            )
            log(f"  projects: {i}/{cfg.total_projects}")

        log(f"Adding collaborators to {cfg.group_projects} projects...")
        for i in range(1, cfg.group_projects + 1):
            project_index = i - 1
            owner_index = project_index % cfg.total_users
            await upsert_collaborators(
                session,
                project=projects[project_index],
                all_users=users,
                owner_index=owner_index,
                project_index=i,
                rng=rng,
            )
            log(f"  collaborator projects: {i}/{cfg.group_projects}")

        log(f"Applying {cfg.total_votes} votes across published projects...")
        await apply_votes(
            session,
            users=users,
            projects=projects,
            published_projects=cfg.published_projects,
            total_votes=cfg.total_votes,
        )
        for i in range(1, cfg.total_votes + 1):
            log(f"  votes: {i}/{cfg.total_votes}")

        await session.commit()

    log("Seed complete")
    log(f"- Users: {cfg.total_users}")
    log(
        f"- Projects: {cfg.total_projects} "
        f"({cfg.published_projects} published, {cfg.total_projects - cfg.published_projects} drafts)"
    )
    log(f"- Group projects: {cfg.group_projects}")
    log(f"- Votes targeted: {cfg.total_votes}")


def main() -> None:
    cfg = parse_args()
    import asyncio

    asyncio.run(seed_mock_data(cfg))


if __name__ == "__main__":
    main()
