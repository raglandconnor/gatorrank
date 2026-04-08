from datetime import date
from typing import Literal

from fastapi import Depends, Query
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_db
from app.schemas.search import ProjectSearchRequest
from app.services.search import PostgresSearchService, SearchService


def get_search_service(
    db: AsyncSession = Depends(get_db),
) -> SearchService:
    """Return the configured project search service implementation."""
    return PostgresSearchService(db)


def get_project_search_request(
    q: str | None = Query(
        default=None,
        description=(
            "Optional keyword query matched against project `title` and "
            "`short_description`."
        ),
    ),
    categories: list[str] = Query(
        default_factory=list,
        description="Optional category filters. Repeated query params are supported.",
    ),
    tags: list[str] = Query(
        default_factory=list,
        description="Optional tag filters. Repeated query params are supported.",
    ),
    tech_stack: list[str] = Query(
        default_factory=list,
        description="Optional tech-stack filters. Repeated query params are supported.",
    ),
    categories_legacy: list[str] = Query(
        default_factory=list,
        alias="categories[]",
        include_in_schema=False,
    ),
    tags_legacy: list[str] = Query(
        default_factory=list,
        alias="tags[]",
        include_in_schema=False,
    ),
    tech_stack_legacy: list[str] = Query(
        default_factory=list,
        alias="tech_stack[]",
        include_in_schema=False,
    ),
    limit: int = Query(
        default=20,
        description="Page size. Values are clamped to the service-supported range.",
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque pagination cursor returned by a previous search response.",
    ),
    sort: Literal["top", "new"] = Query(
        default="top",
        description="Sort mode (`top` or `new`). Defaults to `top`.",
    ),
    published_from: date | None = Query(
        default=None,
        description=(
            "Start of the `published_at` date window (inclusive) for `sort=top` in "
            "`YYYY-MM-DD` format. Ignored for `sort=new`."
        ),
    ),
    published_to: date | None = Query(
        default=None,
        description=(
            "End of the `published_at` date window (inclusive) for `sort=top` in "
            "`YYYY-MM-DD` format. Ignored for `sort=new`."
        ),
    ),
) -> ProjectSearchRequest:
    """Build and validate the search query contract for project search requests."""
    try:
        return ProjectSearchRequest(
            q=q,
            categories=[*categories, *categories_legacy],
            tags=[*tags, *tags_legacy],
            tech_stack=[*tech_stack, *tech_stack_legacy],
            limit=limit,
            cursor=cursor,
            sort=sort,
            published_from=published_from,
            published_to=published_to,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc
