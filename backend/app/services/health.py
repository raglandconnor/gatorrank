from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.health import HealthResponse


def get_health_response() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        message="API is running",
        timestamp=datetime.now(),
    )


async def get_db_health_response(db: AsyncSession) -> HealthResponse:
    res = await db.execute(text("SELECT now()"))
    db_now = res.scalar_one()
    return HealthResponse(
        status="connected", message="Database connection successful", timestamp=db_now
    )
