from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import get_current_user, get_current_user_optional
from app.db.database import get_db
from app.models.user import User
from app.schemas.project import ProjectListResponse
from app.schemas.user import UserPrivate, UserPublic, UserUpdate
from app.services.project import CursorError, ProjectService
from app.services.user import UserService
from app.services.vote import VoteService

router = APIRouter()


@router.get(
    "/users/me",
    summary="Get current user profile",
    description="Return the authenticated user's private profile fields.",
    response_model=UserPrivate,
    responses={
        401: {"description": "Authentication required"},
    },
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserPrivate:
    """Return the authenticated user's private profile."""
    return UserPrivate.model_validate(current_user)


@router.patch(
    "/users/me",
    summary="Update current user profile",
    description=(
        "Partially update the authenticated user's profile. "
        "At least one field must be provided. "
        "`full_name` may be omitted but cannot be `null` when provided."
    ),
    response_model=UserPrivate,
    responses={
        401: {"description": "Authentication required"},
        422: {
            "description": "Validation error (e.g., empty payload or invalid fields)"
        },
        500: {"description": "Authenticated user invariant violation"},
    },
)
async def update_current_user_profile(
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserPrivate:
    """Update profile mapping (full_name, profile_picture_url) for the current user."""
    service = UserService(db)
    updated_user = await service.update_user(current_user.id, payload)
    if updated_user is None:
        raise HTTPException(
            status_code=500, detail="Authenticated user record not found"
        )
    return UserPrivate.model_validate(updated_user)


@router.get(
    "/users/me/votes",
    summary="List my voted projects",
    description=(
        "Return published projects voted by the authenticated user, ordered by most "
        "recent vote first, with cursor pagination."
    ),
    response_model=ProjectListResponse,
    responses={
        400: {"description": "Invalid cursor"},
        401: {"description": "Authentication required"},
    },
)
async def list_my_voted_projects(
    limit: int = Query(
        default=20,
        gt=0,
        le=100,
        description="Page size (1-100).",
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque pagination cursor from a previous response.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectListResponse:
    """Return published projects voted by the authenticated user."""
    service = VoteService(db)
    try:
        return await service.list_my_voted_projects(
            user_id=current_user.id, limit=limit, cursor=cursor
        )
    except CursorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/users/{user_id}",
    summary="Get public user profile",
    description="Return public-safe profile fields for a specific user.",
    response_model=UserPublic,
    responses={
        404: {"description": "User not found"},
    },
)
async def get_user_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    """Return public-safe fields for a given user."""
    service = UserService(db)
    user = await service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic.model_validate(user)


@router.get(
    "/users/{user_id}/projects",
    summary="List published projects for a user",
    description=(
        "Return published projects authored by the given user, with cursor pagination."
    ),
    response_model=ProjectListResponse,
    responses={
        400: {"description": "Invalid cursor"},
        401: {"description": "Invalid or expired bearer token"},
        404: {"description": "User not found"},
    },
)
async def list_user_projects(
    user_id: UUID,
    limit: int = Query(
        default=20,
        gt=0,
        le=100,
        description="Page size (1-100).",
    ),
    cursor: str | None = Query(
        default=None,
        description=(
            "Opaque pagination cursor from a previous response. "
            "Reuse with the same `sort` and date-range values."
        ),
    ),
    sort: Literal["top", "new"] = Query(
        default="new",
        description="Sort order: `new` by creation time, `top` by vote rank in date window.",
    ),
    published_from: date | None = Query(
        default=None,
        description="Inclusive `published_at` start date (`YYYY-MM-DD`) for `sort=top`.",
    ),
    published_to: date | None = Query(
        default=None,
        description="Inclusive `published_at` end date (`YYYY-MM-DD`) for `sort=top`.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ProjectListResponse:
    """Return published projects authored by the specific user."""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    project_service = ProjectService(db)
    try:
        return await project_service.list_projects(
            sort=sort,
            limit=limit,
            cursor=cursor,
            published_from=published_from,
            published_to=published_to,
            created_by_id=user_id,
            current_user_id=current_user.id if current_user else None,
        )
    except CursorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
