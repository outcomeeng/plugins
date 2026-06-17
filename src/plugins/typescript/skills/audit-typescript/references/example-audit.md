<examples>

<example name="approved">

Auditing `src/config/` for a CLI tool after Phase 1 and Phase 2 passed.

# CODE REVIEW

**Decision:** APPROVED

## Verdict

| # | Concern                | Status | Detail                                 |
| - | ---------------------- | ------ | -------------------------------------- |
| 1 | Automated gates        | PASS   | `pnpm validate` -- zero warnings       |
| 2 | Test execution         | PASS   | 47/47 tests, 84% coverage              |
| 3 | Function comprehension | PASS   | 12 functions, no surprises             |
| 4 | Design coherence       | PASS   | IO separated, DI used, SRP maintained  |
| 5 | Import structure       | PASS   | All aliases correct, no deep relatives |
| 6 | ADR/PDR compliance     | PASS   | 15-database.adr.md constraints met     |

---

Code meets standards.

</example>

<example name="rejected-design-flaw">

Auditing `src/orders/` for an e-commerce service.

# CODE REVIEW

**Decision:** REJECTED

## Verdict

| # | Concern                | Status | Detail                                         |
| - | ---------------------- | ------ | ---------------------------------------------- |
| 1 | Automated gates        | PASS   | `just validate` -- zero warnings               |
| 2 | Test execution         | PASS   | 23/23 tests pass                               |
| 3 | Function comprehension | REJECT | processOrders tangles IO with logic            |
| 4 | Design coherence       | REJECT | IO/logic separation violated                   |
| 5 | Import structure       | PASS   | Aliases correctly configured                   |
| 6 | ADR/PDR compliance     | REJECT | ADR mandates DI for all external service calls |

---

## Findings

### processOrders tangles IO with computation

**Where:** `src/orders/processor.ts:42`
**Concern:** Function comprehension, Design coherence
**Why this fails:** Predict/verify revealed `processOrders` both computes order totals AND sends confirmation emails via `sendgrid.send()`. IO and logic are tangled -- the function cannot be tested without an email service.

Predict: "Given the name `processOrders`, I predict this processes a list of orders and returns results."
Verify: The body computes totals (expected), then calls `sendgrid.send()` for each order (surprise -- IO mixed with computation).

**Correct approach:**

```typescript
// Separate computation from IO
function computeOrderTotals(orders: Order[]): OrderSummary[] {
  // Pure computation -- no IO
}

async function processOrders(
  orders: Order[],
  deps: { sendEmail: EmailSender },
): Promise<void> {
  const summaries = computeOrderTotals(orders);
  for (const summary of summaries) {
    await deps.sendEmail(summary.confirmation);
  }
}
```

---

### Direct SendGrid import violates ADR DI constraint

**Where:** `src/orders/processor.ts:3`
**Concern:** ADR/PDR compliance
**Why this fails:** `import { send } from "@sendgrid/mail"` -- `15-email.adr.md` requires all external service calls to use dependency injection. Direct import creates a hard dependency on SendGrid.

**Correct approach:**

```typescript
// Define interface for email sending
interface EmailSender {
  send(to: string, subject: string, body: string): Promise<void>;
}

// Inject dependency
async function processOrders(
  orders: Order[],
  deps: { sendEmail: EmailSender },
): Promise<void> {
  // ...
}
```

---

## Required Changes

1. Extract `computeOrderTotals` as pure function (no IO)
2. Inject email sending dependency via `deps` parameter
3. Remove direct SendGrid import

---

Fix issues and resubmit for review.

</example>

<example name="rejected-gates-failed">

Short example showing early termination.

# CODE REVIEW

**Decision:** REJECTED

## Verdict

| # | Concern                | Status | Detail                     |
| - | ---------------------- | ------ | -------------------------- |
| 1 | Automated gates        | REJECT | 3 ESLint errors            |
| 2 | Test execution         | --     | Blocked by Phase 1 failure |
| 3 | Function comprehension | --     | Blocked by Phase 1 failure |
| 4 | Design coherence       | --     | Blocked by Phase 1 failure |
| 5 | Import structure       | --     | Blocked by Phase 1 failure |
| 6 | ADR/PDR compliance     | --     | Blocked by Phase 1 failure |

---

## Required Changes

1. Fix 3 ESLint errors reported by `pnpm validate`

---

Fix issues and resubmit for review.

</example>

</examples>
