from datetime import UTC, date, datetime, time, timedelta
from typing import Literal
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.project import (
    ProjectDetailResponse,
    ProjectListItemResponse,
    ProjectListResponse,
    ProjectMemberInfo,
)
from app.utils.pagination import (
    CursorError,
    decode_cursor_payload,
    encode_cursor_payload,
)

ProjectSort = Literal["top", "new"]


class ProjectAccessForbiddenError(PermissionError):
    """Raised when an authenticated user cannot access an existing project."""


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_project_by_id(self, project_id: UUID) -> Project | None:
        statement = select(Project).where(Project.id == project_id)
        result = await self.db.exec(statement)
        return result.first()

    async def get_member_role(self, project_id: UUID, user_id: UUID) -> str | None:
        statement = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        result = await self.db.exec(statement)
        member = result.first()
        if member is None:
            return None
        return member.role

    async def is_project_member(self, project_id: UUID, user_id: UUID) -> bool:
        return (await self.get_member_role(project_id, user_id)) is not None

    def can_view_project(
        self,
        project: Project,
        current_user_id: UUID | None,
        member_role: str | None = None,
    ) -> bool:
        if project.is_published:
            return True
        if current_user_id is None:
            return False
        if project.created_by_id == current_user_id:
            return True
        return member_role is not None

    def can_edit_project(
        self,
        project: Project,
        current_user_id: UUID | None,
        member_role: str | None = None,
    ) -> bool:
        if current_user_id is None:
            return False
        if project.created_by_id == current_user_id:
            return True
        return member_role in {"owner", "maintainer"}

    async def get_project_detail(
        self,
        project_id: UUID,
        current_user_id: UUID | None,
    ) -> ProjectDetailResponse | None:
        project = await self.get_project_by_id(project_id)
        if project is None:
            return None

        member_role: str | None = None
        if current_user_id is not None:
            member_role = await self.get_member_role(project.id, current_user_id)

        if not self.can_view_project(project, current_user_id, member_role):
            if current_user_id is not None:
                raise ProjectAccessForbiddenError("Project access forbidden")
            return None

        members = await self.get_project_members(project.id)
        return ProjectDetailResponse(
            **project.model_dump(),
            members=members,
        )

    async def get_project_members(self, project_id: UUID) -> list[ProjectMemberInfo]:
        project_member_cols = getattr(ProjectMember, "__table__").c
        user_cols = getattr(User, "__table__").c
        statement = (
            select(ProjectMember, User)
            .join(User, user_cols.id == project_member_cols.user_id)
            .where(project_member_cols.project_id == project_id)
            .order_by(project_member_cols.added_at.asc())
        )
        result = await self.db.exec(statement)

        members: list[ProjectMemberInfo] = []
        for member, user in result.all():
            members.append(
                ProjectMemberInfo(
                    user_id=user.id,
                    role=member.role,
                    full_name=user.full_name,
                    profile_picture_url=user.profile_picture_url,
                )
            )
        return members

    async def list_projects(
        self,
        *,
        sort: ProjectSort = "top",
        limit: int = 20,
        cursor: str | None = None,
        published_from: date | None = None,
        published_to: date | None = None,
    ) -> ProjectListResponse:
        limit = max(1, min(limit, 100))

        project_cols = getattr(Project, "__table__").c
        statement = self._base_published_projects_query()
        if (
            sort == "top"
            and cursor is not None
            and published_from is None
            and published_to is None
        ):
            cursor_range = self._extract_top_range_from_cursor(cursor)
            if cursor_range is not None:
                published_from, published_to = cursor_range
        top_range = self._resolve_top_date_range(
            sort=sort,
            published_from=published_from,
            published_to=published_to,
        )

        if sort == "top":
            if top_range is None:
                raise CursorError("Invalid date range")
            range_start_dt, range_end_exclusive_dt = self._top_range_bounds(top_range)
            statement = statement.where(
                project_cols.published_at.is_not(None),
                project_cols.published_at >= range_start_dt,
                project_cols.published_at < range_end_exclusive_dt,
            )

        cursor_payload: dict[str, str | int] | None = None
        if cursor is not None:
            cursor_payload = self._decode_cursor(cursor, sort, top_range=top_range)

        if sort == "new":
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

        members_by_project = await self._get_members_for_projects(
            [p.id for p in projects]
        )

        items = [
            self._to_project_list_item(project, members_by_project.get(project.id, []))
            for project in projects
        ]

        next_cursor: str | None = None
        if has_more and projects:
            next_cursor = self._encode_cursor(projects[-1], sort, top_range=top_range)

        return ProjectListResponse(items=items, next_cursor=next_cursor)

    @staticmethod
    def _base_published_projects_query():
        project_cols = getattr(Project, "__table__").c
        return select(Project).where(project_cols.is_published.is_(True))

    async def _get_members_for_projects(
        self, project_ids: list[UUID]
    ) -> dict[UUID, list[ProjectMemberInfo]]:
        if not project_ids:
            return {}

        project_member_cols = getattr(ProjectMember, "__table__").c
        user_cols = getattr(User, "__table__").c
        statement = (
            select(ProjectMember, User)
            .join(User, user_cols.id == project_member_cols.user_id)
            .where(project_member_cols.project_id.in_(project_ids))
            .order_by(
                project_member_cols.project_id.asc(), project_member_cols.added_at.asc()
            )
        )
        result = await self.db.exec(statement)

        members_by_project: dict[UUID, list[ProjectMemberInfo]] = {
            pid: [] for pid in project_ids
        }
        for member, user in result.all():
            members_by_project[member.project_id].append(
                ProjectMemberInfo(
                    user_id=user.id,
                    role=member.role,
                    full_name=user.full_name,
                    profile_picture_url=user.profile_picture_url,
                )
            )

        return members_by_project

    @staticmethod
    def _to_project_list_item(
        project: Project, members: list[ProjectMemberInfo]
    ) -> ProjectListItemResponse:
        return ProjectListItemResponse(**project.model_dump(), members=members)

    def _encode_cursor(
        self,
        project: Project,
        sort: ProjectSort,
        *,
        top_range: tuple[date, date] | None = None,
    ) -> str:
        if sort == "new":
            payload: dict[str, str | int] = {
                "sort": "new",
                "id": str(project.id),
                "created_at": project.created_at.isoformat(),
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
            }

        return encode_cursor_payload(payload)

    def _decode_cursor(
        self,
        cursor: str,
        sort: ProjectSort,
        *,
        top_range: tuple[date, date] | None = None,
    ) -> dict[str, str | int]:
        payload = decode_cursor_payload(cursor)

        if sort == "new":
            required = {"sort", "id", "created_at"}
        else:
            required = {
                "sort",
                "id",
                "vote_count",
                "created_at",
                "published_from",
                "published_to",
            }

        if set(payload.keys()) != required:
            raise CursorError("Invalid cursor")

        if payload["sort"] != sort:
            raise CursorError("Cursor sort does not match requested sort")

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
    def _resolve_top_date_range(
        *,
        sort: ProjectSort,
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

    def _extract_top_range_from_cursor(self, cursor: str) -> tuple[date, date] | None:
        try:
            payload = decode_cursor_payload(cursor)
        except CursorError:
            return None

        raw_from = payload.get("published_from")
        raw_to = payload.get("published_to")
        if raw_from is None or raw_to is None:
            return None

        return (self._parse_date(raw_from), self._parse_date(raw_to))
