<l3_remote_credentialed>

<purpose>
Use `l3` only when the assertion requires remote, shared, credentialed, or network-dependent systems that cannot be reproduced with local real infrastructure.
</purpose>

<source_shape>
Do not hide remote complexity inside production modules. Route credentials, base URLs, clock behavior, and network clients through explicit boundaries so local tests can cover domain logic and `l3` tests only cover the remote contract.
</source_shape>

<test_shape>

- Read documented credentials or managed test-account helpers.
- Fail loudly when selected evidence requires missing credentials.
- Skip only when the suite explicitly marks the remote evidence optional for that command.
- Keep remote contract assertions narrow and tied to the spec assertion.

</test_shape>

<file_naming>
Use the canonical TypeScript test filename pattern from `/standardizing-typescript-tests`: `<subject>.<evidence>.<level>[.<runner>].test.ts`.

Examples: `stripe-webhook.conformance.l3.test.ts`, `production-login.scenario.l3.playwright.test.ts`, `billing-retry.compliance.l3.test.ts`.
</file_naming>

<example>

```typescript
import { submitSignedFixture } from "@testing/harnesses/stripe";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

type StripeCredentials = {
  readonly token: string;
};

function requireStripeCredentials(): StripeCredentials {
  const token = process.env.STRIPE_TEST_TOKEN;
  if (!token) {
    throw new Error(
      "STRIPE_TEST_TOKEN is required for stripe-webhook.conformance.l3.test.ts.",
    );
  }
  return { token };
}

describe("Stripe webhook contract", () => {
  it("accepts signed fixture events through the remote contract endpoint", async () => {
    const credentials = requireStripeCredentials();
    const response = await submitSignedFixture({
      token: credentials.token,
      fixturePath: resolve(process.cwd(), "testing/fixtures/stripe-event.json"),
    });

    expect(response.status).toBe(200);
  });
});
```

This is `l3` because the assertion depends on a remote credentialed contract. Missing credentials fail loudly instead of producing a passing test. `submitSignedFixture` reads the illustrative fixture path from disk, signs its contents locally, and submits the payload; the remote endpoint never receives a filesystem path.

</example>

<reject>

- Escalating to `l3` because a flow feels end-to-end while equivalent local evidence exists
- Passing silently when required credentials, base URLs, or remote services are absent
- Combining broad remote smoke tests with many unrelated assertions

</reject>

<success_criteria>
An `l3` TypeScript test is correct when it proves behavior only available through remote or credentialed systems, uses documented credential handling, and never passes silently when required evidence cannot run.
</success_criteria>

</l3_remote_credentialed>
