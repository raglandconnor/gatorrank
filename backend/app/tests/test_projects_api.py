from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_user_optional
from app.db.database import get_db
from app.main import app
from app.schemas.project import (
    ProjectDetailResponse,
    ProjectListItemResponse,
    ProjectListResponse,
)
from app.services.project import CursorError, ProjectAccessForbiddenError


client = TestClient(app)


def _build_project_response(project_id: UUID) -> ProjectDetailResponse:
    now = datetime.now(timezone.utc)
    return ProjectDetailResponse(
        id=project_id,
        created_by_id=uuid4(),
        title="Project",
        description="Project description",
        demo_url=None,
        github_url=None,
        video_url=None,
        vote_count=5,
        is_group_project=False,
        is_published=True,
        published_at=now,
        created_at=now,
        updated_at=now,
        members=[],
    )


def _build_project_list_response() -> ProjectListResponse:
    now = datetime.now(timezone.utc)
    return ProjectListResponse(
        items=[
            ProjectListItemResponse(
                id=uuid4(),
                created_by_id=uuid4(),
                title="Listed Project",
                description="Listed project description",
                demo_url=None,
                github_url=None,
                video_url=None,
                vote_count=10,
                is_group_project=False,
                is_published=True,
                published_at=now,
                created_at=now,
                updated_at=now,
                members=[],
            )
        ],
        next_cursor="next-cursor-token",
    )


def _assert_service_called_with(
    mock_get_project_detail, project_id: UUID, current_user_id
):
    await_args = mock_get_project_detail.await_args
    assert await_args is not None
    args = await_args.args
    if len(args) == 2:
        assert args[0] == project_id
        assert args[1] == current_user_id
        return
    if len(args) == 3:
        assert args[1] == project_id
        assert args[2] == current_user_id
        return
    raise AssertionError(f"Unexpected call args length: {len(args)}")


async def _override_get_db():
    class MockSession:
        pass

    yield MockSession()


def test_get_project_detail_published_visible_anonymous():
    project_id = uuid4()
    response_model = _build_project_response(project_id)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        with patch(
            "app.api.v1.projects.ProjectService.get_project_detail",
            new=AsyncMock(return_value=response_model),
        ) as mock_get_project_detail:
            response = client.get(f"/api/v1/projects/{project_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(project_id)
    assert payload["title"] == "Project"
    assert payload["members"] == []

    _assert_service_called_with(mock_get_project_detail, project_id, None)


def test_get_project_detail_unpublished_hidden_anonymous():
    project_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        with patch(
            "app.api.v1.projects.ProjectService.get_project_detail",
            new=AsyncMock(return_value=None),
        ):
            response = client.get(f"/api/v1/projects/{project_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_get_project_detail_unpublished_visible_to_member():
    project_id = uuid4()
    member_id = uuid4()
    response_model = _build_project_response(project_id)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: SimpleNamespace(
        id=member_id
    )
    try:
        with patch(
            "app.api.v1.projects.ProjectService.get_project_detail",
            new=AsyncMock(return_value=response_model),
        ) as mock_get_project_detail:
            response = client.get(f"/api/v1/projects/{project_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    _assert_service_called_with(mock_get_project_detail, project_id, member_id)


def test_get_project_detail_not_found_returns_404():
    project_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        with patch(
            "app.api.v1.projects.ProjectService.get_project_detail",
            new=AsyncMock(return_value=None),
        ):
            response = client.get(f"/api/v1/projects/{project_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_get_project_detail_forbidden_returns_403():
    project_id = uuid4()
    stranger_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: SimpleNamespace(
        id=stranger_id
    )
    try:
        with patch(
            "app.api.v1.projects.ProjectService.get_project_detail",
            new=AsyncMock(
                side_effect=ProjectAccessForbiddenError("Project access forbidden")
            ),
        ):
            response = client.get(f"/api/v1/projects/{project_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project access forbidden"


def test_list_projects_default_sort_top():
    response_model = _build_project_list_response()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with patch(
            "app.api.v1.projects.ProjectService.list_projects",
            new=AsyncMock(return_value=response_model),
        ) as mock_list_projects:
            response = client.get("/api/v1/projects")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["next_cursor"] == "next-cursor-token"
    assert len(payload["items"]) == 1

    await_args = mock_list_projects.await_args
    assert await_args is not None
    kwargs = await_args.kwargs
    assert kwargs["sort"] == "top"
    assert kwargs["limit"] == 20
    assert kwargs["cursor"] is None
    assert kwargs["published_from"] is None
    assert kwargs["published_to"] is None


def test_list_projects_passes_sort_limit_and_cursor():
    response_model = _build_project_list_response()
    cursor = "abc123"

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with patch(
            "app.api.v1.projects.ProjectService.list_projects",
            new=AsyncMock(return_value=response_model),
        ) as mock_list_projects:
            response = client.get("/api/v1/projects?sort=new&limit=5&cursor=abc123")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    await_args = mock_list_projects.await_args
    assert await_args is not None
    kwargs = await_args.kwargs
    assert kwargs["sort"] == "new"
    assert kwargs["limit"] == 5
    assert kwargs["cursor"] == cursor
    assert kwargs["published_from"] is None
    assert kwargs["published_to"] is None


def test_list_projects_passes_top_date_range():
    response_model = _build_project_list_response()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with patch(
            "app.api.v1.projects.ProjectService.list_projects",
            new=AsyncMock(return_value=response_model),
        ) as mock_list_projects:
            response = client.get(
                "/api/v1/projects?sort=top&published_from=2025-01-01&published_to=2025-03-31"
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    await_args = mock_list_projects.await_args
    assert await_args is not None
    kwargs = await_args.kwargs
    assert str(kwargs["published_from"]) == "2025-01-01"
    assert str(kwargs["published_to"]) == "2025-03-31"


def test_list_projects_invalid_cursor_returns_400():
    app.dependency_overrides[get_db] = _override_get_db
    try:
        with patch(
            "app.api.v1.projects.ProjectService.list_projects",
            new=AsyncMock(side_effect=CursorError("Invalid cursor")),
        ):
            response = client.get("/api/v1/projects?cursor=bad")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid cursor"
