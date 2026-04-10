# Backend

## Mock Data Seeding (Dev)

Use the scripts below to seed frontend-realistic mock data directly in the database and to clean it up safely.

### Seed via Python DB flow

Command:

```bash
cd backend
PYTHONPATH=. uv run python app/scripts/seed_mock_data.py
```

What it does by default:
- Creates or logs in `24` mock users (`mock_user_###@ufl.edu`).
- Applies deterministic role distribution (`admin`/`faculty`/`student`).
- Creates `36` projects (first `30` published, remaining `6` drafts).
- Adds collaborators to `12` projects with varied team size.
- Seeds taxonomy vocabularies and deterministic project taxonomy assignments.
- Applies edge-case state shaping (including soft-deleted mock projects and varied published date windows).
- Applies a weighted vote distribution targeting `140` votes over published projects.
- Uses deterministic generation (seeded randomness) so output is stable between runs.
- Uses richer content (varied names/titles and lorem-style descriptions) for better frontend visualization.

Rerun behavior:
- Idempotent: existing mock users/projects are updated in place by deterministic keys.
- Memberships and votes are re-applied consistently for mock-scoped entities.
- Optional `--reset-mock` will delete existing mock-scoped rows first, then reseed.

Optional overrides:

```bash
cd backend
PYTHONPATH=. uv run python app/scripts/seed_mock_data.py \
  --total-users 24 \
  --total-projects 36 \
  --published-projects 30 \
  --group-projects 12 \
  --total-votes 140 \
  --email-domain ufl.edu \
  --mock-password 'mock-password-12345' \
  --random-seed 42 \
  --with-taxonomy \
  --with-edge-cases \
  --no-with-auth-sessions \
  --reset-mock
```

Flags:
- `--with-taxonomy` / `--no-with-taxonomy`: include taxonomy term vocab + project term assignments.
- `--with-edge-cases` / `--no-with-edge-cases`: include soft-delete and lifecycle/date-window edge-case shaping.
- `--with-auth-sessions` / `--no-with-auth-sessions`: include deterministic refresh-session fixtures (active/revoked/expired).
- `--reset-mock` is required when using `--no-with-taxonomy` or `--no-with-edge-cases` to avoid stale prior mock state.

### Cleanup mock data (dev-only)

Command:

```bash
cd backend
PYTHONPATH=. uv run python app/scripts/cleanup_mock_data.py --yes
```

Safety rules:
- Deletes only mock-scoped data (mock user emails and projects owned by those users, plus legacy `[MOCK]` titles).
- Includes taxonomy join cleanup for mock-scoped projects before deleting projects.
- Refuses to run against non-local DB hosts unless `--allow-non-local` is provided.
- Prints table-level delete counts.

Example for remote dev DB:

```bash
cd backend
PYTHONPATH=. uv run python app/scripts/cleanup_mock_data.py --yes --allow-non-local
```

### Recommended dev workflow

1. Apply migrations:

```bash
cd backend && uv run alembic upgrade head
```

2. Seed mock data:

```bash
cd backend && PYTHONPATH=. uv run python app/scripts/seed_mock_data.py
```

3. If you need a clean reseed, cleanup then seed:

```bash
cd backend && PYTHONPATH=. uv run python app/scripts/cleanup_mock_data.py --yes
cd backend && PYTHONPATH=. uv run python app/scripts/seed_mock_data.py
```
