import logging
from typing import Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

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
    "/items/{item_id}",
    summary="Get item by ID",
    description="Retrieve an item by its ID with an optional query parameter",
    response_description="Item details including ID and optional query parameter",
)
def read_item(item_id: int, q: Union[str, None] = None):
    """
    Get an item by its ID.

    Args:
        item_id: The unique identifier of the item
        q: Optional query string parameter

    Returns:
        dict: A dictionary containing the item_id and optional query parameter q
    """
    return {"item_id": item_id, "q": q}
