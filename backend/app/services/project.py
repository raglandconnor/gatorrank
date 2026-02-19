from datetime import datetime
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
                    email=user.email,
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
    ) -> ProjectListResponse:
        limit = max(1, min(limit, 100))

        project_cols = getattr(Project, "__table__").c
        statement = self._base_published_projects_query()

        cursor_payload: dict[str, str | int] | None = None
        if cursor is not None:
            cursor_payload = self._decode_cursor(cursor, sort)

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
            next_cursor = self._encode_cursor(projects[-1], sort)

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
                    email=user.email,
                    profile_picture_url=user.profile_picture_url,
                )
            )

        return members_by_project

    @staticmethod
    def _to_project_list_item(
        project: Project, members: list[ProjectMemberInfo]
    ) -> ProjectListItemResponse:
        return ProjectListItemResponse(**project.model_dump(), members=members)

    def _encode_cursor(self, project: Project, sort: ProjectSort) -> str:
        if sort == "new":
            payload: dict[str, str | int] = {
                "sort": "new",
                "id": str(project.id),
                "created_at": project.created_at.isoformat(),
            }
        else:
            payload = {
                "sort": "top",
                "id": str(project.id),
                "vote_count": project.vote_count,
                "created_at": project.created_at.isoformat(),
            }

        return encode_cursor_payload(payload)

    def _decode_cursor(self, cursor: str, sort: ProjectSort) -> dict[str, str | int]:
        payload = decode_cursor_payload(cursor)

        cursor_sort = payload.get("sort")
        if cursor_sort != sort:
            raise CursorError("Cursor sort does not match requested sort")

        if sort == "new":
            required = {"sort", "id", "created_at"}
        else:
            required = {"sort", "id", "vote_count", "created_at"}

        if set(payload.keys()) != required:
            raise CursorError("Invalid cursor")

        return payload

    @staticmethod
    def _parse_datetime(value: str | int) -> datetime:
        if not isinstance(value, str):
            raise CursorError("Invalid cursor")
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise CursorError("Invalid cursor") from exc
