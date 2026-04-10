from datetime import date
from typing import Annotated, Literal
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

ProjectsPageLimit = Annotated[
    int,
    Query(
        ...,
        gt=0,
        le=100,
        description="Page size (1-100).",
    ),
]
ProjectsCursor = Annotated[
    str | None,
    Query(
        ...,
        description=(
            "Opaque pagination cursor from a previous response. "
            "Reuse with the same `sort` and date-range values."
        ),
    ),
]
ProjectsSort = Annotated[
    Literal["top", "new"],
    Query(
        ...,
        description="Sort order: `new` by creation time, `top` by vote rank in date window.",
    ),
]
MyProjectsVisibility = Annotated[
    Literal["all", "published", "draft"],
    Query(
        ...,
        description=(
            "Visibility scope for my associated projects (creator or member): `all` includes drafts and "
            "published projects, `published` includes only published projects, and "
            "`draft` includes only drafts."
        ),
    ),
]
ProjectsPublishedFrom = Annotated[
    date | None,
    Query(
        ...,
        description="Inclusive `published_at` start date (`YYYY-MM-DD`) for `sort=top`.",
    ),
]
ProjectsPublishedTo = Annotated[
    date | None,
    Query(
        ...,
        description="Inclusive `published_at` end date (`YYYY-MM-DD`) for `sort=top`.",
    ),
]


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
        "`full_name` may be omitted but cannot be `null` when provided. "
        "`username` is immutable and cannot be updated."
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
        "Return published, non-deleted projects voted by the authenticated user, ordered by most "
        "recent vote first, with cursor pagination, computed `team_size`, and taxonomy fields "
        "(`categories`, `tags`, `tech_stack`)."
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
    """Return voted project cards, including computed team size and taxonomy fields."""
    service = VoteService(db)
    try:
        return await service.list_my_voted_projects(
            user_id=current_user.id, limit=limit, cursor=cursor
        )
    except CursorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/users/me/projects",
    summary="List my projects",
    description=(
        "Return the authenticated user's associated (creator or member), non-deleted projects with cursor "
        "pagination, computed `team_size`, and taxonomy fields (`categories`, "
        "`tags`, `tech_stack`). Drafts are included by default. "
        "`sort=new` returns one newest-first stream across the selected visibility. "
        "`sort=top` reuses published date-window semantics for published results; "
        "when drafts are included, published results are returned first and drafts "
        "follow in newest-first order. `published_from` and `published_to` apply "
        "only to published results under `sort=top` and are ignored for draft-only listings."
    ),
    response_model=ProjectListResponse,
    responses={
        400: {"description": "Invalid cursor"},
        401: {"description": "Authentication required"},
    },
)
async def list_my_projects(
    limit: ProjectsPageLimit = 20,
    cursor: ProjectsCursor = None,
    visibility: MyProjectsVisibility = "all",
    sort: ProjectsSort = "new",
    published_from: ProjectsPublishedFrom = None,
    published_to: ProjectsPublishedTo = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectListResponse:
    """Return creator/member-associated project cards, including drafts, with taxonomy parity."""
    service = ProjectService(db)
    try:
        return await service.list_projects_for_owner(
            owner_id=current_user.id,
            sort=sort,
            visibility=visibility,
            limit=limit,
            cursor=cursor,
            published_from=published_from,
            published_to=published_to,
            current_user_id=current_user.id,
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
    "/users/by-username/{username}",
    summary="Get public user profile by username",
    description=(
        "Return public-safe profile fields for a specific username. "
        "Lookup is case-insensitive and resolves against canonical lowercase storage."
    ),
    response_model=UserPublic,
    responses={
        404: {"description": "User not found"},
    },
)
async def get_user_profile_by_username(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    """Return public-safe fields for a given username (case-insensitive lookup)."""
    service = UserService(db)
    user = await service.get_user_by_username(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic.model_validate(user)


async def _get_user_or_404_by_id(db: AsyncSession, *, user_id: UUID) -> User:
    """Resolve a user by id or raise 404 for missing users."""
    user = await UserService(db).get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def _get_user_or_404_by_username(db: AsyncSession, *, username: str) -> User:
    """Resolve a user by username (case-insensitive) or raise 404."""
    user = await UserService(db).get_user_by_username(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def _list_published_projects_for_creator(
    *,
    db: AsyncSession,
    associated_user_id: UUID,
    current_user_id: UUID | None,
    limit: int,
    cursor: str | None,
    sort: Literal["top", "new"],
    published_from: date | None,
    published_to: date | None,
) -> ProjectListResponse:
    """List published project cards for a user association with team/taxonomy parity."""
    project_service = ProjectService(db)
    try:
        return await project_service.list_projects(
            sort=sort,
            limit=limit,
            cursor=cursor,
            published_from=published_from,
            published_to=published_to,
            associated_user_id=associated_user_id,
            current_user_id=current_user_id,
        )
    except CursorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/users/{user_id}/projects",
    summary="List published projects for a user",
    description=(
        "Return published projects associated with the given user, with cursor pagination "
        "and computed `team_size`, plus taxonomy fields (`categories`, `tags`, "
        "`tech_stack`)."
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
    limit: ProjectsPageLimit = 20,
    cursor: ProjectsCursor = None,
    sort: ProjectsSort = "new",
    published_from: ProjectsPublishedFrom = None,
    published_to: ProjectsPublishedTo = None,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ProjectListResponse:
    """Return a user's published associated project cards with team/taxonomy parity."""
    user = await _get_user_or_404_by_id(db, user_id=user_id)
    return await _list_published_projects_for_creator(
        db=db,
        associated_user_id=user.id,
        current_user_id=current_user.id if current_user else None,
        limit=limit,
        cursor=cursor,
        sort=sort,
        published_from=published_from,
        published_to=published_to,
    )


@router.get(
    "/users/by-username/{username}/projects",
    summary="List published projects for a user by username",
    description=(
        "Return published projects associated with the given username, with cursor "
        "pagination and computed `team_size`, plus taxonomy fields (`categories`, "
        "`tags`, `tech_stack`). Username lookup is case-insensitive and resolves "
        "against canonical lowercase storage."
    ),
    response_model=ProjectListResponse,
    responses={
        400: {"description": "Invalid cursor"},
        401: {"description": "Invalid or expired bearer token"},
        404: {"description": "User not found"},
    },
)
async def list_user_projects_by_username(
    username: str,
    limit: ProjectsPageLimit = 20,
    cursor: ProjectsCursor = None,
    sort: ProjectsSort = "new",
    published_from: ProjectsPublishedFrom = None,
    published_to: ProjectsPublishedTo = None,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ProjectListResponse:
    """Return username-associated project cards with team/taxonomy parity."""
    user = await _get_user_or_404_by_username(db, username=username)
    return await _list_published_projects_for_creator(
        db=db,
        associated_user_id=user.id,
        current_user_id=current_user.id if current_user else None,
        limit=limit,
        cursor=cursor,
        sort=sort,
        published_from=published_from,
        published_to=published_to,
    )
