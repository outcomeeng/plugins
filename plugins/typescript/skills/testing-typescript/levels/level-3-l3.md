<objective>
TypeScript `l3` test patterns for evidence that requires remote, shared, credentialed, or network-dependent systems.
</objective>

<when_to_use>
Use `l3` when the evidence requires:

- Live third-party services
- Shared preview or production-like environments
- Credentials or managed test accounts
- Remote browser execution against a deployed app
- Contract evidence that cannot be reproduced locally

`l3` is still evidence-driven. Do not create an `l3` test only because a flow is end-to-end; use `l2` when the same proof is available through local real infrastructure.
</when_to_use>

<file_naming>
Use the `/standardizing-typescript-tests` filename pattern:

```text
<subject>.<evidence>.l3[.<runner>].test.ts
```

Examples:

- `stripe-webhook.conformance.l3.test.ts`
- `github-release.scenario.l3.test.ts`
- `production-login.scenario.l3.playwright.test.ts`
- `billing-boundary.compliance.l3.test.ts`

</file_naming>

<credential_policy>
Credentialed tests must fail or skip intentionally:

- Use documented environment variables or secret helpers
- Fail loudly when the selected command requires the credential
- Skip only when the test suite marks the evidence as optional for that command
- Never let a missing credential become a passing test

```typescript
function requireStripeToken(): string {
  const token = process.env.STRIPE_TEST_TOKEN;
  if (!token) {
    throw new Error("STRIPE_TEST_TOKEN is required for this l3 contract test");
  }
  return token;
}
```

</credential_policy>

<patterns>
Remote contract example:

```typescript
import { describe, expect, it } from "vitest";

describe("Stripe webhook contract", () => {
  it("accepts signed fixture events", async () => {
    const token = requireStripeToken();

    const response = await submitSignedFixture({
      token,
      fixtureName: "checkout-session-completed",
    });

    expect(response.status).toBe(200);
  });
});
```

Remote browser example:

```typescript
// production-login.scenario.l3.playwright.test.ts
import { expect, test } from "@playwright/test";

test("operator can sign in to the shared preview app", async ({ page }) => {
  await page.goto(process.env.PREVIEW_BASE_URL ?? "");
  await page.getByLabel("Email").fill(requirePreviewEmail());
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});
```

</patterns>

<success_criteria>
An `l3` TypeScript test is correct when it proves behavior only available through remote or credentialed systems, uses documented credential handling, and never passes silently when required evidence cannot run.
</success_criteria>
