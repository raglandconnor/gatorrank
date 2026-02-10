from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health import get_health_response

router = APIRouter()


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
