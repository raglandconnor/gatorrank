from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_user, get_current_user_optional
from app.db.database import get_db
from app.main import app
from app.schemas.project import (
    ProjectDetailResponse,
    ProjectListItemResponse,
    ProjectListResponse,
    ProjectMemberInfo,
)
from app.services.project import (
    CursorError,
    ProjectAccessForbiddenError,
    ProjectConflictError,
    ProjectResourceNotFoundError,
    ProjectValidationError,
)


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


def _build_create_project_payload(**overrides):
    payload = {
        "title": " New Project ",
        "description": "  A project description  ",
        "github_url": "https://github.com/example/repo",
    }
    payload.update(overrides)
    return payload


def _build_update_project_payload(**overrides):
    payload = {
        "title": "  Updated Project Title  ",
        "description": "  Updated project description  ",
        "demo_url": "https://example.com/demo",
    }
    payload.update(overrides)
    return payload


def _build_draft_project_response(
    project_id: UUID, created_by_id: UUID
) -> ProjectDetailResponse:
    now = datetime.now(timezone.utc)
    return ProjectDetailResponse(
        id=project_id,
        created_by_id=created_by_id,
        title="New Project",
        description="A project description",
        demo_url=None,
        github_url="https://github.com/example/repo",
        video_url=None,
        vote_count=0,
        is_group_project=False,
        is_published=False,
        published_at=None,
        created_at=now,
        updated_at=now,
        members=[
            ProjectMemberInfo(
                user_id=created_by_id,
                role="owner",
                full_name=None,
                profile_picture_url=None,
            )
        ],
    )


def _build_member_info(user_id: UUID, role: str = "contributor") -> ProjectMemberInfo:
    return ProjectMemberInfo(
        user_id=user_id,
        role=role,
        full_name="Member Name",
        profile_picture_url="https://example.com/avatar.png",
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


def _override_current_user(user_id: UUID):
    return lambda: SimpleNamespace(id=user_id, email="creator@ufl.edu")


def test_create_project_returns_201_and_payload():
    user_id = uuid4()
    project_id = uuid4()
    response_model = _build_draft_project_response(project_id, user_id)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.create_project",
            new=AsyncMock(return_value=response_model),
        ):
            response = client.post(
                "/api/v1/projects", json=_build_create_project_payload()
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == str(project_id)
    assert payload["created_by_id"] == str(user_id)
    assert payload["is_published"] is False
    assert payload["published_at"] is None
    assert payload["members"][0]["role"] == "owner"


def test_create_project_requires_auth():
    response = client.post("/api/v1/projects", json=_build_create_project_payload())

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_create_project_passes_user_and_payload_to_service():
    user_id = uuid4()
    project_id = uuid4()
    response_model = _build_draft_project_response(project_id, user_id)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.create_project",
            new=AsyncMock(return_value=response_model),
        ) as mock_create_project:
            response = client.post(
                "/api/v1/projects", json=_build_create_project_payload()
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    await_args = mock_create_project.await_args
    assert await_args is not None
    kwargs = await_args.kwargs
    assert kwargs["created_by_id"] == user_id
    assert kwargs["payload"].title == "New Project"
    assert kwargs["payload"].description == "A project description"
    assert kwargs["payload"].github_url == "https://github.com/example/repo"


def test_create_project_validation_missing_title_returns_422():
    user_id = uuid4()
    payload = _build_create_project_payload()
    payload.pop("title")

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.create_project",
            new=AsyncMock(),
        ) as mock_create_project:
            response = client.post("/api/v1/projects", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert mock_create_project.await_count == 0


def test_create_project_validation_blank_title_returns_422():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.create_project",
            new=AsyncMock(),
        ) as mock_create_project:
            response = client.post(
                "/api/v1/projects",
                json=_build_create_project_payload(title="   "),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert mock_create_project.await_count == 0


def test_create_project_validation_missing_description_returns_422():
    user_id = uuid4()
    payload = _build_create_project_payload()
    payload.pop("description")

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.create_project",
            new=AsyncMock(),
        ) as mock_create_project:
            response = client.post("/api/v1/projects", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert mock_create_project.await_count == 0


def test_create_project_validation_blank_description_returns_422():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.create_project",
            new=AsyncMock(),
        ) as mock_create_project:
            response = client.post(
                "/api/v1/projects",
                json=_build_create_project_payload(description="   "),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert mock_create_project.await_count == 0


def test_create_project_rejects_is_group_project_field_returns_422():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.create_project",
            new=AsyncMock(),
        ) as mock_create_project:
            response = client.post(
                "/api/v1/projects",
                json=_build_create_project_payload(is_group_project=True),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert mock_create_project.await_count == 0


def test_create_project_validation_requires_at_least_one_project_url():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.create_project",
            new=AsyncMock(),
        ) as mock_create_project:
            response = client.post(
                "/api/v1/projects",
                json=_build_create_project_payload(
                    demo_url=None,
                    github_url=None,
                    video_url=None,
                ),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert mock_create_project.await_count == 0
    errors = response.json()["detail"]
    assert any(
        "Provide at least one of demo_url, github_url, or video_url."
        in str(error.get("msg", ""))
        for error in errors
    )


def test_create_project_validation_invalid_url_returns_422():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.create_project",
            new=AsyncMock(),
        ) as mock_create_project:
            response = client.post(
                "/api/v1/projects",
                json=_build_create_project_payload(github_url="not-a-url"),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert mock_create_project.await_count == 0


def test_create_project_validation_accepts_http_and_https_urls():
    user_id = uuid4()
    project_id = uuid4()
    response_model = _build_draft_project_response(project_id, user_id)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.create_project",
            new=AsyncMock(return_value=response_model),
        ) as mock_create_project:
            response = client.post(
                "/api/v1/projects",
                json=_build_create_project_payload(
                    demo_url="http://example.com/demo",
                    github_url=None,
                    video_url="https://example.com/video",
                ),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    await_args = mock_create_project.await_args
    assert await_args is not None
    payload = await_args.kwargs["payload"]
    assert payload.demo_url == "http://example.com/demo"
    assert payload.video_url == "https://example.com/video"


def test_create_project_normalizes_empty_optional_urls_to_none():
    user_id = uuid4()
    project_id = uuid4()
    response_model = _build_draft_project_response(project_id, user_id)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.create_project",
            new=AsyncMock(return_value=response_model),
        ) as mock_create_project:
            response = client.post(
                "/api/v1/projects",
                json=_build_create_project_payload(
                    demo_url="  ",
                    github_url="https://github.com/example/repo",
                    video_url="",
                ),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    await_args = mock_create_project.await_args
    assert await_args is not None
    payload = await_args.kwargs["payload"]
    assert payload.demo_url is None
    assert payload.github_url == "https://github.com/example/repo"
    assert payload.video_url is None


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


def test_update_project_returns_200_and_payload():
    user_id = uuid4()
    project_id = uuid4()
    response_model = _build_project_response(project_id)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.update_project",
            new=AsyncMock(return_value=response_model),
        ) as mock_update_project:
            response = client.patch(
                f"/api/v1/projects/{project_id}",
                json=_build_update_project_payload(),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(project_id)

    await_args = mock_update_project.await_args
    assert await_args is not None
    kwargs = await_args.kwargs
    assert kwargs["project_id"] == project_id
    assert kwargs["current_user_id"] == user_id
    assert kwargs["payload"].title == "Updated Project Title"
    assert kwargs["payload"].description == "Updated project description"
    assert kwargs["payload"].demo_url == "https://example.com/demo"


def test_update_project_requires_auth():
    response = client.patch(
        f"/api/v1/projects/{uuid4()}",
        json=_build_update_project_payload(),
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_update_project_empty_payload_returns_422():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.update_project",
            new=AsyncMock(),
        ) as mock_update_project:
            response = client.patch(f"/api/v1/projects/{uuid4()}", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert mock_update_project.await_count == 0


def test_update_project_rejects_non_editable_field_returns_422():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.update_project",
            new=AsyncMock(),
        ) as mock_update_project:
            response = client.patch(
                f"/api/v1/projects/{uuid4()}",
                json={"is_group_project": True, "title": "Updated"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert mock_update_project.await_count == 0


def test_update_project_not_found_returns_404():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.update_project",
            new=AsyncMock(return_value=None),
        ):
            response = client.patch(
                f"/api/v1/projects/{uuid4()}",
                json=_build_update_project_payload(),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_update_project_forbidden_returns_403():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.update_project",
            new=AsyncMock(
                side_effect=ProjectAccessForbiddenError("Project edit forbidden")
            ),
        ):
            response = client.patch(
                f"/api/v1/projects/{uuid4()}",
                json=_build_update_project_payload(),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project edit forbidden"


def test_update_project_validation_error_returns_422():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.update_project",
            new=AsyncMock(
                side_effect=ProjectValidationError(
                    "Provide at least one of demo_url, github_url, or video_url."
                )
            ),
        ):
            response = client.patch(
                f"/api/v1/projects/{uuid4()}",
                json={"demo_url": None, "github_url": None, "video_url": None},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Provide at least one of demo_url, github_url, or video_url."
    )


def test_publish_project_returns_200_and_payload():
    user_id = uuid4()
    project_id = uuid4()
    response_model = _build_project_response(project_id)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.publish_project",
            new=AsyncMock(return_value=response_model),
        ) as mock_publish_project:
            response = client.post(f"/api/v1/projects/{project_id}/publish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(project_id)

    await_args = mock_publish_project.await_args
    assert await_args is not None
    kwargs = await_args.kwargs
    assert kwargs["project_id"] == project_id
    assert kwargs["current_user_id"] == user_id


def test_publish_project_requires_auth():
    response = client.post(f"/api/v1/projects/{uuid4()}/publish")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_publish_project_not_found_returns_404():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.publish_project",
            new=AsyncMock(return_value=None),
        ):
            response = client.post(f"/api/v1/projects/{uuid4()}/publish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_publish_project_forbidden_returns_403():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.publish_project",
            new=AsyncMock(
                side_effect=ProjectAccessForbiddenError("Project publish forbidden")
            ),
        ):
            response = client.post(f"/api/v1/projects/{uuid4()}/publish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project publish forbidden"


def test_unpublish_project_returns_200_and_payload():
    user_id = uuid4()
    project_id = uuid4()
    response_model = _build_project_response(project_id)
    response_model.is_published = False
    response_model.published_at = None

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.unpublish_project",
            new=AsyncMock(return_value=response_model),
        ) as mock_unpublish_project:
            response = client.post(f"/api/v1/projects/{project_id}/unpublish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(project_id)
    assert payload["is_published"] is False
    assert payload["published_at"] is None

    await_args = mock_unpublish_project.await_args
    assert await_args is not None
    kwargs = await_args.kwargs
    assert kwargs["project_id"] == project_id
    assert kwargs["current_user_id"] == user_id


def test_unpublish_project_requires_auth():
    response = client.post(f"/api/v1/projects/{uuid4()}/unpublish")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_unpublish_project_not_found_returns_404():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.unpublish_project",
            new=AsyncMock(return_value=None),
        ):
            response = client.post(f"/api/v1/projects/{uuid4()}/unpublish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_unpublish_project_forbidden_returns_403():
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.unpublish_project",
            new=AsyncMock(
                side_effect=ProjectAccessForbiddenError("Project unpublish forbidden")
            ),
        ):
            response = client.post(f"/api/v1/projects/{uuid4()}/unpublish")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Project unpublish forbidden"


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


def test_list_project_members_returns_200():
    project_id = uuid4()
    member = _build_member_info(uuid4(), role="maintainer")

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        with patch(
            "app.api.v1.projects.ProjectService.list_project_members",
            new=AsyncMock(return_value=[member]),
        ):
            response = client.get(f"/api/v1/projects/{project_id}/members")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["user_id"] == str(member.user_id)
    assert payload[0]["role"] == "maintainer"


def test_add_project_member_returns_201():
    project_id = uuid4()
    owner_id = uuid4()
    member = _build_member_info(uuid4(), role="contributor")

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(owner_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.add_project_member",
            new=AsyncMock(return_value=member),
        ) as mock_add_member:
            response = client.post(
                f"/api/v1/projects/{project_id}/members",
                json={"email": "  NEWMEMBER@UFL.EDU ", "role": "contributor"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["user_id"] == str(member.user_id)
    await_args = mock_add_member.await_args
    assert await_args is not None
    kwargs = await_args.kwargs
    assert kwargs["project_id"] == project_id
    assert kwargs["current_user_id"] == owner_id
    assert kwargs["payload"].email == "newmember@ufl.edu"
    assert kwargs["payload"].role == "contributor"


def test_add_project_member_conflict_returns_409():
    project_id = uuid4()
    owner_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(owner_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.add_project_member",
            new=AsyncMock(
                side_effect=ProjectConflictError(
                    "User is already a member of this project"
                )
            ),
        ):
            response = client.post(
                f"/api/v1/projects/{project_id}/members",
                json={"email": "member@ufl.edu", "role": "contributor"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == "User is already a member of this project"


def test_update_project_member_returns_200():
    project_id = uuid4()
    target_user_id = uuid4()
    owner_id = uuid4()
    member = _build_member_info(target_user_id, role="maintainer")

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(owner_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.update_project_member",
            new=AsyncMock(return_value=member),
        ) as mock_update_member:
            response = client.patch(
                f"/api/v1/projects/{project_id}/members/{target_user_id}",
                json={"role": "maintainer"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["role"] == "maintainer"
    await_args = mock_update_member.await_args
    assert await_args is not None
    kwargs = await_args.kwargs
    assert kwargs["project_id"] == project_id
    assert kwargs["target_user_id"] == target_user_id
    assert kwargs["current_user_id"] == owner_id
    assert kwargs["payload"].role == "maintainer"


def test_remove_project_member_returns_204():
    project_id = uuid4()
    target_user_id = uuid4()
    owner_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(owner_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.remove_project_member",
            new=AsyncMock(return_value=True),
        ):
            response = client.delete(
                f"/api/v1/projects/{project_id}/members/{target_user_id}"
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""


def test_leave_project_last_owner_returns_409():
    project_id = uuid4()
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.leave_project",
            new=AsyncMock(side_effect=ProjectConflictError("Last owner cannot leave")),
        ):
            response = client.post(f"/api/v1/projects/{project_id}/leave")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == "Last owner cannot leave"


def test_leave_project_not_member_returns_404():
    project_id = uuid4()
    user_id = uuid4()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user(user_id)
    try:
        with patch(
            "app.api.v1.projects.ProjectService.leave_project",
            new=AsyncMock(
                side_effect=ProjectResourceNotFoundError("Project membership not found")
            ),
        ):
            response = client.post(f"/api/v1/projects/{project_id}/leave")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Project membership not found"
