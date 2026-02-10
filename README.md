# gatorrank

A website for ranking student-made projects at UF.

## Table of Contents

- [Tech Stack](#tech-stack)
- [Installation](#installation)
  - [Backend](#backend)
  - [Frontend](#frontend)
  - [Pre-commit Hooks](#pre-commit-hooks)
- [Contributing](#contributing)
  - [Workflow](#workflow)
  - [CI](#ci)
  - [Branching Strategy](#branching-strategy)

## Tech Stack

Backend:

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- Supabase
- uv

Frontend:

- TypeScript
- Next.js 16
- Tailwind CSS
- Chakra UI
- Bun

## Installation

### Backend

1. Sync dependencies with [uv](https://docs.astral.sh/uv/getting-started/installation/):

   ```bash
   cd backend
   uv sync
   ```

2. Select the Python interpreter in VS Code:
   - Press `Cmd+Shift+P` or `Ctrl+Shift+P`
   - Type "Python: Select Interpreter"
   - Choose `./backend/.venv/bin/python3`

3. Run the FastAPI server:

   ```bash
   uv run uvicorn main:app --reload
   ```

   The backend server will be available at `http://localhost:8000`

   API documentation (Swagger UI) is available at `http://localhost:8000/docs`

### Frontend

1. Install dependencies with [bun](https://bun.sh):

   ```bash
   cd frontend
   bun install
   ```

2. Run the Next.js development server:

   ```bash
   bun dev
   ```

   The frontend will be available at `http://localhost:3000`

### Pre-commit Hooks

Pre-commit runs a small set of automated checks before commits. In this repo it:
- trims trailing whitespace and ensures files end with a newline
- runs `ruff` + `ruff format` for backend Python files
- runs `prettier` for frontend TypeScript/JavaScript/CSS/JSON/YAML/Markdown files

Install the pre-commit runner once:

```bash
uv tool install pre-commit
```

Then enable the hooks for this repo:

```bash
# in the project root
pre-commit install
pre-commit run --all-files
```

> **Note:**
> If a pre-commit hook auto-fixes files during `git commit`, pre-commit will stop the commit so you can review the changes.
> Re-stage the modified files (e.g., `git add <files>`) and run `git commit` again.

## Contributing

### Workflow

1. Create a feature branch from `main`
2. Make your changes
3. Open a pull request to `main`
4. Get review approval before merging

### CI

GitHub Actions automatically runs `pre-commit run --all-files` on every pull request and whenever commits are pushed to or merged into `main`.

### Branching Strategy

- `main` - Production-ready code
- `feature/*` - New features and changes
- `fix/*` - Bug fixes
- `refactor/*` - Code refactoring
- `hotfix/*` - Urgent production fixes
- `docs/*` - Documentation updates
- `test/*` - Test additions or updates
- `style/*` - Code style changes
