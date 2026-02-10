from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Health check message")
    timestamp: datetime = Field(..., description="Timestamp of the health check")
