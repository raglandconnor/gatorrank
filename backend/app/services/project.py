from datetime import UTC, date, datetime, time, timedelta
import re
from typing import Literal
import unicodedata
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
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
from app.models.taxonomy import (
    Category,
    ProjectCategory,
    ProjectTag,
    ProjectTechStack,
    Tag,
    TechStack,
)
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
from app.schemas.taxonomy import TaxonomyTermResponse
from app.services.taxonomy import normalize_taxonomy_name
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
    _MAX_SLUG_RETRY_ATTEMPTS = 8

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_project_by_id(
        self, project_id: UUID, *, include_deleted: bool = False
    ) -> Project | None:
        project_cols = getattr(Project, "__table__").c
        statement = select(Project).where(project_cols.id == project_id)
        if not include_deleted:
            statement = statement.where(project_cols.deleted_at.is_(None))
        result = await self.db.exec(statement)
        return result.first()

    async def get_project_by_slug(
        self, slug: str, *, include_deleted: bool = False
    ) -> Project | None:
        normalized_slug = slug.strip().lower()
        project_cols = getattr(Project, "__table__").c
        statement = select(Project).where(project_cols.slug == normalized_slug)
        if not include_deleted:
            statement = statement.where(project_cols.deleted_at.is_(None))
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
        for _ in range(self._MAX_SLUG_RETRY_ATTEMPTS):
            slug = await self._generate_unique_slug(payload.title)
            project = Project(  # pyright: ignore[reportCallIssue]
                created_by_id=created_by_id,
                title=payload.title,
                slug=slug,
                short_description=payload.short_description,
                long_description=payload.long_description,
                demo_url=payload.demo_url,
                github_url=payload.github_url,
                video_url=payload.video_url,
                timeline_start_date=payload.timeline_start_date,
                timeline_end_date=payload.timeline_end_date,
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
                await self.db.flush()
                create_categories = payload.categories or None
                create_tags = payload.tags or None
                create_tech_stack = payload.tech_stack or None
                await self._replace_project_taxonomy_assignments(
                    project_id=project.id,
                    categories=create_categories,
                    tags=create_tags,
                    tech_stack=create_tech_stack,
                )
                await self.db.commit()
            except IntegrityError as exc:
                await self.db.rollback()
                if self._is_project_slug_conflict(exc):
                    continue
                raise
            except Exception:
                await self.db.rollback()
                raise

            created = await self.get_project_detail(project.id, created_by_id)
            if created is None:
                raise RuntimeError("Created project could not be loaded")
            return created

        raise RuntimeError("Project slug generation failed after retry attempts")

    async def soft_delete_project(
        self, project_id: UUID, current_user_id: UUID
    ) -> bool:
        project = await self.get_project_by_id(project_id, include_deleted=True)
        if project is None:
            return False

        if project.deleted_at is not None:
            return project.created_by_id == current_user_id

        if project.created_by_id != current_user_id:
            raise ProjectAccessForbiddenError("Project access forbidden")

        project.deleted_at = datetime.now(UTC)
        try:
            self.db.add(project)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return True

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
        final_timeline_start_date = (
            payload.timeline_start_date
            if "timeline_start_date" in payload.model_fields_set
            else project.timeline_start_date
        )
        final_timeline_end_date = (
            payload.timeline_end_date
            if "timeline_end_date" in payload.model_fields_set
            else project.timeline_end_date
        )
        if not any([final_demo_url, final_github_url, final_video_url]):
            raise ProjectValidationError(
                "Provide at least one of demo_url, github_url, or video_url."
            )
        if final_timeline_end_date is not None and final_timeline_start_date is None:
            raise ProjectValidationError(
                "timeline_end_date requires timeline_start_date."
            )
        if (
            final_timeline_start_date is not None
            and final_timeline_end_date is not None
            and final_timeline_start_date > final_timeline_end_date
        ):
            raise ProjectValidationError(
                "timeline_start_date must be on or before timeline_end_date."
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
        if "timeline_start_date" in payload.model_fields_set:
            project.timeline_start_date = payload.timeline_start_date
        if "timeline_end_date" in payload.model_fields_set:
            project.timeline_end_date = payload.timeline_end_date

        categories: list[str] | None = None
        tags: list[str] | None = None
        tech_stack: list[str] | None = None
        if "categories" in payload.model_fields_set:
            categories = payload.categories
        if "tags" in payload.model_fields_set:
            tags = payload.tags
        if "tech_stack" in payload.model_fields_set:
            tech_stack = payload.tech_stack

        try:
            self.db.add(project)
            await self.db.flush()
            await self._replace_project_taxonomy_assignments(
                project_id=project.id,
                categories=categories,
                tags=tags,
                tech_stack=tech_stack,
            )
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
        if project.deleted_at is not None:
            return False
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
        taxonomy_by_project = await self._get_project_taxonomy_by_project_ids(
            [project.id]
        )
        taxonomy = taxonomy_by_project.get(project.id, self._empty_taxonomy_payload())
        viewer_has_voted = False
        if project.is_published and current_user_id is not None:
            viewer_has_voted = await self._viewer_has_voted(project.id, current_user_id)
        return ProjectDetailResponse(
            **project.model_dump(),
            members=members,
            team_size=len(members),
            viewer_has_voted=viewer_has_voted,
            categories=taxonomy["categories"],
            tags=taxonomy["tags"],
            tech_stack=taxonomy["tech_stack"],
        )

    async def get_project_detail_by_slug(
        self,
        slug: str,
        current_user_id: UUID | None,
    ) -> ProjectDetailResponse | None:
        project = await self.get_project_by_slug(slug)
        if project is None:
            return None
        return await self.get_project_detail(project.id, current_user_id)

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
        taxonomy_by_project = await self._get_project_taxonomy_by_project_ids(
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
                members_by_project,
                taxonomy_by_project,
                voted_project_ids,
            )
            for project in projects
        ]

        next_cursor: str | None = None
        if has_more and projects:
            next_cursor = self._encode_cursor(projects[-1], sort, top_range=top_range)

        return ProjectListResponse(items=items, next_cursor=next_cursor)

    async def _replace_project_taxonomy_assignments(
        self,
        *,
        project_id: UUID,
        categories: list[str] | None,
        tags: list[str] | None,
        tech_stack: list[str] | None,
    ) -> None:
        if categories is not None:
            category_terms = await self._resolve_or_create_terms(Category, categories)
            await self._replace_join_assignments(
                join_model=ProjectCategory,
                term_fk_field="category_id",
                project_id=project_id,
                terms=category_terms,
            )
        if tags is not None:
            tag_terms = await self._resolve_or_create_terms(Tag, tags)
            await self._replace_join_assignments(
                join_model=ProjectTag,
                term_fk_field="tag_id",
                project_id=project_id,
                terms=tag_terms,
            )
        if tech_stack is not None:
            tech_stack_terms = await self._resolve_or_create_terms(
                TechStack, tech_stack
            )
            await self._replace_join_assignments(
                join_model=ProjectTechStack,
                term_fk_field="tech_stack_id",
                project_id=project_id,
                terms=tech_stack_terms,
            )

    async def _resolve_or_create_terms(
        self,
        model: type[Category] | type[Tag] | type[TechStack],
        values: list[str],
    ) -> list[TaxonomyTermResponse]:
        terms: list[TaxonomyTermResponse] = []
        for value in values:
            normalized_name = normalize_taxonomy_name(value)
            model_cols = getattr(model, "__table__").c
            existing_statement = select(model).where(
                model_cols.normalized_name == normalized_name
            )
            existing_result = await self.db.exec(existing_statement)
            existing = existing_result.first()
            if existing is not None:
                terms.append(TaxonomyTermResponse.model_validate(existing))
                continue

            insert_statement = (
                pg_insert(getattr(model, "__table__"))
                .values(name=value.strip(), normalized_name=normalized_name)
                .on_conflict_do_nothing(index_elements=["normalized_name"])
                .returning(model_cols.id, model_cols.name)
            )
            insert_result = await self.db.exec(insert_statement)
            inserted = insert_result.first()
            if inserted is not None:
                terms.append(TaxonomyTermResponse(id=inserted.id, name=inserted.name))
                continue

            race_result = await self.db.exec(existing_statement)
            raced_existing = race_result.first()
            if raced_existing is None:
                raise RuntimeError("Taxonomy term could not be resolved")
            terms.append(TaxonomyTermResponse.model_validate(raced_existing))

        return terms

    async def _replace_join_assignments(
        self,
        *,
        join_model: type[ProjectCategory] | type[ProjectTag] | type[ProjectTechStack],
        term_fk_field: Literal["category_id", "tag_id", "tech_stack_id"],
        project_id: UUID,
        terms: list[TaxonomyTermResponse],
    ) -> None:
        join_cols = getattr(join_model, "__table__").c
        delete_statement = sa.delete(join_model).where(
            join_cols.project_id == project_id
        )
        await self.db.exec(delete_statement)

        for position, term in enumerate(terms):
            if term_fk_field == "category_id":
                assignment = ProjectCategory(  # pyright: ignore[reportCallIssue]
                    project_id=project_id,
                    category_id=term.id,
                    position=position,
                )
            elif term_fk_field == "tag_id":
                assignment = ProjectTag(  # pyright: ignore[reportCallIssue]
                    project_id=project_id,
                    tag_id=term.id,
                    position=position,
                )
            elif term_fk_field == "tech_stack_id":
                assignment = ProjectTechStack(  # pyright: ignore[reportCallIssue]
                    project_id=project_id,
                    tech_stack_id=term.id,
                    position=position,
                )
            else:
                raise ValueError(f"Unsupported taxonomy term_fk_field: {term_fk_field}")
            self.db.add(assignment)

    async def _get_project_taxonomy_by_project_ids(
        self, project_ids: list[UUID]
    ) -> dict[UUID, dict[str, list[TaxonomyTermResponse]]]:
        if not project_ids:
            return {}

        payload = {
            project_id: self._empty_taxonomy_payload() for project_id in project_ids
        }

        project_category_cols = getattr(ProjectCategory, "__table__").c
        category_cols = getattr(Category, "__table__").c
        category_statement = (
            select(ProjectCategory, Category)
            .join(Category, category_cols.id == project_category_cols.category_id)
            .where(project_category_cols.project_id.in_(project_ids))
            .order_by(
                project_category_cols.project_id.asc(),
                project_category_cols.position.asc(),
            )
        )
        category_result = await self.db.exec(category_statement)
        for assignment, category in category_result.all():
            payload[assignment.project_id]["categories"].append(
                TaxonomyTermResponse.model_validate(category)
            )

        project_tag_cols = getattr(ProjectTag, "__table__").c
        tag_cols = getattr(Tag, "__table__").c
        tag_statement = (
            select(ProjectTag, Tag)
            .join(Tag, tag_cols.id == project_tag_cols.tag_id)
            .where(project_tag_cols.project_id.in_(project_ids))
            .order_by(
                project_tag_cols.project_id.asc(),
                project_tag_cols.position.asc(),
            )
        )
        tag_result = await self.db.exec(tag_statement)
        for assignment, tag in tag_result.all():
            payload[assignment.project_id]["tags"].append(
                TaxonomyTermResponse.model_validate(tag)
            )

        project_tech_stack_cols = getattr(ProjectTechStack, "__table__").c
        tech_stack_cols = getattr(TechStack, "__table__").c
        tech_stack_statement = (
            select(ProjectTechStack, TechStack)
            .join(
                TechStack,
                tech_stack_cols.id == project_tech_stack_cols.tech_stack_id,
            )
            .where(project_tech_stack_cols.project_id.in_(project_ids))
            .order_by(
                project_tech_stack_cols.project_id.asc(),
                project_tech_stack_cols.position.asc(),
            )
        )
        tech_stack_result = await self.db.exec(tech_stack_statement)
        for assignment, tech_stack in tech_stack_result.all():
            payload[assignment.project_id]["tech_stack"].append(
                TaxonomyTermResponse.model_validate(tech_stack)
            )

        return payload

    @staticmethod
    def _empty_taxonomy_payload() -> dict[str, list[TaxonomyTermResponse]]:
        return {
            "categories": [],
            "tags": [],
            "tech_stack": [],
        }

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
        stmt = select(Project).where(
            project_cols.is_published.is_(True),
            project_cols.deleted_at.is_(None),
        )
        if created_by_id:
            stmt = stmt.where(project_cols.created_by_id == created_by_id)
        return stmt

    async def _get_members_for_projects(
        self, project_ids: list[UUID]
    ) -> dict[UUID, list[ProjectMemberInfo]]:
        return await get_members_for_projects(self.db, project_ids)

    @staticmethod
    def _to_project_list_item(
        project: Project,
        members_by_project: dict[UUID, list[ProjectMemberInfo]],
        taxonomy_by_project: dict[UUID, dict[str, list[TaxonomyTermResponse]]],
        voted_project_ids: set[UUID],
    ) -> ProjectListItemResponse:
        members = members_by_project.get(project.id, [])
        taxonomy = taxonomy_by_project.get(
            project.id, ProjectService._empty_taxonomy_payload()
        )
        return ProjectListItemResponse(
            **project.model_dump(),
            members=members,
            team_size=len(members),
            viewer_has_voted=project.id in voted_project_ids,
            categories=taxonomy["categories"],
            tags=taxonomy["tags"],
            tech_stack=taxonomy["tech_stack"],
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

    async def _generate_unique_slug(self, title: str) -> str:
        base_slug = self._build_slug_base(title)
        project_cols = getattr(Project, "__table__").c
        statement = select(project_cols.slug).where(
            sa.or_(
                project_cols.slug == base_slug,
                project_cols.slug.like(f"{base_slug}-%"),
            )
        )
        existing_result = await self.db.exec(statement)
        existing_slugs = {slug for slug in existing_result.all()}
        if base_slug not in existing_slugs:
            return base_slug

        pattern = re.compile(rf"^{re.escape(base_slug)}-(\d+)$")
        max_suffix = 1
        for existing_slug in existing_slugs:
            match = pattern.match(existing_slug)
            if match is None:
                continue
            suffix = int(match.group(1))
            if suffix > max_suffix:
                max_suffix = suffix
        return f"{base_slug}-{max_suffix + 1}"

    @staticmethod
    def _build_slug_base(title: str) -> str:
        transliterated = (
            unicodedata.normalize("NFKD", title)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        lowered = transliterated.strip().lower()
        hyphenated = re.sub(r"[^a-z0-9]+", "-", lowered)
        collapsed = re.sub(r"-{2,}", "-", hyphenated).strip("-")
        return collapsed or "project"

    @staticmethod
    def _is_project_slug_conflict(exc: IntegrityError) -> bool:
        orig = getattr(exc, "orig", None)
        diag = getattr(orig, "diag", None)
        constraint_name = getattr(diag, "constraint_name", None)
        if constraint_name in {"uq_projects_slug", "projects_slug_key"}:
            return True

        message = str(orig or exc).lower()
        return "projects" in message and "slug" in message and "unique" in message
