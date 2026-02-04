# gatorrank

A website for ranking student-made projects at UF.

## Table of Contents

- [Installation](#installation)
  - [Backend](#backend)
  - [Frontend](#frontend)
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
