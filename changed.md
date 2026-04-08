# BE3-005A Change Log

## Scope

This feature completes project taxonomy payload parity across project card/detail endpoints.

Updated endpoints and payload paths:

- `GET /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `GET /api/v1/projects/slug/{slug}`
- `GET /api/v1/users/{user_id}/projects`
- `GET /api/v1/users/by-username/{username}/projects`
- `GET /api/v1/users/me/votes`

## Implementation Changes

### Taxonomy hydration parity

- Reused project taxonomy hydration in `VoteService` so `GET /users/me/votes` now returns:
  - `categories`
  - `tags`
  - `tech_stack`
- Reused the same project-card mapping path as the main project listing service to keep team size, vote state, and taxonomy shaping consistent.
- Preserved taxonomy assignment ordering by relying on stored join-table `position` ordering when building payloads.

### Service surface updates

- Added a public wrapper on `ProjectService` to fetch taxonomy payloads by project id list.
- Added a public wrapper for converting a `Project` into a `ProjectListItemResponse` with full parity fields.
- Added service docstrings clarifying that list/detail payloads include taxonomy fields in stored assignment order.

### Route and OpenAPI documentation updates

- Updated route descriptions/docstrings for affected project and user endpoints to explicitly document taxonomy parity.
- Documented that list/detail project payloads include `categories`, `tags`, and `tech_stack` alongside computed `team_size`.

## Test Coverage Added/Updated

### Integration coverage

- Expanded project API integration coverage to assert taxonomy presence and ordering for:
  - project detail by id
  - project detail by slug
  - project feed
  - user projects by id
  - user projects by username
  - voted projects
- Added vote service integration coverage confirming voted-project payloads include taxonomy fields in stored assignment order.

## Files Changed

- `backend/app/api/v1/projects.py`
- `backend/app/api/v1/users.py`
- `backend/app/services/project.py`
- `backend/app/services/vote.py`
- `backend/app/tests/integration/test_projects_api_integration.py`
- `backend/app/tests/integration/test_vote_service_integration.py`

## Verification Performed

Executed successfully in WSL:

- `cd /home/mauri/gatorrank && pre-commit run --all-files`
- `cd /home/mauri/gatorrank/backend && uv run pytest`

Backend test result:

- `225 passed, 214 skipped`

## Notes

- Backend local env was updated only in ignored `backend/.env` for local verification.
- Verified with `git status` and ignore rules that no sensitive env file was staged or tracked.
