import os
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest
from docker.errors import DockerException
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

from app.tests.integration._db_url_utils import to_sync_migration_url

BACKEND_ROOT = Path(__file__).resolve().parents[3]
PRE_SLUG_REVISION = "377b094d6028"


def test_alembic_roundtrip_latest_revision() -> None:
    try:
        container = PostgresContainer("postgres:16-alpine")
        container.start()
    except DockerException as exc:
        pytest.skip(f"Docker daemon unavailable for migration round-trip test: {exc}")

    try:
        sync_url = to_sync_migration_url(container.get_connection_url())
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
            ["uv", "run", "alembic", "downgrade", "base"],
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


def test_slug_backfill_is_deterministic_for_collisions() -> None:
    try:
        container = PostgresContainer("postgres:16-alpine")
        container.start()
    except DockerException as exc:
        pytest.skip(f"Docker daemon unavailable for migration round-trip test: {exc}")

    try:
        sync_url = to_sync_migration_url(container.get_connection_url())
        env = os.environ.copy()
        env["DATABASE_URL"] = sync_url
        env["DATABASE_SSL"] = "false"
        env["DATABASE_SSL_VERIFY"] = "false"

        subprocess.run(
            ["uv", "run", "alembic", "upgrade", PRE_SLUG_REVISION],
            cwd=BACKEND_ROOT,
            env=env,
            check=True,
        )

        engine = create_engine(sync_url)
        creator_id = str(uuid4())
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO users (id, email, password_hash, role, created_at, updated_at)
                        VALUES (:id, :email, :password_hash, :role, NOW(), NOW())
                        """
                    ),
                    {
                        "id": creator_id,
                        "email": "migration-slug-backfill@ufl.edu",
                        "password_hash": "test-password-hash",
                        "role": "student",
                    },
                )

                # Insert out-of-order to ensure backfill is driven by created_at + id sorting.
                conn.execute(
                    text(
                        """
                        INSERT INTO projects (
                            id, created_by_id, title, short_description, vote_count,
                            is_group_project, is_published, published_at, created_at, updated_at
                        )
                        VALUES
                            ('00000000-0000-0000-0000-000000000002', :creator_id, 'Cafe', 'B', 0, FALSE, FALSE, NULL, '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00'),
                            ('00000000-0000-0000-0000-000000000001', :creator_id, 'Café', 'A', 0, FALSE, FALSE, NULL, '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00'),
                            ('00000000-0000-0000-0000-000000000003', :creator_id, 'cafe!!!', 'C', 0, FALSE, FALSE, NULL, '2026-01-02T00:00:00+00:00', '2026-01-02T00:00:00+00:00')
                        """
                    ),
                    {"creator_id": creator_id},
                )

            subprocess.run(
                ["uv", "run", "alembic", "upgrade", "head"],
                cwd=BACKEND_ROOT,
                env=env,
                check=True,
            )

            with engine.begin() as conn:
                rows = conn.execute(
                    text(
                        """
                        SELECT id::text, slug
                        FROM projects
                        ORDER BY id ASC
                        """
                    )
                ).fetchall()

            assert rows == [
                ("00000000-0000-0000-0000-000000000001", "cafe"),
                ("00000000-0000-0000-0000-000000000002", "cafe-2"),
                ("00000000-0000-0000-0000-000000000003", "cafe-3"),
            ]
        finally:
            engine.dispose()
    finally:
        container.stop()
