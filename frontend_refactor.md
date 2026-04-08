# Frontend Refactor Plan

## Goal
Increase long-term maintainability and code quality in the frontend by reducing duplication, lowering component complexity, and standardizing data-access patterns.

## 1) Split Large Page/Component Files Into Feature Modules (Highest ROI)
- Refactor the largest files into smaller feature-oriented units:
  - `app/profile/[userId]/edit/page.tsx`
  - `components/projects/ProjectForm.tsx`
  - `app/projects/[projectId]/page.tsx`
  - `app/profile/[userId]/page.tsx`
- Target structure:
  - `features/<feature>/sections/*` for page-level UI chunks
  - `features/<feature>/hooks/*` for state/data logic
  - `features/<feature>/types.ts` for local contracts
- Keep route files thin: composition + routing only.

## 2) Introduce a Single Typed API Request Layer
- Consolidate request/response/error handling into one shared helper (e.g. `lib/api/request.ts`):
  - JSON parsing and fallback errors
  - Typed `HttpError` propagation
  - Auth/no-auth request modes
- Migrate duplicated parsing logic from:
  - `lib/api/auth.ts`
  - `lib/api/projects.ts`
  - `lib/api/users.ts`
- Keep transport utilities side-effect-light; avoid hard navigation redirects from low-level API helpers.

## 3) Extract Repeated Utilities and Local Storage Adapters
- Centralize duplicated utilities:
  - `getInitials(...)`
  - profile extended-data `load/save` localStorage logic
- Suggested modules:
  - `lib/format/user.ts`
  - `lib/profile/extendedProfileStorage.ts`
- Add small unit tests for utility behavior and storage serialization edge cases.

## 4) Build Reusable Card Primitives
- Reduce duplication across card variants:
  - `components/ProjectCard.tsx`
  - `components/projects/ProjectGridCard.tsx`
  - `components/ProfileProjectCard.tsx`
- Extract shared primitives:
  - Card shell (hover/background/spacing)
  - Vote/engagement controls
  - Tag row rendering
- Keep variant-specific layout differences only at the leaf component level.

## 5) Replace Remaining Mock/Staging Paths With Real Feature Paths
- Remove temporary development logic that can calcify:
  - `console.log` submit path in `app/projects/create/page.tsx`
  - `mockProject` dependency in `app/projects/edit/page.tsx`
- Wire both flows to real API-backed hooks/services.
- Add loading/error/success states that match production behavior.

## 6) Strengthen Frontend Guardrails (Lint + Test Coverage)
- Add coverage thresholds in `vitest.config.ts` (global + critical-path floors).
- Expand lint rules to discourage complexity/duplication drift (targeted, not noisy).
- Require tests for extracted hooks/utilities and key page states before merge.

## Suggested Execution Order
1. API request layer (Item 2)
2. Shared utilities/storage extraction (Item 3)
3. Large file decomposition into sections/hooks (Item 1)
4. Card primitive unification (Item 4)
5. Replace mock paths (Item 5)
6. Tighten quality gates (Item 6)

## Success Criteria
- Largest frontend files are split into focused modules with clear ownership.
- No duplicated API parsing/error logic across domain clients.
- Shared utilities exist for repeated formatting/storage concerns.
- Card implementations reuse common primitives.
- Mock-only page behavior removed from create/edit project flows.
- Coverage thresholds and lint checks actively prevent regression.
