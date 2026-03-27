# GatorRank Backend Checkpoint Report
**Date:** 2026-03-26
**Engineer:** Codex
**Feature Branch:** `feature/soft-delete`

This checkpoint summarizes the backend soft delete implementation for projects. The goal of this change was to keep deleted project data in the database while making deleted projects disappear from normal API reads and public application flows.

---

## 1. Scope Completed
The following soft delete work was completed:
- Added `deleted_at` to the `projects` table and SQLModel model.
- Added owner-only `DELETE /projects/{project_id}` soft delete behavior.
- Made delete idempotent for the owner.
- Updated project read paths so soft-deleted projects are hidden from:
  - `GET /projects`
  - `GET /projects/{project_id}`
  - `GET /users/{user_id}/projects`
- Added unit, API, and integration coverage for soft delete semantics.

---

## 2. Schema and Service Changes
### Database / Model
- Added nullable `deleted_at TIMESTAMP WITH TIME ZONE` to `projects`.
- Generated Alembic migration: `43d6b84cf473_add_project_soft_delete.py`.
- Migration preserves existing rows and supports downgrade by dropping the column.

### Service Behavior
- `ProjectService.get_project_by_id()` now excludes deleted rows by default and can explicitly include them for owner delete idempotency.
- `ProjectService.soft_delete_project()`:
  - returns `False` for missing projects
  - raises `ProjectAccessForbiddenError` for non-owner deletes on active projects
  - sets `deleted_at` once for the owner
  - returns success on repeated owner deletes without removing the row
- `ProjectService.can_view_project()` now rejects deleted projects for all callers.
- Project listing queries now filter out rows with `deleted_at` set.

### API Behavior
- Added `DELETE /projects/{project_id}` returning:
  - `204` on successful owner delete
  - `204` on repeated owner delete
  - `403` for non-owner delete attempts on active projects
  - `404` for missing projects
- Existing detail and listing routes now naturally hide deleted projects through the service layer.

---

## 3. Test Coverage Added
The following new coverage was added:
- Unit coverage for deleted-project visibility checks.
- API route tests for delete success, forbidden, and missing-project behavior.
- Service integration tests for:
  - marking `deleted_at`
  - owner idempotency
  - non-owner rejection
  - hidden detail/list behavior after delete
- API integration tests for:
  - owner delete returning `204`
  - hidden detail/feed/user-project listings after delete
  - repeated owner delete returning `204`
  - non-owner `403`
  - missing-project `404`

---

## 4. Validation Performed
Validation completed on this branch:
- Full backend pytest suite: `130 passed`
- Ruff: `All checks passed`
- Alembic migration autogeneration completed against a temporary Postgres database.
- Alembic `upgrade head` completed successfully with the new migration included.
- Targeted DB-backed integration soft delete tests passed after migration verification.

---

## 5. Compatibility Notes
- Soft delete is additive to the existing schema and does not remove existing fields or alter project IDs.
- The implementation preserves previous draft/public visibility behavior for non-deleted projects.
- `backend/app/core/config.py` was updated to ignore extra `.env` keys. This was necessary because the checked-in backend `.env` includes keys outside the strict `Settings` model, which caused integration-test Alembic bootstrap failures before the application code could run.
- Unrelated worktree changes present before this feature were intentionally left untouched.

---

## 6. Recommended PR Review Focus
Reviewers should focus on:
- owner-only delete semantics
- repeated delete idempotency
- hidden read behavior after delete
- migration correctness and deploy safety
- whether the config `extra="ignore"` change matches team expectations for environment handling
