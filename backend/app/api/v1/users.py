from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.project import ProjectListResponse
from app.schemas.user import UserPrivate, UserPublic, UserUpdate
from app.services.project import CursorError, ProjectService
from app.services.user import UserService

router = APIRouter()


@router.get(
    "/users/me",
    summary="Get current user profile",
    response_model=UserPrivate,
    responses={
        401: {"description": "Authentication required"},
    },
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserPrivate:
    """Return the authenticated user's private profile."""
    return current_user  # pyright: ignore[reportReturnType]


@router.patch(
    "/users/me",
    summary="Update current user profile",
    response_model=UserPrivate,
    responses={
        401: {"description": "Authentication required"},
        422: {"description": "Validation error (e.g., empty full_name)"},
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
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user  # pyright: ignore[reportReturnType]


@router.get(
    "/users/{user_id}",
    summary="Get public user profile",
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
    return user  # pyright: ignore[reportReturnType]


@router.get(
    "/users/{user_id}/projects",
    summary="List published projects for a user",
    response_model=ProjectListResponse,
    responses={
        404: {"description": "User not found"},
    },
)
async def list_user_projects(
    user_id: UUID,
    limit: int = Query(default=20, gt=0, le=100),
    cursor: str | None = Query(default=None),
    sort: Literal["top", "new"] = Query(default="new"),
    published_from: date | None = Query(default=None),
    published_to: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
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
        )
    except CursorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
