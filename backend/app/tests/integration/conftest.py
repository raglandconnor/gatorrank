import os
import subprocess
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from docker.errors import DockerException
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel.ext.asyncio.session import AsyncSession
from testcontainers.postgres import PostgresContainer


BACKEND_ROOT = Path(__file__).resolve().parents[3]


def _to_async_database_url(sync_url: str) -> str:
    if sync_url.startswith("postgresql+psycopg2://"):
        return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if sync_url.startswith("postgresql+psycopg://"):
        return sync_url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
    if sync_url.startswith("postgresql://"):
        return sync_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return sync_url


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    try:
        container = PostgresContainer("postgres:16-alpine")
        container.start()
    except DockerException as exc:
        pytest.skip(f"Docker daemon unavailable for integration tests: {exc}")
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def database_urls(postgres_container: PostgresContainer) -> dict[str, str]:
    sync_url = postgres_container.get_connection_url()
    return {"sync": sync_url, "async": _to_async_database_url(sync_url)}


@pytest.fixture(scope="session", autouse=True)
def migrated_database(database_urls: dict[str, str]) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_urls["sync"]
    env["DATABASE_SSL"] = "false"
    env["DATABASE_SSL_VERIFY"] = "false"

    subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env=env,
        check=True,
    )


@pytest_asyncio.fixture(scope="session")
async def async_engine(
    database_urls: dict[str, str],
) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(
        database_urls["async"],
        poolclass=NullPool,
    )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with async_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()
