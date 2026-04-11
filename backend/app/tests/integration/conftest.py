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

from app.tests.integration._db_url_utils import (
    to_async_database_url,
    to_sync_migration_url,
)

BACKEND_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    try:
        container = PostgresContainer("postgres:16-alpine")
        container.start()
    except DockerException as exc:
        yield None
        return
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def database_urls(postgres_container: PostgresContainer | None) -> dict[str, str]:
    if postgres_container:
        sync_url = postgres_container.get_connection_url()
    else:
        sync_url = os.environ.get("DATABASE_URL")
        if not sync_url:
            pytest.skip("No Docker daemon and no DATABASE_URL provided")
        sync_url = sync_url.replace("postgresql+asyncpg://", "postgresql://")
    
    return {
        "sync": to_sync_migration_url(sync_url),
        "async": to_async_database_url(sync_url),
    }


@pytest.fixture(scope="session", autouse=True)
def migrated_database(database_urls: dict[str, str]) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_urls["sync"]
    # Only force SSL off for a local testcontainer; for remote Supabase keep env SSL settings
    if "localhost" in database_urls["sync"] or "127.0.0.1" in database_urls["sync"]:
        env["DATABASE_SSL"] = "false"
        env["DATABASE_SSL_VERIFY"] = "false"

    subprocess.run(
        ["/home/mauri/.local/bin/uv", "run", "alembic", "upgrade", "head"],
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
    """Per-test database session that issues real commits.

    We do NOT attempt transaction rollback here because Supabase's FK constraint
    checks see only the committed state of the database, so any savepoint-based
    isolation scheme causes FK violations when a service inserts a child row that
    references a parent row flushed but not yet "really" committed.

    Instead, every test is written to:
     - use uuid4-derived unique emails / slugs so rows from different test runs
       never collide on unique constraints;
     - scope list-result assertions to the IDs the test itself seeded, rather
       than asserting exact global list contents.
    """
    async with AsyncSession(async_engine, expire_on_commit=False) as session:
        yield session


