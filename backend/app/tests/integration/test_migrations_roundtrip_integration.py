import os
import subprocess
from pathlib import Path

import pytest
from docker.errors import DockerException
from testcontainers.postgres import PostgresContainer

BACKEND_ROOT = Path(__file__).resolve().parents[3]


def _to_sync_migration_url(sync_url: str) -> str:
    if sync_url.startswith("postgresql+psycopg2://"):
        return sync_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    return sync_url


def test_alembic_roundtrip_latest_revision() -> None:
    try:
        container = PostgresContainer("postgres:16-alpine")
        container.start()
    except DockerException as exc:
        pytest.skip(f"Docker daemon unavailable for migration round-trip test: {exc}")

    try:
        sync_url = _to_sync_migration_url(container.get_connection_url())
        env = os.environ.copy()
        env["DATABASE_URL"] = sync_url
        env["DATABASE_SSL"] = "false"
        env["DATABASE_SSL_VERIFY"] = "false"

        subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            cwd=BACKEND_ROOT,
            env=env,
            check=True,
        )
        subprocess.run(
            ["uv", "run", "alembic", "downgrade", "-1"],
            cwd=BACKEND_ROOT,
            env=env,
            check=True,
        )
        subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            cwd=BACKEND_ROOT,
            env=env,
            check=True,
        )
    finally:
        container.stop()
