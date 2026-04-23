<objective>
TypeScript `l2` test patterns for evidence that requires real local dependencies or heavier local setup.
</objective>

<when_to_use>
Use `l2` when the evidence requires:

- Docker containers
- Local databases or queues
- Local dev servers
- Browser execution against local infrastructure
- Project-specific binaries such as Hugo, Caddy, or a CLI installed during bootstrap

`l2` still uses real dependencies. Avoid replacing the dependency with `vi.mock`, `jest.mock`, or a fake that hides the behavior the assertion is about.
</when_to_use>

<file_naming>
Use the `/standardizing-typescript-tests` filename pattern:

```text
<subject>.<evidence>.l2[.<runner>].test.ts
```

Examples:

- `postgres-user-store.scenario.l2.test.ts`
- `hugo-build.scenario.l2.test.ts`
- `browser-auth.scenario.l2.playwright.test.ts`
- `api-schema.conformance.l2.test.ts`

</file_naming>

<patterns>
Harness-first local dependency example:

```typescript
import { PostgresHarness } from "@testing/harnesses/postgres";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

describe("UserStore", () => {
  const postgres = new PostgresHarness();

  beforeAll(async () => {
    await postgres.start();
  });

  afterAll(async () => {
    await postgres.stop();
  });

  it("persists and reloads users", async () => {
    const store = new UserStore(postgres.connectionString);

    await store.save({ id: "user-1", email: "ada@example.com" });

    await expect(store.findById("user-1")).resolves.toMatchObject({
      email: "ada@example.com",
    });
  });
});
```

Local browser runner example:

```typescript
// browser-auth.scenario.l2.playwright.test.ts
import { expect, test } from "@playwright/test";

test("user can sign in against the local dev server", async ({ page }) => {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill("ada@example.com");
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByText("Welcome")).toBeVisible();
});
```

</patterns>

<success_criteria>
An `l2` TypeScript test is correct when it proves behavior against real local dependencies through documented harnesses and can run safely in a prepared CI or developer environment.
</success_criteria>
