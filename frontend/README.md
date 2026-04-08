## Frontend Testing

This frontend uses Bun-based test commands with two layers:

- Unit/component tests: Vitest + Testing Library
- End-to-end tests: Playwright (headless by default)

### Run Tests

From the `frontend` directory:

```bash
bun run test:unit
```

Run Playwright E2E tests (headless):

```bash
bun run test:e2e
```

Run Playwright in headed mode for debugging:

```bash
bun run test:e2e:headed
```

Run the full frontend test suite:

```bash
bun run test
```

### Test File Layout

- `tests/unit/**/*.test.ts` for utility and pure logic tests
- `tests/components/**/*.test.tsx` for React component tests
- `tests/e2e/**/*.spec.ts` for browser E2E tests
- `tests/setup.ts` for Vitest setup and Next.js test mocks
- `tests/utils/render.tsx` for shared test render helpers

### Config Files

- `vitest.config.ts` for unit/component test config
- `playwright.config.ts` for E2E config and local web server setup
