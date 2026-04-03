from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.project import Project, Vote
from app.schemas.project import ProjectListItemResponse, ProjectListResponse
from app.services.project_members import get_members_for_projects
from app.utils.pagination import (
    CursorError,
    decode_cursor_payload,
    encode_cursor_payload,
)

VOTE_SORT_RECENT = "recent_votes"


class VoteTargetNotFoundError(LookupError):
    """Raised when vote target project is missing or not eligible for voting."""


class VoteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_vote(self, *, project_id: UUID, user_id: UUID) -> bool:
        """Add a vote if absent. Returns True when a new vote is created."""
        project = await self._get_vote_target_project(project_id)
        if project is None:
            raise VoteTargetNotFoundError("Project not found")

        vote_cols = getattr(Vote, "__table__").c
        insert_statement = (
            pg_insert(Vote)
            .values(user_id=user_id, project_id=project_id)
            .on_conflict_do_nothing(index_elements=["user_id", "project_id"])
            .returning(vote_cols.id)
        )
        try:
            inserted_vote_id = (await self.db.exec(insert_statement)).one_or_none()
            if inserted_vote_id is None:
                await self.db.commit()
                return False

            await self._increment_vote_count(project_id)
            await self.db.commit()
            return True
        except Exception:
            await self.db.rollback()
            raise

    async def remove_vote(self, *, project_id: UUID, user_id: UUID) -> bool:
        """Remove a vote if present. Returns True when an existing vote is removed."""
        project = await self._get_vote_target_project(project_id)
        if project is None:
            raise VoteTargetNotFoundError("Project not found")

        vote_cols = getattr(Vote, "__table__").c
        delete_stmt = (
            delete(Vote)
            .where(
                vote_cols.project_id == project_id,
                vote_cols.user_id == user_id,
            )
            .returning(vote_cols.id)
        )

        try:
            result = await self.db.exec(delete_stmt)
            removed_vote_id = result.one_or_none()
            if removed_vote_id is not None:
                await self._decrement_vote_count(project_id)
            await self.db.commit()
            return removed_vote_id is not None
        except Exception:
            await self.db.rollback()
            raise

    async def list_my_voted_projects(
        self,
        *,
        user_id: UUID,
        limit: int = 20,
        cursor: str | None = None,
    ) -> ProjectListResponse:
        """Return published projects voted by user, newest vote first."""
        limit = max(1, min(limit, 100))

        vote_cols = getattr(Vote, "__table__").c
        project_cols = getattr(Project, "__table__").c
        statement = (
            select(Vote, Project)
            .join(Project, project_cols.id == vote_cols.project_id)
            .where(
                vote_cols.user_id == user_id,
                project_cols.is_published.is_(True),
            )
        )

        if cursor is not None:
            cursor_payload = self._decode_recent_votes_cursor(cursor)
            cursor_voted_at = self._parse_datetime(cursor_payload["voted_at"])
            cursor_project_id = UUID(cursor_payload["project_id"])
            statement = statement.where(
                (vote_cols.created_at < cursor_voted_at)
                | (
                    (vote_cols.created_at == cursor_voted_at)
                    & (vote_cols.project_id < cursor_project_id)
                )
            )

        statement = statement.order_by(
            vote_cols.created_at.desc(),
            vote_cols.project_id.desc(),
        ).limit(limit + 1)

        rows = list((await self.db.exec(statement)).all())
        has_more = len(rows) > limit
        page_rows = rows[:limit]
        projects = [project for _, project in page_rows]

        members_by_project = await get_members_for_projects(
            self.db, [project.id for project in projects]
        )
        items = [
            ProjectListItemResponse(
                **project.model_dump(),
                members=members_by_project.get(project.id, []),
                team_size=len(members_by_project.get(project.id, [])),
                viewer_has_voted=True,
            )
            for _, project in page_rows
        ]

        next_cursor: str | None = None
        if has_more and page_rows:
            last_vote, last_project = page_rows[-1]
            next_cursor = self._encode_recent_votes_cursor(
                voted_at=last_vote.created_at,
                project_id=last_project.id,
            )

        return ProjectListResponse(items=items, next_cursor=next_cursor)

    async def _get_vote_target_project(self, project_id: UUID) -> Project | None:
        project_cols = getattr(Project, "__table__").c
        statement = select(Project).where(
            project_cols.id == project_id,
            project_cols.is_published.is_(True),
        )
        result = await self.db.exec(statement)
        return result.first()

    async def _increment_vote_count(self, project_id: UUID) -> None:
        project_cols = getattr(Project, "__table__").c
        statement = (
            update(Project)
            .where(project_cols.id == project_id)
            .values(vote_count=project_cols.vote_count + 1)
        )
        await self.db.exec(statement)

    async def _decrement_vote_count(self, project_id: UUID) -> None:
        project_cols = getattr(Project, "__table__").c
        statement = (
            update(Project)
            .where(project_cols.id == project_id)
            .values(
                vote_count=sa.case(
                    (project_cols.vote_count > 0, project_cols.vote_count - 1),
                    else_=0,
                )
            )
        )
        await self.db.exec(statement)

    def _encode_recent_votes_cursor(
        self, *, voted_at: datetime, project_id: UUID
    ) -> str:
        payload = {
            "sort": VOTE_SORT_RECENT,
            "voted_at": voted_at.isoformat(),
            "project_id": str(project_id),
        }
        return encode_cursor_payload(payload)

    def _decode_recent_votes_cursor(self, cursor: str) -> dict[str, str]:
        payload = decode_cursor_payload(cursor)
        required = {"sort", "voted_at", "project_id"}
        if set(payload.keys()) != required:
            raise CursorError("Invalid cursor")

        if payload["sort"] != VOTE_SORT_RECENT:
            raise CursorError("Invalid cursor")

        voted_at = payload["voted_at"]
        project_id = payload["project_id"]
        if not isinstance(voted_at, str) or not isinstance(project_id, str):
            raise CursorError("Invalid cursor")

        try:
            self._parse_datetime(voted_at)
            UUID(project_id)
        except (TypeError, ValueError) as exc:
            raise CursorError("Invalid cursor") from exc

        return {"sort": payload["sort"], "voted_at": voted_at, "project_id": project_id}

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise CursorError("Invalid cursor") from exc
