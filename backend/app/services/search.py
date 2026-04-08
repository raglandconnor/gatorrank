from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, date, datetime, time, timedelta
import hashlib
import json
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.project import Project
from app.models.taxonomy import (
    Category,
    ProjectCategory,
    ProjectTag,
    ProjectTechStack,
    Tag,
    TechStack,
)
from app.schemas.search import ProjectSearchRequest, ProjectSearchResponse, SearchSort
from app.services.project import CursorError, ProjectService
from app.services.taxonomy import normalize_taxonomy_name
from app.utils.pagination import decode_cursor_payload, encode_cursor_payload


class SearchService(ABC):
    """Service boundary for project search implementations."""

    @abstractmethod
    async def search_projects(
        self,
        *,
        request: ProjectSearchRequest,
        current_user_id: UUID | None = None,
    ) -> ProjectSearchResponse:
        """Search published projects using a stable query contract."""


class PostgresSearchService(SearchService):
    """Postgres-backed implementation of the project search contract."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._project_service = ProjectService(db)

    async def search_projects(
        self,
        *,
        request: ProjectSearchRequest,
        current_user_id: UUID | None = None,
    ) -> ProjectSearchResponse:
        limit = max(1, min(request.limit, 100))
        project_cols = getattr(Project, "__table__").c

        top_range = self._resolve_top_date_range(
            sort=request.sort,
            published_from=request.published_from,
            published_to=request.published_to,
        )
        if (
            request.sort == "top"
            and request.cursor is not None
            and request.published_from is None
            and request.published_to is None
        ):
            cursor_range = self._extract_top_range_from_cursor(request.cursor)
            if cursor_range is not None:
                top_range = cursor_range

        if request.sort == "top" and top_range is None:
            raise CursorError("Invalid date range")

        search_signature = self._build_search_signature(
            request=request, top_range=top_range
        )
        cursor_payload: dict[str, str | int] | None = None
        if request.cursor is not None:
            cursor_payload = self._decode_cursor(
                cursor=request.cursor,
                sort=request.sort,
                search_signature=search_signature,
                top_range=top_range,
            )

        statement = ProjectService._base_published_projects_query()
        statement = self._apply_keyword_filter(statement, request=request)
        statement = await self._apply_taxonomy_filters(statement, request=request)

        if request.sort == "top":
            if top_range is None:
                raise CursorError("Invalid date range")
            range_start_dt, range_end_exclusive_dt = self._top_range_bounds(top_range)
            statement = statement.where(
                project_cols.published_at.is_not(None),
                project_cols.published_at >= range_start_dt,
                project_cols.published_at < range_end_exclusive_dt,
            )

        if request.sort == "new":
            if cursor_payload is not None:
                created_at = self._parse_datetime(cursor_payload["created_at"])
                cursor_id = UUID(str(cursor_payload["id"]))
                statement = statement.where(
                    (project_cols.created_at < created_at)
                    | (
                        (project_cols.created_at == created_at)
                        & (project_cols.id < cursor_id)
                    )
                )
            statement = statement.order_by(
                project_cols.created_at.desc(),
                project_cols.id.desc(),
            )
        else:
            if cursor_payload is not None:
                vote_count = int(cursor_payload["vote_count"])
                created_at = self._parse_datetime(cursor_payload["created_at"])
                cursor_id = UUID(str(cursor_payload["id"]))
                statement = statement.where(
                    (project_cols.vote_count < vote_count)
                    | (
                        (project_cols.vote_count == vote_count)
                        & (project_cols.created_at < created_at)
                    )
                    | (
                        (project_cols.vote_count == vote_count)
                        & (project_cols.created_at == created_at)
                        & (project_cols.id < cursor_id)
                    )
                )
            statement = statement.order_by(
                project_cols.vote_count.desc(),
                project_cols.created_at.desc(),
                project_cols.id.desc(),
            )

        statement = statement.limit(limit + 1)
        result = await self.db.exec(statement)
        rows = list(result.all())

        has_more = len(rows) > limit
        projects = rows[:limit]
        project_ids = [project.id for project in projects]

        members_by_project = await self._project_service._get_members_for_projects(
            project_ids
        )
        taxonomy_by_project = (
            await self._project_service.get_project_taxonomy_by_project_ids(project_ids)
        )
        voted_project_ids: set[UUID] = set()
        if current_user_id is not None:
            voted_project_ids = await self._project_service._get_voted_project_ids(
                user_id=current_user_id,
                project_ids=project_ids,
            )

        items = [
            self._project_service._to_project_list_item(
                project,
                members_by_project,
                taxonomy_by_project,
                voted_project_ids,
            )
            for project in projects
        ]

        next_cursor: str | None = None
        if has_more and projects:
            next_cursor = self._encode_cursor(
                project=projects[-1],
                sort=request.sort,
                search_signature=search_signature,
                top_range=top_range,
            )

        return ProjectSearchResponse(items=items, next_cursor=next_cursor)

    def _apply_keyword_filter(
        self,
        statement: Any,
        *,
        request: ProjectSearchRequest,
    ) -> Any:
        if request.q is None:
            return statement

        project_cols = getattr(Project, "__table__").c
        escaped_query = self._escape_like_query(request.q.lower())
        pattern = f"%{escaped_query}%"
        return statement.where(
            sa.or_(
                sa.func.lower(project_cols.title).like(pattern, escape="\\"),
                sa.func.lower(project_cols.short_description).like(
                    pattern, escape="\\"
                ),
            )
        )

    async def _apply_taxonomy_filters(
        self,
        statement: Any,
        *,
        request: ProjectSearchRequest,
    ) -> Any:
        category_terms = [
            normalize_taxonomy_name(value) for value in request.categories
        ]
        tag_terms = [normalize_taxonomy_name(value) for value in request.tags]
        tech_stack_terms = [
            normalize_taxonomy_name(value) for value in request.tech_stack
        ]

        statement = await self._apply_taxonomy_filter_family(
            statement=statement,
            model=Category,
            join_model=ProjectCategory,
            join_term_fk="category_id",
            normalized_terms=category_terms,
        )
        statement = await self._apply_taxonomy_filter_family(
            statement=statement,
            model=Tag,
            join_model=ProjectTag,
            join_term_fk="tag_id",
            normalized_terms=tag_terms,
        )
        statement = await self._apply_taxonomy_filter_family(
            statement=statement,
            model=TechStack,
            join_model=ProjectTechStack,
            join_term_fk="tech_stack_id",
            normalized_terms=tech_stack_terms,
        )
        return statement

    async def _apply_taxonomy_filter_family(
        self,
        *,
        statement: Any,
        model: type[Category] | type[Tag] | type[TechStack],
        join_model: type[ProjectCategory] | type[ProjectTag] | type[ProjectTechStack],
        join_term_fk: str,
        normalized_terms: list[str],
    ) -> Any:
        if not normalized_terms:
            return statement

        term_ids = await self._resolve_term_ids(model, normalized_terms)
        if not term_ids:
            return statement.where(sa.sql.false())

        project_cols = getattr(Project, "__table__").c
        join_cols = getattr(join_model, "__table__").c
        return statement.where(
            sa.exists(
                select(1).where(
                    join_cols.project_id == project_cols.id,
                    getattr(join_cols, join_term_fk).in_(term_ids),
                )
            )
        )

    async def _resolve_term_ids(
        self,
        model: type[Category] | type[Tag] | type[TechStack],
        normalized_terms: list[str],
    ) -> list[UUID]:
        model_cols = getattr(model, "__table__").c
        statement = select(model_cols.id).where(
            model_cols.normalized_name.in_(normalized_terms)
        )
        result = await self.db.exec(statement)
        return [row for row in result.all()]

    def _encode_cursor(
        self,
        *,
        project: Project,
        sort: SearchSort,
        search_signature: str,
        top_range: tuple[date, date] | None,
    ) -> str:
        if sort == "new":
            payload: dict[str, str | int] = {
                "sort": "new",
                "id": str(project.id),
                "created_at": project.created_at.isoformat(),
                "search_sig": search_signature,
            }
        else:
            if top_range is None:
                raise CursorError("Invalid cursor")
            payload = {
                "sort": "top",
                "id": str(project.id),
                "vote_count": project.vote_count,
                "created_at": project.created_at.isoformat(),
                "published_from": top_range[0].isoformat(),
                "published_to": top_range[1].isoformat(),
                "search_sig": search_signature,
            }
        return encode_cursor_payload(payload)

    def _decode_cursor(
        self,
        *,
        cursor: str,
        sort: SearchSort,
        search_signature: str,
        top_range: tuple[date, date] | None,
    ) -> dict[str, str | int]:
        payload = decode_cursor_payload(cursor)
        if sort == "new":
            required = {"sort", "id", "created_at", "search_sig"}
        else:
            required = {
                "sort",
                "id",
                "vote_count",
                "created_at",
                "published_from",
                "published_to",
                "search_sig",
            }

        if set(payload.keys()) != required:
            raise CursorError("Invalid cursor")
        if payload["sort"] != sort:
            raise CursorError("Cursor sort does not match requested sort")
        if payload["search_sig"] != search_signature:
            raise CursorError("Cursor does not match requested search")

        try:
            UUID(str(payload["id"]))
            self._parse_datetime(payload["created_at"])
            if sort == "top":
                int(payload["vote_count"])
                payload_from = self._parse_date(payload["published_from"])
                payload_to = self._parse_date(payload["published_to"])
                if top_range is None:
                    raise CursorError("Invalid cursor")
                if (payload_from, payload_to) != top_range:
                    raise CursorError("Invalid cursor")
        except (TypeError, ValueError) as exc:
            raise CursorError("Invalid cursor") from exc
        return payload

    def _extract_top_range_from_cursor(self, cursor: str) -> tuple[date, date] | None:
        try:
            payload = decode_cursor_payload(cursor)
        except CursorError:
            return None
        raw_from = payload.get("published_from")
        raw_to = payload.get("published_to")
        if raw_from is None or raw_to is None:
            return None
        try:
            return (self._parse_date(raw_from), self._parse_date(raw_to))
        except CursorError:
            return None

    def _build_search_signature(
        self,
        *,
        request: ProjectSearchRequest,
        top_range: tuple[date, date] | None,
    ) -> str:
        signature_payload: dict[str, Any] = {
            "q": request.q.lower() if request.q is not None else None,
            "categories": sorted(
                normalize_taxonomy_name(v) for v in request.categories
            ),
            "tags": sorted(normalize_taxonomy_name(v) for v in request.tags),
            "tech_stack": sorted(
                normalize_taxonomy_name(v) for v in request.tech_stack
            ),
            "sort": request.sort,
        }
        if request.sort == "top":
            if top_range is None:
                raise CursorError("Invalid date range")
            signature_payload["published_from"] = top_range[0].isoformat()
            signature_payload["published_to"] = top_range[1].isoformat()

        encoded = json.dumps(signature_payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @staticmethod
    def _resolve_top_date_range(
        *,
        sort: SearchSort,
        published_from: date | None,
        published_to: date | None,
    ) -> tuple[date, date] | None:
        if sort != "top":
            return None
        end_date = published_to or datetime.now(UTC).date()
        start_date = published_from or (end_date - timedelta(days=90))
        if start_date > end_date:
            raise CursorError("Invalid date range")
        return (start_date, end_date)

    @staticmethod
    def _top_range_bounds(top_range: tuple[date, date]) -> tuple[datetime, datetime]:
        start_date, end_date = top_range
        start_dt = datetime.combine(start_date, time.min, tzinfo=UTC)
        end_exclusive_dt = datetime.combine(
            end_date + timedelta(days=1),
            time.min,
            tzinfo=UTC,
        )
        return start_dt, end_exclusive_dt

    @staticmethod
    def _parse_datetime(value: str | int) -> datetime:
        if not isinstance(value, str):
            raise CursorError("Invalid cursor")
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise CursorError("Invalid cursor") from exc

    @staticmethod
    def _parse_date(value: str | int) -> date:
        if not isinstance(value, str):
            raise CursorError("Invalid cursor")
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise CursorError("Invalid cursor") from exc

    @staticmethod
    def _escape_like_query(value: str) -> str:
        escaped = value.replace("\\", "\\\\")
        escaped = escaped.replace("%", "\\%")
        escaped = escaped.replace("_", "\\_")
        return escaped
