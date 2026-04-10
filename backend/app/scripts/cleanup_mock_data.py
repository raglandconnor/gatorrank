"""Dev-only cleanup utility for mock seed data.

Deletes only rows associated with seeded mock identifiers:
- users.email LIKE 'mock_user_%@<domain>'
- projects.created_by_id in mock user ids (plus legacy '[MOCK] title fallback)

Usage:
  PYTHONPATH=. uv run python app/scripts/cleanup_mock_data.py --yes
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from urllib.parse import urlparse
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import delete
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.db.database import AsyncSessionLocal
from app.models.auth import RefreshSession
from app.models.project import Project, ProjectMember, Vote
from app.models.taxonomy import ProjectCategory, ProjectTag, ProjectTechStack
from app.models.user import User


@dataclass
class CleanupCounts:
    votes: int = 0
    project_members: int = 0
    project_categories: int = 0
    project_tags: int = 0
    project_tech_stacks: int = 0
    projects: int = 0
    refresh_sessions: int = 0
    users: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Delete mock seed data (dev-only).")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required confirmation flag to execute deletions.",
    )
    parser.add_argument(
        "--email-domain",
        default="ufl.edu",
        help="Domain used by mock users (default: ufl.edu).",
    )
    parser.add_argument(
        "--allow-non-local",
        action="store_true",
        help=(
            "Allow execution when DATABASE_URL host is not localhost/127.0.0.1. "
            "Use only for dedicated dev databases."
        ),
    )
    return parser.parse_args()


def _database_host() -> str:
    settings = get_settings()
    parsed = urlparse(settings.DATABASE_URL)
    return parsed.hostname or ""


def enforce_dev_guardrails(*, allow_non_local: bool, confirmed: bool) -> None:
    if not confirmed:
        raise SystemExit("Refusing to run without --yes")

    host = _database_host().lower()
    if host in {"localhost", "127.0.0.1"}:
        return

    if not allow_non_local:
        raise SystemExit(
            "Refusing to run on non-local database host without --allow-non-local"
        )


async def _fetch_mock_user_ids(
    session: AsyncSession,
    *,
    email_domain: str,
) -> list[UUID]:
    pattern = f"mock_user_%@{email_domain.lower()}"
    user_cols = getattr(User, "__table__").c
    users_result = await session.exec(
        select(User).where(sa.func.lower(user_cols.email).like(pattern))
    )
    return [user.id for user in users_result.all()]


async def _fetch_mock_project_ids(
    session: AsyncSession,
    *,
    mock_user_ids: list[UUID],
) -> list[UUID]:
    # Primary match: projects owned by mock users.
    # Fallback: legacy project titles that previously used '[MOCK] ...'.
    project_title_pattern = "[MOCK] %"
    project_cols = getattr(Project, "__table__").c

    project_filters: list[sa.ColumnElement[bool]] = [
        project_cols.title.like(project_title_pattern)
    ]
    if mock_user_ids:
        project_filters.append(project_cols.created_by_id.in_(mock_user_ids))

    projects_result = await session.exec(
        select(Project).where(sa.or_(*project_filters))
    )
    return [project.id for project in projects_result.all()]


async def cleanup_mock_data(*, email_domain: str) -> CleanupCounts:
    counts = CleanupCounts()

    async with AsyncSessionLocal() as session:
        vote_cols = getattr(Vote, "__table__").c
        project_member_cols = getattr(ProjectMember, "__table__").c
        project_cols = getattr(Project, "__table__").c
        refresh_session_cols = getattr(RefreshSession, "__table__").c
        user_cols = getattr(User, "__table__").c
        project_category_cols = getattr(ProjectCategory, "__table__").c
        project_tag_cols = getattr(ProjectTag, "__table__").c
        project_tech_stack_cols = getattr(ProjectTechStack, "__table__").c

        user_ids = await _fetch_mock_user_ids(session, email_domain=email_domain)
        project_ids = await _fetch_mock_project_ids(session, mock_user_ids=user_ids)

        vote_filters: list[sa.ColumnElement[bool]] = []
        if user_ids:
            vote_filters.append(vote_cols.user_id.in_(user_ids))
        if project_ids:
            vote_filters.append(vote_cols.project_id.in_(project_ids))
        if vote_filters:
            vote_result = await session.exec(delete(Vote).where(sa.or_(*vote_filters)))
            counts.votes = vote_result.rowcount or 0

        member_filters: list[sa.ColumnElement[bool]] = []
        if user_ids:
            member_filters.append(project_member_cols.user_id.in_(user_ids))
        if project_ids:
            member_filters.append(project_member_cols.project_id.in_(project_ids))
        if member_filters:
            member_result = await session.exec(
                delete(ProjectMember).where(sa.or_(*member_filters))
            )
            counts.project_members = member_result.rowcount or 0

        if project_ids:
            categories_result = await session.exec(
                delete(ProjectCategory).where(
                    project_category_cols.project_id.in_(project_ids)
                )
            )
            counts.project_categories = categories_result.rowcount or 0
            tags_result = await session.exec(
                delete(ProjectTag).where(project_tag_cols.project_id.in_(project_ids))
            )
            counts.project_tags = tags_result.rowcount or 0
            tech_stacks_result = await session.exec(
                delete(ProjectTechStack).where(
                    project_tech_stack_cols.project_id.in_(project_ids)
                )
            )
            counts.project_tech_stacks = tech_stacks_result.rowcount or 0

        if project_ids:
            projects_result = await session.exec(
                delete(Project).where(project_cols.id.in_(project_ids))
            )
            counts.projects = projects_result.rowcount or 0

        if user_ids:
            sessions_result = await session.exec(
                delete(RefreshSession).where(refresh_session_cols.user_id.in_(user_ids))
            )
            counts.refresh_sessions = sessions_result.rowcount or 0

            users_result = await session.exec(
                delete(User).where(user_cols.id.in_(user_ids))
            )
            counts.users = users_result.rowcount or 0

        await session.commit()

    return counts


async def main() -> None:
    args = parse_args()
    enforce_dev_guardrails(
        allow_non_local=args.allow_non_local,
        confirmed=args.yes,
    )

    counts = await cleanup_mock_data(email_domain=args.email_domain)

    print("Mock cleanup complete")
    print(f"- votes: {counts.votes}")
    print(f"- project_members: {counts.project_members}")
    print(f"- project_categories: {counts.project_categories}")
    print(f"- project_tags: {counts.project_tags}")
    print(f"- project_tech_stacks: {counts.project_tech_stacks}")
    print(f"- projects: {counts.projects}")
    print(f"- refresh_sessions: {counts.refresh_sessions}")
    print(f"- users: {counts.users}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
