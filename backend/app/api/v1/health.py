import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.health import HealthResponse
from app.services.health import get_health_response, get_db_health_response
from app.db.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/health",
    summary="Health check",
    description="Check if the API is running and healthy",
    response_model=HealthResponse,
)
def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Service status, message, and timestamp
    """
    return get_health_response()


@router.get(
    "/db-health",
    summary="DB Health check",
    description="Check if the database connection is healthy",
    response_model=HealthResponse,
)
async def db_health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Database health check endpoint.

    Returns:
        HealthResponse: Service status, message, and timestamp
    """
    try:
        return await get_db_health_response(db)
    except Exception:
        logger.exception("Database health check failed")
        raise HTTPException(status_code=503, detail="Database unavailable")
