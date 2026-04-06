from datetime import datetime, timezone
from typing import cast
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from app.models.project import Project
from app.models.taxonomy import ProjectCategory
from app.schemas.project import ProjectCreateRequest
from app.schemas.taxonomy import TaxonomyTermResponse
from app.services.project import (
    CursorError,
    ProjectAccessForbiddenError,
    ProjectConflictError,
    ProjectResourceNotFoundError,
    ProjectService,
)
from sqlmodel.ext.asyncio.session import AsyncSession


class DummySession:
    pass


def make_project(*, is_published: bool, created_by_id=None) -> Project:
    now = datetime.now(timezone.utc)
    return Project(
        id=uuid4(),
        created_by_id=created_by_id or uuid4(),
        title="Test Project",
        short_description="Description",
        long_description=None,
        demo_url=None,
        github_url=None,
        video_url=None,
        vote_count=10,
        is_group_project=False,
        is_published=is_published,
        published_at=now if is_published else None,
        created_at=now,
        updated_at=now,
    )


def test_can_view_project_hides_soft_deleted_projects():
    service = ProjectService(cast(AsyncSession, DummySession()))
    owner_id = uuid4()
    project = make_project(is_published=True, created_by_id=owner_id)
    project.deleted_at = datetime.now(timezone.utc)

    assert service.can_view_project(project, current_user_id=owner_id) is False


def test_can_view_project_allows_published_anonymous():
    service = ProjectService(cast(AsyncSession, DummySession()))
    project = make_project(is_published=True)

    assert service.can_view_project(project, current_user_id=None) is True


def test_can_view_project_hides_unpublished_from_anonymous():
    service = ProjectService(cast(AsyncSession, DummySession()))
    project = make_project(is_published=False)

    assert service.can_view_project(project, current_user_id=None) is False


def test_can_view_project_allows_unpublished_owner():
    service = ProjectService(cast(AsyncSession, DummySession()))
    owner_id = uuid4()
    project = make_project(is_published=False, created_by_id=owner_id)

    assert service.can_view_project(project, current_user_id=owner_id) is True


def test_can_view_project_allows_unpublished_member():
    service = ProjectService(cast(AsyncSession, DummySession()))
    project = make_project(is_published=False)

    can_view = service.can_view_project(
        project, current_user_id=uuid4(), member_role="contributor"
    )
    assert can_view is True


def test_can_edit_project_allows_owner():
    service = ProjectService(cast(AsyncSession, DummySession()))
    owner_id = uuid4()
    project = make_project(is_published=False, created_by_id=owner_id)

    assert service.can_edit_project(project, current_user_id=owner_id) is True


def test_can_edit_project_rejects_maintainer():
    service = ProjectService(cast(AsyncSession, DummySession()))
    project = make_project(is_published=False)

    can_edit = service.can_edit_project(
        project, current_user_id=uuid4(), member_role="maintainer"
    )
    assert can_edit is False


def test_can_edit_project_rejects_contributor():
    service = ProjectService(cast(AsyncSession, DummySession()))
    project = make_project(is_published=False)

    can_edit = service.can_edit_project(
        project, current_user_id=uuid4(), member_role="contributor"
    )
    assert can_edit is False


def test_decode_cursor_rejects_malformed_cursor():
    service = ProjectService(cast(AsyncSession, DummySession()))

    with pytest.raises(CursorError, match="Invalid cursor"):
        service._decode_cursor("not-a-valid-cursor", "top")


def test_decode_cursor_rejects_sort_mismatch():
    service = ProjectService(cast(AsyncSession, DummySession()))
    project = make_project(is_published=True)
    top_cursor = service._encode_cursor(
        project,
        "top",
        top_range=(project.created_at.date(), project.created_at.date()),
    )

    with pytest.raises(CursorError, match="Invalid cursor"):
        service._decode_cursor(top_cursor, "new")


@pytest.mark.asyncio
async def test_create_project_skips_taxonomy_assignment_when_create_lists_empty():
    db = AsyncMock()
    db.add = Mock()
    service = ProjectService(cast(AsyncSession, db))
    creator_id = uuid4()
    project_id = uuid4()
    payload = ProjectCreateRequest(
        title="Project Create Empty Taxonomy",
        short_description="Description",
        github_url="https://github.com/example/project",
        categories=[],
        tags=[],
        tech_stack=[],
    )
    detail_stub = type("Detail", (), {"id": project_id})()

    service.get_project_detail = AsyncMock(return_value=detail_stub)  # type: ignore[method-assign]
    replace_spy = AsyncMock(return_value=None)
    service._replace_project_taxonomy_assignments = replace_spy  # type: ignore[method-assign]

    created = await service.create_project(created_by_id=creator_id, payload=payload)

    assert created is detail_stub
    await_args = replace_spy.await_args
    assert await_args is not None
    kwargs = await_args.kwargs
    assert kwargs["categories"] is None
    assert kwargs["tags"] is None
    assert kwargs["tech_stack"] is None


@pytest.mark.asyncio
async def test_replace_join_assignments_invalid_term_fk_field_raises():
    db = AsyncMock()
    service = ProjectService(cast(AsyncSession, db))
    term = TaxonomyTermResponse(id=uuid4(), name="Term")

    with pytest.raises(ValueError, match="Unsupported taxonomy term_fk_field"):
        await service._replace_join_assignments(
            join_model=ProjectCategory,
            term_fk_field="invalid_fk",  # type: ignore[arg-type]
            project_id=uuid4(),
            terms=[term],
        )


@pytest.mark.asyncio
async def test_assert_owner_access_rejects_non_owner():
    service = ProjectService(cast(AsyncSession, DummySession()))
    project = make_project(is_published=False)
    non_owner_id = uuid4()

    service.get_member_role = AsyncMock(return_value="maintainer")  # type: ignore[method-assign]

    with pytest.raises(
        ProjectAccessForbiddenError, match="Project member management forbidden"
    ):
        await service._assert_owner_access(
            project=project, current_user_id=non_owner_id
        )


@pytest.mark.asyncio
async def test_list_project_members_rejects_draft_non_member():
    service = ProjectService(cast(AsyncSession, DummySession()))
    project = make_project(is_published=False)

    service.get_project_by_id = AsyncMock(return_value=project)  # type: ignore[method-assign]
    service.get_member_role = AsyncMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(
        ProjectAccessForbiddenError, match="Project members access forbidden"
    ):
        await service.list_project_members(
            project_id=project.id,
            current_user_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_leave_project_non_member_raises_not_found():
    service = ProjectService(cast(AsyncSession, DummySession()))
    project = make_project(is_published=False)

    service.get_project_by_id = AsyncMock(return_value=project)  # type: ignore[method-assign]
    service.get_project_member = AsyncMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(
        ProjectResourceNotFoundError, match="Project membership not found"
    ):
        await service.leave_project(project_id=project.id, current_user_id=uuid4())


@pytest.mark.asyncio
async def test_leave_project_last_owner_raises_conflict():
    service = ProjectService(cast(AsyncSession, DummySession()))
    owner_id = uuid4()
    project = make_project(is_published=False, created_by_id=owner_id)
    owner_member = type(
        "M",
        (),
        {"role": "owner", "project_id": project.id, "user_id": owner_id},
    )()

    service.get_project_by_id = AsyncMock(return_value=project)  # type: ignore[method-assign]
    service.get_project_member = AsyncMock(return_value=owner_member)  # type: ignore[method-assign]
    service._count_members_by_role = AsyncMock(return_value=1)  # type: ignore[method-assign]

    with pytest.raises(
        ProjectConflictError, match="Last owner cannot leave the project"
    ):
        await service.leave_project(project_id=project.id, current_user_id=owner_id)
