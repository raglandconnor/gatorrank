from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.policy.roles import PolicyDeniedError, require_taxonomy_management
from app.schemas.taxonomy import TaxonomyTermCreateRequest, TaxonomyTermResponse
from app.services.taxonomy import TaxonomyConflictError, TaxonomyService

router = APIRouter(prefix="/taxonomy")


def _require_taxonomy_admin(user: User) -> None:
    try:
        require_taxonomy_management(user)
    except PolicyDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Taxonomy management forbidden",
        ) from exc


@router.get(
    "/categories",
    summary="List taxonomy categories",
    description=(
        "Return the full taxonomy categories list for authenticated users. "
        "Clients are responsible for filtering/sorting for typeahead UX."
    ),
    response_model=list[TaxonomyTermResponse],
    responses={401: {"description": "Authentication required"}},
)
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaxonomyTermResponse]:
    """Return all category terms in deterministic alphabetical order."""
    _ = current_user
    service = TaxonomyService(db)
    return await service.list_categories()


@router.post(
    "/categories",
    summary="Create taxonomy category",
    description=(
        "Create a category term explicitly. This endpoint is admin-only. "
        "Authenticated non-admin term creation is handled via project assignment "
        "flows in BE3-005."
    ),
    response_model=TaxonomyTermResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin role required"},
        409: {"description": "Taxonomy term already exists"},
        422: {"description": "Validation error"},
    },
)
async def create_category(
    payload: TaxonomyTermCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaxonomyTermResponse:
    """Create a category term with normalized uniqueness enforcement."""
    _require_taxonomy_admin(current_user)
    service = TaxonomyService(db)
    try:
        return await service.create_category(payload)
    except TaxonomyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "/tags",
    summary="List taxonomy tags",
    description=(
        "Return the full taxonomy tags list for authenticated users. "
        "Clients are responsible for filtering/sorting for typeahead UX."
    ),
    response_model=list[TaxonomyTermResponse],
    responses={401: {"description": "Authentication required"}},
)
async def list_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaxonomyTermResponse]:
    """Return all tag terms in deterministic alphabetical order."""
    _ = current_user
    service = TaxonomyService(db)
    return await service.list_tags()


@router.post(
    "/tags",
    summary="Create taxonomy tag",
    description=(
        "Create a tag term explicitly. This endpoint is admin-only. "
        "Authenticated non-admin term creation is handled via project assignment "
        "flows in BE3-005."
    ),
    response_model=TaxonomyTermResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin role required"},
        409: {"description": "Taxonomy term already exists"},
        422: {"description": "Validation error"},
    },
)
async def create_tag(
    payload: TaxonomyTermCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaxonomyTermResponse:
    """Create a tag term with normalized uniqueness enforcement."""
    _require_taxonomy_admin(current_user)
    service = TaxonomyService(db)
    try:
        return await service.create_tag(payload)
    except TaxonomyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "/tech-stacks",
    summary="List taxonomy tech stacks",
    description=(
        "Return the full taxonomy tech stack list for authenticated users. "
        "Clients are responsible for filtering/sorting for typeahead UX."
    ),
    response_model=list[TaxonomyTermResponse],
    responses={401: {"description": "Authentication required"}},
)
async def list_tech_stacks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaxonomyTermResponse]:
    """Return all tech stack terms in deterministic alphabetical order."""
    _ = current_user
    service = TaxonomyService(db)
    return await service.list_tech_stacks()


@router.post(
    "/tech-stacks",
    summary="Create taxonomy tech stack",
    description=(
        "Create a tech stack term explicitly. This endpoint is admin-only. "
        "Authenticated non-admin term creation is handled via project assignment "
        "flows in BE3-005."
    ),
    response_model=TaxonomyTermResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin role required"},
        409: {"description": "Taxonomy term already exists"},
        422: {"description": "Validation error"},
    },
)
async def create_tech_stack(
    payload: TaxonomyTermCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaxonomyTermResponse:
    """Create a tech stack term with normalized uniqueness enforcement."""
    _require_taxonomy_admin(current_user)
    service = TaxonomyService(db)
    try:
        return await service.create_tech_stack(payload)
    except TaxonomyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
