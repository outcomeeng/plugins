<l3_remote_credentialed>

<purpose>
Use `l3` only when the assertion requires remote, shared, credentialed, or network-dependent systems that cannot be reproduced with local real infrastructure.
</purpose>

<source_shape>
Do not hide remote complexity inside production modules. Route credentials, base URLs, clock behavior, and network clients through explicit boundaries so local tests can cover domain logic and `l3` tests only cover the remote contract.
</source_shape>

<test_shape>

- Read documented credentials or managed test-account harness functions.
- Fail loudly when selected evidence requires missing credentials.
- Never use `it.skip`, `it.skipIf`, or `test.skip`; when credentials or services are absent, throw with a clear diagnostic.
- Keep remote contract assertions narrow and tied to the spec assertion.

</test_shape>

<file_naming>
Use the canonical TypeScript test filename pattern from `/typescript-test-standards`: `<subject>.<evidence>.<level>[.<runner>].test.ts`.

Examples: `stripe-webhook.conformance.l3.test.ts`, `production-login.scenario.l3.playwright.test.ts`, `billing-retry.compliance.l3.test.ts`.
</file_naming>

<example>

```typescript
import { WEBHOOK_ACCEPTED_STATUS } from "@/stripe-webhook";
import { assertSignedStripeFixtureAccepted } from "@testing/harnesses/stripe";
import { describe, expect, it } from "vitest";

describe("Stripe webhook contract", () => {
  it("accepts signed fixture events through the remote contract endpoint", async () => {
    await expect(assertSignedStripeFixtureAccepted()).resolves.toMatchObject({ status: WEBHOOK_ACCEPTED_STATUS });
  });
});
```

This is `l3` because the assertion depends on a remote credentialed contract. Missing credentials fail loudly from the credential harness instead of producing a passing test. `submitSignedFixture` reads the illustrative fixture path from disk, signs its contents locally, and submits the payload; the remote endpoint never receives a filesystem path.

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
