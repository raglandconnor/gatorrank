from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import get_current_user, get_current_user_optional
from app.db.database import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectListResponse,
)
from app.services.project import (
    CursorError,
    ProjectAccessForbiddenError,
    ProjectService,
)

router = APIRouter()


@router.post(
    "/projects",
    summary="Create project draft",
    response_model=ProjectDetailResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        422: {
            "description": (
                "Validation error (for example: missing/blank title or description, "
                "invalid URL format, or no demo/github/video URL provided)."
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

    This endpoint always creates a draft (`is_published=false`). Publishing is a
    separate step handled by `POST /projects/{project_id}/publish`.
    """
    service = ProjectService(db)
    return await service.create_project(created_by_id=current_user.id, payload=payload)


@router.get(
    "/projects/{project_id}",
    summary="Get project detail",
    description="Return project details if visible to the current requester",
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
    service = ProjectService(db)
    current_user_id = current_user.id if current_user else None
    try:
        project = await service.get_project_detail(project_id, current_user_id)
    except ProjectAccessForbiddenError as exc:
        raise HTTPException(status_code=403, detail="Project access forbidden") from exc
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get(
    "/projects",
    summary="List projects",
    response_model=ProjectListResponse,
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
) -> ProjectListResponse:
    """Return the published projects feed with cursor pagination.

    `sort=new` returns newest-first ordering.

    `sort=top` returns vote-ranked results within a published date window
    (`published_at`). The default window is the last 90 days, and callers may
    override it with `published_from` / `published_to` in `YYYY-MM-DD` format.

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
        )
    except CursorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
