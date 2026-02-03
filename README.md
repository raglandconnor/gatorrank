# gatorrank

A website for ranking student-made projects at UF.

## Table of Contents

- [Installation](#installation)
- [Contributing](#contributing)
  - [Branching Strategy](#branching-strategy)
  - [Workflow](#workflow)

## Installation

### Backend

1. Sync dependencies with [uv](https://docs.astral.sh/uv/getting-started/installation/):

   ```bash
   cd backend
   uv sync
   ```

2. Run the FastAPI server:

   ```bash
   uv run uvicorn main:app --reload
   ```

   The backend server will be available at `http://localhost:8000`

   API documentation (Swagger UI) is available at `http://localhost:8000/docs`

## Contributing

### Branching Strategy

- `main` - Production-ready code
- `feature/*` - New features and changes
- `fix/*` - Bug fixes
- `refactor/*` - Code refactoring
- `hotfix/*` - Urgent production fixes
- `docs/*` - Documentation updates
- `test/*` - Test additions or updates
- `style/*` - Code style changes

### Workflow

1. Create a feature branch from `main`
2. Make your changes
3. Open a pull request to `main`
4. Get review approval before merging
