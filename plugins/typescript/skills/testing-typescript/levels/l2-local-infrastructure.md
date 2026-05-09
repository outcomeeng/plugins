<l2_local_infrastructure>

<purpose>
Use `l2` when the assertion needs real local infrastructure: Docker containers, local databases or queues, local dev servers, browser execution against local services, or project binaries installed during bootstrap.
</purpose>

<source_shape>
Keep production code testable before adding infrastructure. Separate command setup from domain behavior, inject process runners and clients, and place reusable setup in typed harnesses.
</source_shape>

<test_shape>

- Use real local dependencies through documented harnesses.
- Verify required binaries or services at harness construction time.
- Fail with a clear setup diagnostic when mandatory local infrastructure is unavailable.
- Keep generated data and source-owned protocol values under the same ownership rules as `l1`.

</test_shape>

<file_naming>
Use the canonical TypeScript test filename pattern from `/standardizing-typescript-tests`: `<subject>.<evidence>.<level>[.<runner>].test.ts`.

Examples: `postgres-user-store.scenario.l2.test.ts`, `checkout.scenario.l2.playwright.test.ts`, `asset-builder.conformance.l2.test.ts`.
</file_naming>

<example>

```typescript
import { createPostgresHarness } from "@testing/harnesses/postgres";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

describe("UserStore", () => {
  const postgres = createPostgresHarness();

  beforeAll(async () => {
    await postgres.startOrThrow("Install Docker before running UserStore l2 tests.");
  });

  afterAll(async () => {
    await postgres.stop();
  });

  it("persists and reloads users through the local database", async () => {
    const store = new UserStore(postgres.connectionString);
    const user = createTestUser();

    await store.save(user);

    await expect(store.findById(user.id)).resolves.toMatchObject(user);
  });
});
```

This is `l2` because the proof depends on a real local database. The harness factory returns the project-local typed harness, and `startOrThrow` is the expected setup API shape for mandatory infrastructure because it reports a clear diagnostic when the dependency is unavailable.

</example>

<reject>

- Replacing the local dependency with `vi.mock`, `jest.mock`, or a fake that hides the asserted behavior
- Duplicated server, database, browser, or project-binary setup across test files
- Passing tests that silently skip mandatory local evidence

</reject>

<success_criteria>
An `l2` TypeScript test is correct when it proves behavior against real local dependencies through documented harnesses and can run safely in a prepared CI or developer environment.
</success_criteria>

</l2_local_infrastructure>
