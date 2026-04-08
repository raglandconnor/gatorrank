from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import get_current_user, get_current_user_optional
from app.api.deps.search import get_project_search_request, get_search_service
from app.db.database import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectMemberCreateRequest,
    ProjectMemberInfo,
    ProjectMemberUpdateRequest,
    ProjectUpdateRequest,
)
from app.schemas.search import ProjectSearchRequest, ProjectSearchResponse
from app.services.project import (
    CursorError,
    ProjectAccessForbiddenError,
    ProjectConflictError,
    ProjectResourceNotFoundError,
    ProjectService,
    ProjectValidationError,
)
from app.services.search import SearchService
from app.services.vote import VoteService, VoteTargetNotFoundError

router = APIRouter()


@router.post(
    "/projects",
    summary="Create project draft",
    description=(
        "Create a draft project and auto-generate an immutable slug from the normalized "
        "project title (`trim + lowercase + hyphenate` after transliteration). "
        "If the slug collides, deterministic numeric suffixes are applied "
        "(`slug`, `slug-2`, `slug-3`, ...)."
    ),
    response_model=ProjectDetailResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        422: {
            "description": (
                "Validation error (for example: missing/blank title or "
                "short_description, invalid URL format, invalid timeline "
                "dates/order, or no demo/github/video URL provided). URL domains "
                "are not restricted beyond valid http(s) format."
            )
        },
    },
)
async def create_project(
    payload: ProjectCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectDetailResponse:
    """Create a draft project and add the creator as the owner member.

    This endpoint always creates a draft (`is_published=false`).
    """
    service = ProjectService(db)
    return await service.create_project(created_by_id=current_user.id, payload=payload)


@router.get(
    "/projects/slug/{slug}",
    summary="Get project detail by slug",
    description=(
        "Return project details for the provided immutable project slug, including computed "
        "`team_size` and taxonomy fields (`categories`, `tags`, `tech_stack`). "
        "Visibility semantics match `GET /projects/{project_id}`."
    ),
    response_model=ProjectDetailResponse,
    responses={
        403: {"description": "Authenticated user cannot access this draft project"},
        404: {
            "description": "Project not found (or hidden draft for anonymous requester)"
        },
    },
)
async def get_project_detail_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ProjectDetailResponse:
    """Return project details by immutable slug with team and taxonomy parity."""
    service = ProjectService(db)
    current_user_id = current_user.id if current_user else None
    try:
        project = await service.get_project_detail_by_slug(slug, current_user_id)
    except ProjectAccessForbiddenError as exc:
        raise HTTPException(status_code=403, detail="Project access forbidden") from exc
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get(
    "/projects/search",
    summary="Search published projects",
    description=(
        "Search published, non-deleted projects using optional keyword query and taxonomy "
        "filters with cursor pagination. Keyword matching is case-insensitive and limited "
        "to `title` + `short_description`. Taxonomy filters apply OR logic within each "
        "family and AND logic across families. Unknown taxonomy terms are treated as "
        "non-matching values (not validation errors). "
        "For `sort=top`, published date-window defaults match the feed (last 90 days). "
        "Relevance sophistication is intentionally deferred in v1."
    ),
    response_model=ProjectSearchResponse,
    responses={
        400: {"description": "Invalid cursor or date range"},
        401: {"description": "Invalid or expired bearer token"},
    },
)
async def search_projects(
    request: ProjectSearchRequest = Depends(get_project_search_request),
    search_service: SearchService = Depends(get_search_service),
    current_user: User | None = Depends(get_current_user_optional),
) -> ProjectSearchResponse:
    """Search published projects with keyword/taxonomy filters and cursor pagination."""
    try:
        return await search_service.search_projects(
            request=request,
            current_user_id=current_user.id if current_user else None,
        )
    except CursorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/projects/{project_id}",
    summary="Get project detail",
    description=(
        "Return project details if visible to the current requester, including "
        "computed `team_size` from active project memberships and taxonomy fields "
        "(`categories`, `tags`, `tech_stack`)."
    ),
    response_model=ProjectDetailResponse,
    responses={
        403: {"description": "Authenticated user cannot access this draft project"},
        404: {
            "description": "Project not found (or hidden draft for anonymous requester)"
        },
    },
)
async def get_project_detail(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ProjectDetailResponse:
    """Return project details with team and taxonomy parity when requester can view."""
    service = ProjectService(db)
    current_user_id = current_user.id if current_user else None
    try:
        project = await service.get_project_detail(project_id, current_user_id)
    except ProjectAccessForbiddenError as exc:
        raise HTTPException(status_code=403, detail="Project access forbidden") from exc
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete(
    "/projects/{project_id}",
    summary="Soft delete project",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Only the owner can delete this project"},
        404: {"description": "Project not found"},
    },
)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    service = ProjectService(db)
    try:
        deleted = await service.soft_delete_project(project_id, current_user.id)
    except ProjectAccessForbiddenError as exc:
        raise HTTPException(status_code=403, detail="Project access forbidden") from exc

    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/projects/{project_id}/members",
    summary="List project members",
    description=(
        "Return members for a project. Published projects are visible publicly; "
        "draft projects are visible only to authenticated project members."
    ),
    response_model=list[ProjectMemberInfo],
    responses={
        403: {
            "description": "Authenticated user cannot access this draft project's members"
        },
        404: {
            "description": "Project not found (or hidden draft for anonymous requester)"
        },
    },
)
async def list_project_members(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[ProjectMemberInfo]:
    """List members for a project when the requester has project visibility."""
    service = ProjectService(db)
    current_user_id = current_user.id if current_user else None
    try:
        members = await service.list_project_members(
            project_id=project_id,
            current_user_id=current_user_id,
        )
    except ProjectAccessForbiddenError as exc:
        raise HTTPException(
            status_code=403, detail="Project members access forbidden"
        ) from exc

    if members is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return members


@router.post(
    "/projects/{project_id}/members",
    summary="Add project member",
    description=(
        "Add a member to a project by email. Only project owners can add members. "
        "This updates `is_group_project` immediately based on member count."
    ),
    response_model=ProjectMemberInfo,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Only the project owner can manage members"},
        404: {"description": "Project or target user not found"},
        409: {"description": "User is already a member of this project"},
        422: {"description": "Validation error"},
    },
)
async def add_project_member(
    project_id: UUID,
    payload: ProjectMemberCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberInfo:
    """Add a new member to a project owned by the authenticated user."""
    service = ProjectService(db)
    try:
        member = await service.add_project_member(
            project_id=project_id,
            current_user_id=current_user.id,
            payload=payload,
        )
    except ProjectAccessForbiddenError as exc:
        raise HTTPException(
            status_code=403, detail="Project member management forbidden"
        ) from exc
    except ProjectResourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProjectConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if member is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return member


@router.patch(
    "/projects/{project_id}/members/{user_id}",
    summary="Update project member role",
    description=(
        "Update a non-owner member role (`maintainer` or `contributor`). "
        "Only project owners can update member roles."
    ),
    response_model=ProjectMemberInfo,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Only the project owner can manage members"},
        404: {"description": "Project or membership not found"},
        409: {"description": "Requested role change violates owner protections"},
        422: {"description": "Validation error"},
    },
)
async def update_project_member(
    project_id: UUID,
    user_id: UUID,
    payload: ProjectMemberUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberInfo:
    """Update the role of a project member."""
    service = ProjectService(db)
    try:
        member = await service.update_project_member(
            project_id=project_id,
            target_user_id=user_id,
            current_user_id=current_user.id,
            payload=payload,
        )
    except ProjectAccessForbiddenError as exc:
        raise HTTPException(
            status_code=403, detail="Project member management forbidden"
        ) from exc
    except ProjectResourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProjectConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if member is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return member


@router.delete(
    "/projects/{project_id}/members/{user_id}",
    summary="Remove project member",
    description=(
        "Remove a non-owner member from a project. Only project owners can remove "
        "members. Owner membership removal is blocked."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Only the project owner can manage members"},
        404: {"description": "Project or membership not found"},
        409: {"description": "Requested removal violates owner protections"},
    },
)
async def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a member from a project."""
    service = ProjectService(db)
    try:
        removed = await service.remove_project_member(
            project_id=project_id,
            target_user_id=user_id,
            current_user_id=current_user.id,
        )
    except ProjectAccessForbiddenError as exc:
        raise HTTPException(
            status_code=403, detail="Project member management forbidden"
        ) from exc
    except ProjectResourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProjectConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if removed is None:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post(
    "/projects/{project_id}/leave",
    summary="Leave project",
    description=(
        "Leave project membership for the authenticated user. The last project "
        "owner cannot leave."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Project or membership not found"},
        409: {"description": "Last owner cannot leave"},
    },
)
async def leave_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove the authenticated user's membership from a project."""
    service = ProjectService(db)
    try:
        left = await service.leave_project(
            project_id=project_id,
            current_user_id=current_user.id,
        )
    except ProjectResourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProjectConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if left is None:
        raise HTTPException(status_code=404, detail="Project not found")


@router.patch(
    "/projects/{project_id}",
    summary="Update project",
    description=(
        "Partially update a project. Editing is owner-only and allowed for both draft "
        "and published projects. The final project state must include at least one "
        "of `demo_url`, `github_url`, or `video_url`. URL domains are not restricted "
        "beyond valid http(s) format."
    ),
    response_model=ProjectDetailResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Only the project owner can edit the project"},
        404: {"description": "Project not found"},
        422: {
            "description": (
                "Validation error (for example: empty payload, non-editable fields, "
                "invalid URL format, invalid timeline dates/order, or removing all "
                "project URLs)."
            )
        },
    },
)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectDetailResponse:
    """Update editable fields for a project owned by the authenticated user."""
    service = ProjectService(db)
    try:
        project = await service.update_project(
            project_id=project_id,
            current_user_id=current_user.id,
            payload=payload,
        )
    except ProjectAccessForbiddenError as exc:
        raise HTTPException(status_code=403, detail="Project edit forbidden") from exc
    except ProjectValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post(
    "/projects/{project_id}/publish",
    summary="Publish project",
    description=(
        "Publish a project owned by the authenticated user. This is idempotent: "
        "publishing an already published project returns the current project state."
    ),
    response_model=ProjectDetailResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Only the project owner can publish the project"},
        404: {"description": "Project not found"},
    },
)
async def publish_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectDetailResponse:
    """Publish a project and set `published_at` if it is currently a draft."""
    service = ProjectService(db)
    try:
        project = await service.publish_project(
            project_id=project_id,
            current_user_id=current_user.id,
        )
    except ProjectAccessForbiddenError as exc:
        raise HTTPException(
            status_code=403, detail="Project publish forbidden"
        ) from exc

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post(
    "/projects/{project_id}/unpublish",
    summary="Unpublish project",
    description=(
        "Unpublish a project owned by the authenticated user. This is idempotent: "
        "unpublishing an already draft project returns the current project state."
    ),
    response_model=ProjectDetailResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Only the project owner can unpublish the project"},
        404: {"description": "Project not found"},
    },
)
async def unpublish_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectDetailResponse:
    """Unpublish a project and clear `published_at` if it is currently published."""
    service = ProjectService(db)
    try:
        project = await service.unpublish_project(
            project_id=project_id,
            current_user_id=current_user.id,
        )
    except ProjectAccessForbiddenError as exc:
        raise HTTPException(
            status_code=403, detail="Project unpublish forbidden"
        ) from exc

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get(
    "/projects",
    summary="List projects",
    description=(
        "Return published project cards with cursor pagination, including computed "
        "`team_size` from active project memberships and taxonomy fields "
        "(`categories`, `tags`, `tech_stack`)."
    ),
    response_model=ProjectListResponse,
    responses={
        400: {"description": "Invalid cursor"},
        401: {"description": "Invalid or expired bearer token"},
    },
)
async def list_projects(
    limit: int = Query(
        default=20,
        description="Page size. Values are clamped to the service-supported range.",
    ),
    cursor: str | None = Query(
        default=None,
        description=(
            "Opaque pagination cursor returned by a previous response. "
            "Must be used with the same `sort` and (for `sort=top`) the same date range."
        ),
    ),
    sort: Literal["top", "new"] = Query(
        default="top",
        description=(
            "`top` ranks by votes within a published date window; `new` sorts by creation time."
        ),
    ),
    published_from: date | None = Query(
        default=None,
        description=(
            "Start of the `published_at` date window (inclusive) for `sort=top` in `YYYY-MM-DD` format. "
            "Ignored for `sort=new`. Defaults to 90 days before `published_to` (or today if omitted)."
        ),
    ),
    published_to: date | None = Query(
        default=None,
        description=(
            "End of the `published_at` date window (inclusive) for `sort=top` in `YYYY-MM-DD` format. "
            "Ignored for `sort=new`. Defaults to today (UTC date)."
        ),
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ProjectListResponse:
    """Return the published projects feed with project-card taxonomy parity.

    `sort=new` returns newest-first ordering.

    `sort=top` returns vote-ranked results within a published date window
    (`published_at`). The default window is the last 90 days, and callers may
    override it with `published_from` / `published_to` in `YYYY-MM-DD` format.

    Every project card includes computed `team_size` plus taxonomy fields
    (`categories`, `tags`, `tech_stack`) in stored assignment order.

    Reuse the same `sort` and date-range values when paginating with a cursor.
    """
    service = ProjectService(db)
    try:
        return await service.list_projects(
            sort=sort,
            limit=limit,
            cursor=cursor,
            published_from=published_from,
            published_to=published_to,
            current_user_id=current_user.id if current_user else None,
        )
    except CursorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/projects/{project_id}/vote",
    summary="Vote for a project",
    description=(
        "Add the authenticated user's vote for a published, non-deleted project. "
        "This endpoint is idempotent and returns `204` even if the vote already exists."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Project not found"},
        422: {"description": "Validation error"},
    },
)
async def add_project_vote(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Vote for a published, non-deleted project as the authenticated user."""
    service = VoteService(db)
    try:
        await service.add_vote(project_id=project_id, user_id=current_user.id)
    except VoteTargetNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.delete(
    "/projects/{project_id}/vote",
    summary="Remove project vote",
    description=(
        "Remove the authenticated user's vote for a published, non-deleted project. "
        "This endpoint is idempotent and returns `204` even if no vote exists."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Project not found"},
        422: {"description": "Validation error"},
    },
)
async def remove_project_vote(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a vote for a published, non-deleted project as the authenticated user."""
    service = VoteService(db)
    try:
        await service.remove_vote(project_id=project_id, user_id=current_user.id)
    except VoteTargetNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
