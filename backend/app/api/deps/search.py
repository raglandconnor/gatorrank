from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_db
from app.services.search import PostgresSearchService, SearchService


def get_search_service(
    db: AsyncSession = Depends(get_db),
) -> SearchService:
    """Return the configured project search service implementation."""
    return PostgresSearchService(db)
