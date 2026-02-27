# GatorRank Phase 1 API Plan (Users, Projects, Project Members, Votes)

## Scope

Phase 1 covers these 4 tables:

- `users`
- `projects`
- `project_members`
- `votes`

Out of scope for this plan (for now):

- Full Supabase JWKS auth integration
- Supabase RLS

Phase 1 auth approach:

- Simple backend JWT auth dependency (HS256 secret-based) suitable for a small project

---

## Current Progress Snapshot (as of now)

- [x] Auth dependencies implemented (`required` + `optional`)
- [x] Auth request-state contract implemented (`current_user_id`, `current_user_email`)
- [x] User upsert-on-auth helper implemented
- [x] `GET /projects/{project_id}` implemented and tested
- [x] `GET /projects` implemented with cursor pagination and sort (`new`, baseline `top`) and tested
- [x] Auth tests and project read-path tests/integration tests in place

Known follow-up alignment items after latest clarifications:

- [ ] `GET /projects/{project_id}` should return `403` (not `404`) for existing draft projects when requester is authenticated but not a member
- [ ] `GET /projects?sort=top` should become time-windowed (current implementation is effectively all-time by `vote_count`)

---

## Clarified Product/Policy Decisions (agreed)

- Draft project visibility: any project member (`owner`, `maintainer`, `contributor`) can view
- Project editing: owner-only
- Draft project access for non-members: return `403` (exists but not accessible)
- Published projects are public
- `PATCH /projects/{id}` is allowed while published
- `DELETE /projects/{id}` is owner-only and should be a soft delete
- `unpublish` should clear `published_at`
- Project member role management is owner-only
- Single-owner model for now
- Owner cannot leave if they are the last owner
- Votes allowed only on published projects
- Project owners may vote on their own projects
- Vote count must be updated transactionally
- `GET /users/{user_id}/projects` returns only published projects
- Feed should stay minimal for now (no extra filters yet)
- Cursor format can change during Phase 1
- Error payload format can remain `{ "detail": "..." }` and iterate later
- PRs can group related endpoints (instead of strict one-ticket-per-PR)

Still intentionally undecided (defer):

- Create-project required fields and publish validation gates
- Public-safe fields for `GET /users/{user_id}`
- Exact response shape for `GET /users/me/votes`

---

## Proposed Routes (with status)

### Projects

- [ ] `POST /projects` - create project (draft by default; frontend can publish via explicit publish endpoint)
- [x] `GET /projects` - list projects (published feed; pagination + cursor + sort implemented; `top` needs time-window follow-up)
- [x] `GET /projects/{project_id}` - project detail (implemented; draft visibility works for members; non-member draft `403` follow-up)
- [ ] `PATCH /projects/{project_id}` - update project (owner-only)
- [ ] `DELETE /projects/{project_id}` - soft delete project (owner-only)
- [ ] `POST /projects/{project_id}/publish` - publish project
- [ ] `POST /projects/{project_id}/unpublish` - unpublish project (clear `published_at`)

### Project Members

- [ ] `GET /projects/{project_id}/members` - list collaborators
- [ ] `POST /projects/{project_id}/members` - add collaborator (owner-only; lookup by username/email)
- [ ] `PATCH /projects/{project_id}/members/{user_id}` - update collaborator role (owner-only)
- [ ] `DELETE /projects/{project_id}/members/{user_id}` - remove collaborator (owner-only)
- [ ] `POST /projects/{project_id}/leave` - current user leaves project (blocked for last owner)

### Votes

- [ ] `POST /projects/{project_id}/vote` - add current user vote (published projects only)
- [ ] `DELETE /projects/{project_id}/vote` - remove current user vote (published projects only)
- [ ] `GET /projects/{project_id}/votes/count` - optional if count not embedded in project response
- [ ] `GET /users/me/votes` - list projects current user voted for (response shape TBD)

### Users

- [ ] `GET /users/me` - current user profile
- [ ] `PATCH /users/me` - update own profile (`full_name` required/non-empty; `profile_picture_url` nullable)
- [ ] `GET /users/{user_id}` - public profile (field set TBD)
- [ ] `GET /users/{user_id}/projects` - published projects for a user

---

## Full Implementation Order (Dependency-Aware)

1. [ ] `POST /projects`
2. [x] `GET /projects/{project_id}` (implemented; one policy follow-up remains for non-member draft response code)
3. [ ] `PATCH /projects/{project_id}`
4. [ ] `POST /projects/{project_id}/publish`
5. [ ] `POST /projects/{project_id}/unpublish`
6. [x] `GET /projects` (implemented; `top` sort time-window behavior follow-up remains)
7. [ ] `DELETE /projects/{project_id}` (soft delete)

8. [ ] `GET /projects/{project_id}/members`
9. [ ] `POST /projects/{project_id}/members`
10. [ ] `PATCH /projects/{project_id}/members/{user_id}`
11. [ ] `DELETE /projects/{project_id}/members/{user_id}`
12. [ ] `POST /projects/{project_id}/leave`

13. [ ] `POST /projects/{project_id}/vote`
14. [ ] `DELETE /projects/{project_id}/vote`

15. [ ] `GET /users/me`
16. [ ] `PATCH /users/me`
17. [ ] `GET /users/{user_id}`
18. [ ] `GET /users/{user_id}/projects`
19. [ ] `GET /users/me/votes`
20. [ ] `GET /projects/{project_id}/votes/count` (optional)

---

## Core Rules (Phase 1)

- Auth policy for routes is one of:
  - `public`
  - `get user (required)`
  - `get user (optional)`
- Auth required for all write routes
- Public reads allowed for published projects and public user profile endpoints
- Draft project detail is visible to all project members (`owner | maintainer | contributor`)
- Project edit/delete/publish/unpublish authority is owner-only
- Enforce unique vote: `(user_id, project_id)`
- Enforce unique project member pair: `(project_id, user_id)`
- Publish sets `is_published=true` and `published_at`
- Unpublish sets `is_published=false` and clears `published_at`
- Feed supports cursor pagination and sort (`new`, `top`)
- `top` should be time-windowed (window definition TBD)
- Votes only on published projects
- Soft delete for projects (implementation details/columns TBD)

---

# Backend Split Plan (2 Engineers)

## Ownership

- Engineer A (you): Projects API
- Engineer B (teammate): Users API + Auth

## Shared Contract (do first / maintain)

- [x] Auth context in backend request state: `current_user_id`, `current_user_email`
- [x] Error format: `{ "detail": "..." }`
- [x] Pagination shape: `limit`, `cursor`, `next_cursor` (for projects feed)
- [x] Role names for project members: `owner | maintainer | contributor`

---

## Tickets: Engineer B (Users + Auth)

### B1. Simple JWT auth verification dependency (HS256)

- [x] Build dependency for bearer token validation (project-scoped simple JWT auth)
- [x] Expose `current_user_id` and `current_user_email` to routes via request state
- Acceptance:
  - [x] Valid JWT reaches protected route
  - [x] Invalid/missing JWT returns `401`

### B2. User upsert-on-auth helper

- [x] On first authenticated request, ensure user exists in `users`
- [x] Create with defaults if missing
- Acceptance:
  - [x] New authed user gets inserted once
  - [x] Existing user is not duplicated

### B3. `GET /users/me`

- [ ] Return authenticated user profile
- Acceptance:
  - [ ] Returns current user row
  - [ ] `401` when unauthenticated

### B4. `PATCH /users/me`

- [ ] Allow updating `full_name`, `profile_picture_url`
- Notes:
  - `full_name` required and must be non-empty
  - `profile_picture_url` may be nullable
- Acceptance:
  - [ ] Only own profile is updated
  - [ ] Validation + `401` handling

### B5. `GET /users/{user_id}`

- [ ] Public user profile endpoint
- Acceptance:
  - [ ] Returns public-safe fields only (field set TBD)
  - [ ] `404` if user missing

### B6. `GET /users/{user_id}/projects`

- [ ] Return published projects for a user
- Acceptance:
  - [ ] Filters to published projects
  - [ ] Pagination works

### B7. Auth test scaffolding

- [x] Shared test fixture(s) for authenticated requests
- Acceptance:
  - [x] Project routes can reuse fixture immediately

---

## Tickets: Engineer A (Projects API)

### A1. `POST /projects`

- [ ] Create project endpoint (draft by default)
- [ ] Add creator as `project_members.owner`
- Notes:
  - Keep explicit publish flow (`POST /projects/{id}/publish`)
  - Frontend can support "Create Draft" vs "Publish" by chaining publish after create
  - Required create fields TBD
- Acceptance:
  - [ ] Project created
  - [ ] Owner membership created
  - [ ] Requires auth

### A2. `GET /projects/{project_id}`

- [x] Project detail read path implemented
- [ ] Align non-member draft access response to `403` (current behavior returns hidden/not found style)
- Acceptance (updated):
  - [x] Published projects visible publicly
  - [x] Drafts visible to owner/maintainer/contributor
  - [ ] Existing draft requested by non-member returns `403`

### A3. `PATCH /projects/{project_id}`

- [ ] Update editable fields
- Notes:
  - Owner-only edits (maintainers/contributors are view-only)
  - Editing allowed while published
- Acceptance:
  - [ ] Only owner can edit
  - [ ] `403` for unauthorized users

### A4. `POST /projects/{project_id}/publish`

- [ ] Set `is_published=true`, set `published_at`
- Notes:
  - Publish validation gates TBD
  - Best-judgment recommendation: make endpoint idempotent (`200`/no-op if already published)
- Acceptance:
  - [ ] Owner-only
  - [ ] Idempotent behavior documented/tested

### A5. `POST /projects/{project_id}/unpublish`

- [ ] Set `is_published=false`, clear `published_at`
- Notes:
  - Best-judgment recommendation: idempotent behavior
- Acceptance:
  - [ ] Owner-only
  - [ ] Visibility updates accordingly

### A6. `GET /projects`

- [x] Published feed endpoint implemented
- [x] Cursor pagination implemented
- [x] `new` sort implemented
- [ ] `top` sort should be time-windowed (current baseline is all-time `vote_count`)
- Acceptance (updated):
  - [x] Only published by default
  - [x] Stable pagination
  - [ ] Time-windowed `top` behavior defined and implemented

### A7. `DELETE /projects/{project_id}`

- [ ] Owner-only soft delete
- Acceptance:
  - [ ] Soft-deletes project (and applies consistent visibility behavior)
  - [ ] `403` for non-owner

### A8. Project members endpoints

- [ ] `GET /projects/{id}/members`
- [ ] `POST /projects/{id}/members`
- [ ] `PATCH /projects/{id}/members/{user_id}`
- [ ] `DELETE /projects/{id}/members/{user_id}`
- [ ] `POST /projects/{id}/leave`
- Notes:
  - Owner-only role/member management
  - Single owner only (for now)
  - Add-member lookup by username/email (request shape TBD)
  - Duplicate membership should return a suitable conflict error (recommend `409`)
  - Last owner cannot leave
- Acceptance:
  - [ ] Unique membership enforced
  - [ ] Owner protection rules enforced

### A9. Votes endpoints

- [ ] `POST /projects/{id}/vote`
- [ ] `DELETE /projects/{id}/vote`
- Notes:
  - Published projects only
  - Owner may vote on own project
  - Vote count updates transactionally
  - Best-judgment recommendation: idempotent vote/unvote endpoints
- Acceptance:
  - [ ] Unique vote enforced
  - [ ] Vote count behavior consistent and transactional

### A10. Optional vote reads

- [ ] `GET /projects/{id}/votes/count`
- Acceptance:
  - [ ] Accurate count and tested

---

## Dependency / Parallelization Plan (updated)

### Completed foundation (parallel work already done)

- [x] B1, B2, B7
- [x] A2 read path (implemented)
- [x] A6 read feed (implemented baseline)
- [x] DB/service layer setup for project read paths

### Immediate next parallel block (maximize concurrency)

- Engineer A (Projects):
  - [ ] A1 (`POST /projects`)
  - [ ] A3 (`PATCH /projects/{id}` owner-only)
  - [ ] A4 + A5 (`publish` / `unpublish`) as a grouped PR
  - [ ] A2 follow-up (`403` for non-member draft access)
- Engineer B (Users):
  - [ ] B3 (`GET /users/me`)
  - [ ] B4 (`PATCH /users/me`)
  - [ ] B5 (`GET /users/{user_id}`)

### Next parallel block

- Engineer A (Projects):
  - [ ] A8 (members endpoints)
  - [ ] A9 (vote endpoints)
  - [ ] A7 (soft delete)
  - [ ] A6 follow-up (time-windowed `top`)
- Engineer B (Users):
  - [ ] B6 (`GET /users/{user_id}/projects`)
  - [ ] `GET /users/me/votes` (with agreed response shape)

### Finalization / integration

- [ ] A10 (`GET /projects/{id}/votes/count`) if still needed
- [ ] Cross-endpoint integration tests for users/projects/votes/member flows
- [ ] Cleanup/refactor shared permission helpers if duplication appears

---

## PR Strategy (updated)

- Group related endpoints when it reduces overhead and preserves reviewability
- Suggested merge order:
  1. A1 + A3 + A4/A5 (projects write/lifecycle core)
  2. B3 + B4 + B5 (users core)
  3. A8 (members)
  4. A9 + `GET /users/me/votes`
  5. B6 + A6 top-window follow-up + A2 `403` follow-up
  6. A7 soft delete + optional A10
