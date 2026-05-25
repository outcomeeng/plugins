<l2_local_infrastructure>

<purpose>
Use `l2` when the assertion needs real local infrastructure: Docker containers, local databases or queues, local dev servers, browser execution against local services, or product binaries installed during bootstrap.
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
import { createGeneratedUser } from "@testing/generators/users";
import { createPostgresHarness, type PostgresHarness } from "@testing/harnesses/postgres";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

describe("UserStore", () => {
  const postgres: PostgresHarness = createPostgresHarness();

  beforeAll(async () => {
    await postgres.startOrThrow("Install Docker before running UserStore l2 tests.");
  });

  afterAll(async () => {
    await postgres.stop();
  });

  it("persists and reloads users through the local database", async () => {
    const store = new UserStore(postgres.connectionString);
    const user = createGeneratedUser();

    await store.save(user);

    await expect(store.findById(user.id)).resolves.toMatchObject(user);
  });
});
```

This is `l2` because the evidence depends on a real local database. The harness module exports both the factory and `PostgresHarness` type; the type includes `startOrThrow(setupMessage)` and `stop()` so mandatory infrastructure failures report a clear diagnostic. The generated user comes from `@testing/generators/`, not from fixture exports.

`createGeneratedUser()` is a single-sample helper backed by a fast-check arbitrary. Use that form when infrastructure setup cost makes a full property loop inappropriate, and keep pure `fc.Arbitrary<T>` helpers for tests that should search a variable domain.

</example>

<migration_note>
Older projects may have harnesses shaped like `new PostgresHarness()` plus `start()`. Migrate the harness when the test itself is being rewritten, rather than making harness migration a prerequisite for unrelated fixes. When migrating, move toward a typed factory plus `startOrThrow(setupMessage)` so missing local infrastructure fails with the diagnostic at the call site. If a product already has a documented equivalent API, keep the local name while preserving the same contract: typed handle, explicit setup failure message, and cleanup method.
</migration_note>

<reject>

- Replacing the local dependency with `vi.mock`, `jest.mock`, or a fake that hides the asserted behavior
- Duplicated server, database, browser, or product-binary setup across test files
- Passing tests that silently skip mandatory local evidence

</reject>

<success_criteria>
An `l2` TypeScript test is correct when it proves behavior against real local dependencies through documented harnesses and can run safely in a prepared CI or developer environment.
</success_criteria>

</l2_local_infrastructure>
