# Frontend API Layer Implementation Plan

## Goal
Build a scalable, side-effect-light API request layer for the frontend that matches current backend contracts and reduces duplication across domain clients.

## Backend Contract Assumptions (Current)
- Error envelope is FastAPI default: `{"detail": string | ValidationIssue[]}`.
- Auth failures return `401` with meaningful detail strings (for example: `Not authenticated`, `Invalid token`, `Token expired`).
- Success payloads are JSON for most endpoints.
- Some endpoints are `204 No Content` and must not be JSON-parsed.

## Design Principles
- Keep transport code pure: no navigation or toast side effects in low-level request helpers.
- Normalize all failures into a single typed `HttpError` shape.
- Centralize auth attach + refresh/retry logic.
- Keep domain files (`auth.ts`, `users.ts`, `projects.ts`, `search.ts`) thin and declarative.
- Preserve backend error messages where possible.

## Stage 0: Baseline and Design Lock
### Scope
- Document request-layer API contract before coding.
- Confirm migration order and 401 UX policy.

### Deliverables
- Finalized `request.ts` function signatures.
- Finalized `HttpError` shape and fields.
- Decision on redirect ownership (transport vs UI/auth layer).

### Exit Criteria
- Team-aligned contract for:
  - `requestJson<T>()`
  - `requestVoid()`
  - auth modes (`none`, `required`, `optional`)

### Stage 0 Contract (Locked)
- `requestJson<T>(path, options?): Promise<T>`
- `requestVoid(path, options?): Promise<void>`
- `RequestOptions` includes:
  - `method?: string`
  - `headers?: HeadersInit`
  - `body?: BodyInit | object | null`
  - `query?: Record<string, string | number | boolean | undefined>`
  - `auth?: 'none' | 'required' | 'optional'` (default `none`)
  - `signal?: AbortSignal`
  - `cache?: RequestCache`
  - `fallbackErrorMessage?: string | ((res: Response) => string)`
- Body handling:
  - If `body` is a plain object, JSON-stringify and set `Content-Type: application/json` when absent.
  - If `body` is already `BodyInit` (`string`, `FormData`, etc.), pass through unchanged.
- Auth behavior:
  - `none`: anonymous fetch only.
  - `required`: refresh-aware authenticated fetch path.
  - `optional`: use authenticated path only when an access token exists; otherwise anonymous fetch.
- Error behavior:
  - Non-OK responses throw `HttpError` with `status` and parsed backend detail message.
  - Keep backend detail precedence; use `fallbackErrorMessage` (static or status-aware) only when detail/statusText is unavailable.

## Stage 1: Build Shared Request Core
### Scope
- Create `frontend/lib/api/request.ts`.
- Reuse existing `client.ts`, `http.ts`, and `fetchWithAuth.ts` where appropriate.

### Implementation
- Add request helpers:
  - `requestJson<T>(path, options)`
  - `requestVoid(path, options)`
- Add shared request options:
  - method, headers, body, query params, `AbortSignal`, auth mode.
- Centralize:
  - URL construction
  - request execution (`fetch` vs `fetchWithAuth`)
  - non-OK handling via `parseApiErrorMessage` + `buildHttpError`
  - 204-safe behavior for void responses

### Exit Criteria
- New core compiles with no consumer migrations yet.
- Request helpers handle:
  - JSON success
  - `204` success
  - non-OK errors with typed `status`.

## Stage 2: Migrate `auth.ts`
### Scope
- Refactor `frontend/lib/api/auth.ts` to use `request.ts`.

### Implementation
- Replace direct `fetch` calls and local `parseErrorMessage` duplication.
- Keep endpoint behavior unchanged (`signup`, `login`, `me`, `refresh`, `logout`).

### Exit Criteria
- No auth behavior regression.
- Auth error messages remain backend-derived.
- `auth.ts` has no bespoke response/error parsing.

## Stage 3: Migrate `users.ts`, `projects.ts`, `search.ts`
### Scope
- Refactor remaining domain clients to use `request.ts`.

### Implementation
- Replace duplicated `parseXResponse` wrappers.
- Route all JSON + void endpoints through shared helpers.
- Preserve per-endpoint fallback messaging only where product-specific.

### Exit Criteria
- Domain clients contain endpoint contracts only.
- Duplicated error parsing logic removed from all four clients.

## Stage 4: Move 401 Navigation Side Effects Out of Transport
### Scope
- Remove direct redirect logic from `fetchWithAuth.ts`.
- Keep auth refresh/retry and session-state behavior explicit.

### Implementation
- Stop calling `window.location.href` in transport.
- Propagate terminal `401` as typed errors.
- Handle redirect/logout UX in higher-level auth/UI layers (for example `AuthProvider`).

### Exit Criteria
- No low-level API helper performs route navigation.
- Protected-route UX still behaves correctly when session expires.

## Stage 5: Test Coverage and Hardening
### Scope
- Add/update focused tests for request-layer behavior.

### Test Targets
- Error parsing:
  - `detail` string
  - `detail` validation array (`msg` extraction)
- Status propagation (`HttpError.status`).
- `requestVoid` correctness for `204`.
- Refresh single-flight behavior under parallel 401s.
- Terminal auth failure propagation after refresh failure.

### Exit Criteria
- All updated tests pass.
- Lint/type checks pass.

## Stage 6: Final Cleanup and Documentation
### Scope
- Remove obsolete helper code and document conventions.

### Implementation
- Delete dead parsing helpers left in domain files.
- Add brief doc/comments in `request.ts` describing usage patterns and side-effect policy.

### Exit Criteria
- API layer has one clear request path.
- Conventions are discoverable for future features.

## Validation Gates Per Stage
- Frontend type/lint checks:
  - `cd frontend && bun run lint && bunx tsc --noEmit`
- Targeted tests after each stage (if available).
- Full frontend test suite before final merge (if present in repo scripts).

## Rollout Order Summary
1. Stage 0
2. Stage 1
3. Stage 2
4. Stage 3
5. Stage 4
6. Stage 5
7. Stage 6

## Risks and Mitigations
- Risk: subtle auth UX changes during redirect decoupling.
  - Mitigation: isolate Stage 4 and verify protected-page behavior manually.
- Risk: accidental payload parsing on 204 endpoints.
  - Mitigation: enforce `requestVoid()` for all known no-content routes.
- Risk: mixed old/new request paths during migration.
  - Mitigation: migrate by domain file and remove old helpers immediately after each migration.
