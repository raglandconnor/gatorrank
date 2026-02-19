from datetime import datetime, timezone
from typing import cast
from uuid import uuid4

import pytest
from app.models.project import Project
from app.services.project import CursorError, ProjectService
from sqlmodel.ext.asyncio.session import AsyncSession


class DummySession:
    pass


def make_project(*, is_published: bool, created_by_id=None) -> Project:
    now = datetime.now(timezone.utc)
    return Project(
        id=uuid4(),
        created_by_id=created_by_id or uuid4(),
        title="Test Project",
        description="Description",
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


def test_can_edit_project_allows_maintainer():
    service = ProjectService(cast(AsyncSession, DummySession()))
    project = make_project(is_published=False)

    can_edit = service.can_edit_project(
        project, current_user_id=uuid4(), member_role="maintainer"
    )
    assert can_edit is True


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
    top_cursor = service._encode_cursor(project, "top")

    with pytest.raises(CursorError, match="Cursor sort does not match requested sort"):
        service._decode_cursor(top_cursor, "new")
