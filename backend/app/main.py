import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(f"CORS allowed origins: {settings.cors_origins_list}")
    yield


app = FastAPI(lifespan=lifespan)


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


app.include_router(health_router, prefix="/api/v1", tags=["health"])
