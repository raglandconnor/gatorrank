# Frontend MVP Task Split (Dependency-Aware)

## Goal

Ship the remaining MVP frontend scope by splitting work into low-coupling feature tracks, while tracking backend/API dependencies explicitly so neither frontend engineer is blocked unexpectedly.

## Current State (from codebase)

- Home page still uses mocks in [frontend/app/page.tsx](frontend/app/page.tsx) (`topOverallProjects`, `trending*` from `mock-projects`).
- Profile page already fetches public user and user projects via [frontend/lib/api/users.ts](frontend/lib/api/users.ts), rendered in [frontend/components/ProfileUserProjects.tsx](frontend/components/ProfileUserProjects.tsx).
- Project detail/edit are still mock-driven in [frontend/data/mock-project.ts](frontend/data/mock-project.ts), [frontend/app/projects/[projectId]/page.tsx](frontend/app/projects/[projectId]/page.tsx), and [frontend/app/projects/edit/page.tsx](frontend/app/projects/edit/page.tsx).
- Create project currently does not persist; it redirects to profile in [frontend/app/projects/create/page.tsx](frontend/app/projects/create/page.tsx).

## Workstreams (split by feature)

### Workstream A — Auth + Profile PR to main (highest priority)

**Owner:** You

- Final PR hardening:
  - Re-run frontend checks (`bun run lint`, `bunx tsc --noEmit`), verify no regressions in auth/profile routes.
  - Validate profile loading states/errors and avatar lifecycle changes.
- Resolve/monitor merge drift with `main` until green.
- Merge once CI + review pass.

**Definition of done**

- PR merged to `main`.
- No auth/profile regressions in login/signup/profile edit flows.

### Workstream B — Projects Data Integration + New Top Projects Page

**Owner:** Teammate (already active on top projects page)

- Replace home-page mock sections with backend-driven data in [frontend/app/page.tsx](frontend/app/page.tsx).
- Add/finish “See Top Overall UF Projects” page (reuse same `get projects` endpoint and shared mapping layer).
- Extract/centralize project DTO -> UI card mapping used by both Home and Top Projects page to avoid duplicate transform logic.

**Definition of done**

- Home + top-projects page read from API, no hardcoded mock lists.
- Shared mapper/util used in both places.

### Workstream C — Profile Projects + Create/Edit enablement

**Primary Owner:** You after Workstream A merge

- Keep/extend profile projects fetching in [frontend/components/ProfileUserProjects.tsx](frontend/components/ProfileUserProjects.tsx):
  - Confirm shape compatibility with backend project list payload.
  - Add loading/empty/error handling parity with home/top page.
- Wire create project to API in [frontend/app/projects/create/page.tsx](frontend/app/projects/create/page.tsx):
  - Submit actual payload.
  - Route to new project detail (or owner profile) based on response.
- Wire edit project to API in [frontend/app/projects/edit/page.tsx](frontend/app/projects/edit/page.tsx):
  - Load existing project by id.
  - Submit update payload.
  - Remove dependence on `mockProject.id`.
- Align project detail page [frontend/app/projects/[projectId]/page.tsx](frontend/app/projects/[projectId]/page.tsx) to backend `GET /projects/{id}`.

**Definition of done**

- Create/edit are fully persisted.
- Profile projects list reflects DB/API state.
- Project detail reflects real project data.

## Backend Dependency Tickets (explicit blockers)

- `GET /projects` supports sorting/filter mode(s) needed by Home and Top Projects page (overall, trending current month, trending last month).
- `GET /users/{id}/projects` contract confirmed for profile list fields used by card UI.
- `POST /projects` returns created project id for redirect.
- `GET /projects/{id}` returns full detail payload used by detail/edit initial load.
- `PATCH /projects/{id}` (or `PUT`) available with validation error shape documented.
- Ownership/authorization semantics for edit endpoints documented (403 vs 404 behavior).

## Parallelization Plan (minimize blocking)

- Sequence:
  1. Merge auth/profile PR first.
  2. In parallel: teammate builds top-projects page + home API integration, while you wire create/edit/detail APIs.
  3. Integrate shared project mapping utility near end.
- Keep contracts stable via one shared `projects` API client + typed interfaces in `frontend/lib/api/types`.
- Use feature flags or guarded fallbacks only if endpoint readiness lags.

## Suggested Ticket Breakdown (ready to paste into tracker)

- FE-A1: Finalize and merge auth/profile PR.
- FE-B1: Home page fetches projects from API (replace mocks).
- FE-B2: Top overall UF projects page using shared endpoint.
- FE-B3: Shared project DTO-to-card mapper utility.
- FE-C1: Profile projects list contract alignment + UX states.
- FE-C2: Create project API integration + success routing.
- FE-C3: Edit project API integration + remove mock dependency.
- FE-C4: Project detail page API integration by project id.
- FE-QA1: End-to-end smoke pass across auth/profile/projects routes.

## Acceptance Checklist

- No mock project data referenced by live routes (except intentional fallback during transition).
- Home, profile projects, top projects, create, edit, and detail all hit real API clients.
- Lint + typecheck pass.
- Manual QA paths documented for both frontend engineers.
