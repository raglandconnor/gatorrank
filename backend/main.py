import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from schemas import HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    logger.info(f"CORS allowed origins: {settings.cors_origins_list}")


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # From .env or fallback
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Root endpoint", description="Returns a simple greeting message")
def read_root():
    """
    Root endpoint that returns a greeting.

    Returns:
        dict: A dictionary containing a greeting message
    """
    return {"Hello": "World"}


@app.get(
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
    return HealthResponse(
        status="healthy",
        message="API is running",
        timestamp=datetime.now(),
    )
