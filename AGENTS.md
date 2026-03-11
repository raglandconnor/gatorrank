# AGENTS.md

## Stack

- Frontend: Bun, Next.js (App Router), TypeScript, Chakra UI.
- Backend: Python 3.12+, `uv`, FastAPI, SQLModel, Alembic, Supabase Postgres, pytest.

## Key Paths

- `frontend/app`, `frontend/components`, `frontend/lib/theme.ts`
- `backend/app/api/v1`, `backend/app/services`, `backend/app/models`, `backend/app/schemas`
- `backend/alembic/versions`
- `backend/app/tests` and `backend/app/tests/integration`

## Run Commands

- Frontend checks: `cd frontend && bun run lint && bunx tsc --noEmit`
- Backend tests: `cd backend && uv run pytest`

## Dependency Management

- For backend Python dependencies, prefer `uv add <dependency>` (or `uv add --dev <dependency>` for dev packages).
- Do not manually edit `backend/pyproject.toml` to add or change dependencies unless the user explicitly asks for a manual edit.
- When dependency changes are made, commit the corresponding lockfile updates produced by `uv`.

## Migrations

- After SQLModel schema changes, create and commit an Alembic migration.
- `cd backend && uv run alembic revision --autogenerate -m "describe change"`
- `cd backend && uv run alembic upgrade head`

Note: Never edit a previously generated migration file. Only make edits to the actual SQLModel code, then generate and apply the migration.

## Env Vars

- Backend (`backend/.env`): `DATABASE_URL`, `DATABASE_JWT_SECRET`
- Frontend (`frontend/.env`): `NEXT_PUBLIC_API_BASE_URL`

## Guardrails

- Keep FastAPI routes thin; put business logic in `backend/app/services`.
- Keep models, schemas, services, routes, and migrations in sync.
- Do not hardcode secrets.
- Before starting implementation, ask questions to make sure you have a full understanding of what you are implementing. Ask clarifying questions to ensure functionality aligns with what the user wants.
- If details are ambiguous but non-blocking, state assumptions explicitly and ask the user to clarify.
- Run `pre-commit run --all-files` before finalizing.
- Run local tests, then after passing run full test suite before finalizing.
- For every FastAPI endpoint and schema change, write/update clear docstrings plus summary/description metadata so Swagger/OpenAPI (/docs) stays accurate and complete.
