from datetime import UTC, date, datetime, time, timedelta
from typing import Literal
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.project import Project, ProjectMember, Vote
from app.models.project_roles import (
    PROJECT_ROLE_OWNER,
    ProjectMemberRole,
    cast_project_member_role,
)
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectListItemResponse,
    ProjectListResponse,
    ProjectMemberCreateRequest,
    ProjectMemberInfo,
    ProjectMemberUpdateRequest,
    ProjectUpdateRequest,
)
from app.services.project_members import get_members_for_projects
from app.utils.pagination import (
    CursorError,
    decode_cursor_payload,
    encode_cursor_payload,
)

ProjectSort = Literal["top", "new"]


class ProjectAccessForbiddenError(PermissionError):
    """Raised when an authenticated user cannot access an existing project."""


class ProjectValidationError(ValueError):
    """Raised when a project write operation fails business validation."""


class ProjectConflictError(ValueError):
    """Raised when a request conflicts with project invariants."""


class ProjectResourceNotFoundError(LookupError):
    """Raised when a related project resource cannot be found."""


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_project_by_id(self, project_id: UUID) -> Project | None:
        statement = select(Project).where(Project.id == project_id)
        result = await self.db.exec(statement)
        return result.first()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).where(User.id == user_id)
        result = await self.db.exec(statement)
        return result.first()

    async def get_user_by_email(self, email: str) -> User | None:
        normalized_email = email.strip().lower()
        statement = select(User).where(sa.func.lower(User.email) == normalized_email)
        result = await self.db.exec(statement)
        return result.first()

    async def create_project(
        self,
        *,
        created_by_id: UUID,
        payload: ProjectCreateRequest,
    ) -> ProjectDetailResponse:
        project = Project(  # pyright: ignore[reportCallIssue]
            created_by_id=created_by_id,
            title=payload.title,
            short_description=payload.short_description,
            long_description=payload.long_description,
            demo_url=payload.demo_url,
            github_url=payload.github_url,
            video_url=payload.video_url,
            is_group_project=False,
            vote_count=0,
            is_published=False,
            published_at=None,
        )
        owner_member = ProjectMember(  # pyright: ignore[reportCallIssue]
            project_id=project.id,
            user_id=created_by_id,
            role=PROJECT_ROLE_OWNER,
        )

        try:
            self.db.add(project)
            self.db.add(owner_member)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        created = await self.get_project_detail(project.id, created_by_id)
        if created is None:
            raise RuntimeError("Created project could not be loaded")
        return created

    async def update_project(
        self,
        *,
        project_id: UUID,
        current_user_id: UUID,
        payload: ProjectUpdateRequest,
    ) -> ProjectDetailResponse | None:
        project = await self.get_project_by_id(project_id)
        if project is None:
            return None

        member_role: str | None = None
        if project.created_by_id != current_user_id:
            member_role = await self.get_member_role(project_id, current_user_id)
        if not self.can_edit_project(project, current_user_id, member_role):
            raise ProjectAccessForbiddenError("Project edit forbidden")

        final_demo_url = (
            payload.demo_url
            if "demo_url" in payload.model_fields_set
            else project.demo_url
        )
        final_github_url = (
            payload.github_url
            if "github_url" in payload.model_fields_set
            else project.github_url
        )
        final_video_url = (
            payload.video_url
            if "video_url" in payload.model_fields_set
            else project.video_url
        )
        if not any([final_demo_url, final_github_url, final_video_url]):
            raise ProjectValidationError(
                "Provide at least one of demo_url, github_url, or video_url."
            )

        if "title" in payload.model_fields_set:
            if payload.title is None:
                raise ProjectValidationError("title cannot be null")
            project.title = payload.title
        if "short_description" in payload.model_fields_set:
            if payload.short_description is None:
                raise ProjectValidationError("short_description cannot be null")
            project.short_description = payload.short_description
        if "long_description" in payload.model_fields_set:
            project.long_description = payload.long_description
        if "demo_url" in payload.model_fields_set:
            project.demo_url = payload.demo_url
        if "github_url" in payload.model_fields_set:
            project.github_url = payload.github_url
        if "video_url" in payload.model_fields_set:
            project.video_url = payload.video_url

        try:
            self.db.add(project)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        updated_project = await self.get_project_detail(project.id, current_user_id)
        if updated_project is None:
            raise RuntimeError("Updated project could not be loaded")
        return updated_project

    async def publish_project(
        self,
        *,
        project_id: UUID,
        current_user_id: UUID,
    ) -> ProjectDetailResponse | None:
        project = await self.get_project_by_id(project_id)
        if project is None:
            return None

        member_role: str | None = None
        if project.created_by_id != current_user_id:
            member_role = await self.get_member_role(project_id, current_user_id)
        if not self.can_edit_project(project, current_user_id, member_role):
            raise ProjectAccessForbiddenError("Project publish forbidden")

        if project.is_published:
            published_project = await self.get_project_detail(
                project.id, current_user_id
            )
            if published_project is None:
                raise RuntimeError("Published project could not be loaded")
            return published_project

        publish_at = datetime.now(UTC)
        project_cols = getattr(Project, "__table__").c
        publish_statement = (
            update(Project)
            .where(
                project_cols.id == project_id,
                project_cols.is_published.is_(False),
            )
            .values(
                is_published=True,
                published_at=publish_at,
            )
        )

        try:
            result = await self.db.exec(publish_statement)
            if result.rowcount and result.rowcount > 0:
                await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        published_project = await self.get_project_detail(project.id, current_user_id)
        if published_project is None:
            raise RuntimeError("Published project could not be loaded")
        return published_project

    async def unpublish_project(
        self,
        *,
        project_id: UUID,
        current_user_id: UUID,
    ) -> ProjectDetailResponse | None:
        project = await self.get_project_by_id(project_id)
        if project is None:
            return None

        member_role: str | None = None
        if project.created_by_id != current_user_id:
            member_role = await self.get_member_role(project_id, current_user_id)
        if not self.can_edit_project(project, current_user_id, member_role):
            raise ProjectAccessForbiddenError("Project unpublish forbidden")

        if not project.is_published:
            unpublished_project = await self.get_project_detail(
                project.id, current_user_id
            )
            if unpublished_project is None:
                raise RuntimeError("Unpublished project could not be loaded")
            return unpublished_project

        project.is_published = False
        project.published_at = None

        try:
            self.db.add(project)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        unpublished_project = await self.get_project_detail(project.id, current_user_id)
        if unpublished_project is None:
            raise RuntimeError("Unpublished project could not be loaded")
        return unpublished_project

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

    async def get_project_member(
        self, project_id: UUID, user_id: UUID
    ) -> ProjectMember | None:
        statement = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        result = await self.db.exec(statement)
        return result.first()

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
        return member_role == PROJECT_ROLE_OWNER

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
        viewer_has_voted = False
        if project.is_published and current_user_id is not None:
            viewer_has_voted = await self._viewer_has_voted(project.id, current_user_id)
        return ProjectDetailResponse(
            **project.model_dump(),
            members=members,
            viewer_has_voted=viewer_has_voted,
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
            members.append(self._member_to_info(member, user))
        return members

    async def list_project_members(
        self, *, project_id: UUID, current_user_id: UUID | None
    ) -> list[ProjectMemberInfo] | None:
        project = await self.get_project_by_id(project_id)
        if project is None:
            return None

        member_role: str | None = None
        if current_user_id is not None:
            member_role = await self.get_member_role(project.id, current_user_id)

        if not self.can_view_project(project, current_user_id, member_role):
            if current_user_id is not None:
                raise ProjectAccessForbiddenError("Project members access forbidden")
            return None

        return await self.get_project_members(project.id)

    async def add_project_member(
        self,
        *,
        project_id: UUID,
        current_user_id: UUID,
        payload: ProjectMemberCreateRequest,
    ) -> ProjectMemberInfo | None:
        project = await self.get_project_by_id(project_id)
        if project is None:
            return None
        await self._assert_owner_access(
            project=project, current_user_id=current_user_id
        )

        user = await self.get_user_by_email(payload.email)
        if user is None:
            raise ProjectResourceNotFoundError("User not found")

        existing_member = await self.get_project_member(project.id, user.id)
        if existing_member is not None:
            raise ProjectConflictError("User is already a member of this project")

        member = ProjectMember(  # pyright: ignore[reportCallIssue]
            project_id=project.id,
            user_id=user.id,
            role=payload.role,
        )

        try:
            self.db.add(member)
            await self.db.flush()
            await self._sync_group_project_flag(project)
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ProjectConflictError(
                "User is already a member of this project"
            ) from exc
        except Exception:
            await self.db.rollback()
            raise

        return self._member_to_info(member, user)

    async def update_project_member(
        self,
        *,
        project_id: UUID,
        target_user_id: UUID,
        current_user_id: UUID,
        payload: ProjectMemberUpdateRequest,
    ) -> ProjectMemberInfo | None:
        project = await self.get_project_by_id(project_id)
        if project is None:
            return None
        await self._assert_owner_access(
            project=project, current_user_id=current_user_id
        )

        member = await self.get_project_member(project.id, target_user_id)
        if member is None:
            raise ProjectResourceNotFoundError("Project membership not found")
        if member.role == PROJECT_ROLE_OWNER:
            raise ProjectConflictError("Owner role cannot be modified")

        user = await self.get_user_by_id(member.user_id)
        if user is None:
            raise RuntimeError("Membership user could not be loaded")

        member.role = payload.role
        try:
            self.db.add(member)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return self._member_to_info(member, user)

    async def remove_project_member(
        self,
        *,
        project_id: UUID,
        target_user_id: UUID,
        current_user_id: UUID,
    ) -> bool | None:
        project = await self.get_project_by_id(project_id)
        if project is None:
            return None
        await self._assert_owner_access(
            project=project, current_user_id=current_user_id
        )

        member = await self.get_project_member(project.id, target_user_id)
        if member is None:
            raise ProjectResourceNotFoundError("Project membership not found")
        if member.role == PROJECT_ROLE_OWNER:
            raise ProjectConflictError("Owner membership cannot be removed")

        try:
            await self.db.delete(member)
            await self.db.flush()
            await self._sync_group_project_flag(project)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return True

    async def leave_project(
        self, *, project_id: UUID, current_user_id: UUID
    ) -> bool | None:
        project = await self.get_project_by_id(project_id)
        if project is None:
            return None

        member = await self.get_project_member(project.id, current_user_id)
        if member is None:
            raise ProjectResourceNotFoundError("Project membership not found")

        if member.role == PROJECT_ROLE_OWNER:
            owner_count = await self._count_members_by_role(
                project.id, role=PROJECT_ROLE_OWNER
            )
            if owner_count <= 1:
                raise ProjectConflictError("Last owner cannot leave the project")

        try:
            await self.db.delete(member)
            await self.db.flush()
            await self._sync_group_project_flag(project)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return True

    async def list_projects(
        self,
        *,
        sort: ProjectSort = "top",
        limit: int = 20,
        cursor: str | None = None,
        published_from: date | None = None,
        published_to: date | None = None,
        created_by_id: UUID | None = None,
        current_user_id: UUID | None = None,
    ) -> ProjectListResponse:
        limit = max(1, min(limit, 100))

        project_cols = getattr(Project, "__table__").c
        statement = self._base_published_projects_query(created_by_id)
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
        voted_project_ids: set[UUID] = set()
        if current_user_id is not None:
            voted_project_ids = await self._get_voted_project_ids(
                user_id=current_user_id,
                project_ids=[project.id for project in projects],
            )

        items = [
            self._to_project_list_item(
                project,
                members_by_project.get(project.id, []),
                viewer_has_voted=project.id in voted_project_ids,
            )
            for project in projects
        ]

        next_cursor: str | None = None
        if has_more and projects:
            next_cursor = self._encode_cursor(projects[-1], sort, top_range=top_range)

        return ProjectListResponse(items=items, next_cursor=next_cursor)

    async def _assert_owner_access(
        self, *, project: Project, current_user_id: UUID | None
    ) -> None:
        member_role: str | None = None
        if current_user_id is not None and project.created_by_id != current_user_id:
            member_role = await self.get_member_role(project.id, current_user_id)
        if not self.can_edit_project(project, current_user_id, member_role):
            raise ProjectAccessForbiddenError("Project member management forbidden")

    async def _count_members_by_role(self, project_id: UUID, *, role: str) -> int:
        statement = (
            select(sa.func.count())
            .select_from(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.role == role,
            )
        )
        result = await self.db.exec(statement)
        return int(result.one())

    async def _sync_group_project_flag(self, project: Project) -> None:
        statement = (
            select(sa.func.count())
            .select_from(ProjectMember)
            .where(ProjectMember.project_id == project.id)
        )
        result = await self.db.exec(statement)
        member_count = int(result.one())
        project.is_group_project = member_count > 1
        self.db.add(project)

    @staticmethod
    def _coerce_member_role(value: str) -> ProjectMemberRole:
        try:
            return cast_project_member_role(value)
        except ValueError as exc:
            raise RuntimeError("Unexpected project member role in database") from exc

    @staticmethod
    def _member_to_info(member: ProjectMember, user: User) -> ProjectMemberInfo:
        return ProjectMemberInfo(
            user_id=user.id,
            role=ProjectService._coerce_member_role(member.role),
            full_name=user.full_name,
            profile_picture_url=user.profile_picture_url,
        )

    @staticmethod
    def _base_published_projects_query(created_by_id: UUID | None = None):
        project_cols = getattr(Project, "__table__").c
        stmt = select(Project).where(project_cols.is_published.is_(True))
        if created_by_id:
            stmt = stmt.where(project_cols.created_by_id == created_by_id)
        return stmt

    async def _get_members_for_projects(
        self, project_ids: list[UUID]
    ) -> dict[UUID, list[ProjectMemberInfo]]:
        return await get_members_for_projects(self.db, project_ids)

    @staticmethod
    def _to_project_list_item(
        project: Project, members: list[ProjectMemberInfo], *, viewer_has_voted: bool
    ) -> ProjectListItemResponse:
        return ProjectListItemResponse(
            **project.model_dump(),
            members=members,
            viewer_has_voted=viewer_has_voted,
        )

    async def _viewer_has_voted(self, project_id: UUID, user_id: UUID) -> bool:
        vote_cols = getattr(Vote, "__table__").c
        statement = select(Vote).where(
            vote_cols.project_id == project_id,
            vote_cols.user_id == user_id,
        )
        result = await self.db.exec(statement)
        return result.one_or_none() is not None

    async def _get_voted_project_ids(
        self, *, user_id: UUID, project_ids: list[UUID]
    ) -> set[UUID]:
        if not project_ids:
            return set()
        vote_cols = getattr(Vote, "__table__").c
        statement = select(vote_cols.project_id).where(
            vote_cols.user_id == user_id,
            vote_cols.project_id.in_(project_ids),
        )
        result = await self.db.exec(statement)
        return {row for row in result.all()}

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

        try:
            return (self._parse_date(raw_from), self._parse_date(raw_to))
        except CursorError:
            return None
