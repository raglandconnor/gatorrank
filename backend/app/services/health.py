from datetime import datetime

from app.schemas.health import HealthResponse


def get_health_response() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        message="API is running",
        timestamp=datetime.now(),
    )
