## Epic E: Comments + Likes (Extensible Design)

### BE3-010: Add Comments Data Model (Soft Delete + Moderation Markers)

**Priority:** P0  
**Status:** Not Started  
**Completed On:** _TBD_  
**Completion Notes:** _TBD_

**Tasks**

- add `comments` table with core fields:
  - `id`, `project_id`, `author_id` (nullable only if future anon posting needed; keep non-null for now)
  - `body`
  - `created_at`, `updated_at`
  - `deleted_at` (soft delete)
  - `moderation_state`/flag fields for hidden-by-moderator placeholder behavior
- include forward-compatible fields to ease future threads/reactions (without exposing now)
- add migration + indexes

**Acceptance Criteria**

- schema supports flat comments with soft-delete and moderator-hide semantics
- design does not block future threaded comment extension
- migrations apply cleanly
- ticket-specific tests are added and pass

**Suggested Split (Isolated Assignment)**

#### BE3-010A: Comments Table + Migration (No API)

**Priority:** P0  
**Status:** Not Started  
**Completed On:** _TBD_  
**Completion Notes:** _TBD_

**Scope**

- add `Comment` model + `comments` table only (no routes/services)
- include fields: `id`, `project_id`, `author_id` (non-null), `body`, `created_at`, `updated_at`, `deleted_at`, moderation marker state/flag
- add migration + indexes (at least `project_id`, plus `project_id + created_at`)
- add focused model/integration tests for create/read, soft-delete marker persistence, and moderation-state persistence

**Out of Scope**

- comment routes/endpoints
- likes model/service
- sorting/pagination behavior
- policy enforcement beyond schema/constraint layer

**Acceptance Criteria**

- model + migration apply cleanly with `uv run alembic upgrade head`
- tests for the new model behavior pass
- no API contract changes introduced

---

### BE3-011: Comment Likes Model + Service

**Priority:** P0  
**Depends on:** BE3-010  
**Status:** Not Started  
**Completed On:** _TBD_  
**Completion Notes:** _TBD_

**Tasks**

- add `comment_likes` table with unique `(comment_id, user_id)`
- implement toggle-like behavior:
  - `POST /comments/{id}/like` (idempotent like)
  - `DELETE /comments/{id}/like` (idempotent unlike)
- expose like count + viewer-liked state in comment payload (viewer-liked false for anonymous)
- add service-level concurrency/race handling tests

**Acceptance Criteria**

- each user can like a comment once
- like/unlike is idempotent under retries
- payload includes consistent like count and viewer state
- ticket-specific tests are added and pass

---

### BE3-012: Comment Routes + Sorting (Non-Paginated v1)

**Priority:** P0  
**Depends on:** BE3-010, BE3-011  
**Status:** Not Started  
**Completed On:** _TBD_  
**Completion Notes:** _TBD_

**Tasks**

- implement comments endpoints:
  - list comments for project (public)
  - create comment (authenticated)
  - delete own comment (authenticated author)
  - admin hide/delete moderation endpoints
- support list sorting:
  - default: most liked
  - optional: `oldest`, `newest`
- return a non-paginated list in v1 (pagination deferred)
- enforce a server-side maximum comments returned per request (hard cap) to bound payload size
- return placeholder metadata for moderated/deleted comments
- include OpenAPI summaries/descriptions and permission notes

**Acceptance Criteria**

- anonymous users can read comments
- authenticated users can create/delete own comments
- admin can moderate any comment
- default + optional sorting behaves as specified
- list endpoint is intentionally non-paginated in v1 and documents this behavior
- hard cap is enforced consistently on comment list responses
- ticket-specific tests are added and pass