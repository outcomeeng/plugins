# Example Verdicts

Three canonical examples covering the verdict shapes the orchestrator emits. Match these byte-for-byte in spirit — the format is not negotiable.

## Example 1 — APPROVED, fresh run

Scope: `src/config/`, 7 files.

```markdown
# TypeScript Audit — APPROVED

**Scope hash:** `8f3c1d9a2e4b`
**Files audited:** 7
**Run:** fresh

| # | Concern                      | Status |
| - | ---------------------------- | ------ |
| 1 | Automated gates              | PASS   |
| 2 | Test execution               | PASS   |
| 3 | Implementation comprehension | PASS   |
| 4 | Test evidence                | PASS   |
| 5 | ADR/PDR compliance           | PASS   |
| 6 | Determinism contract         | PASS   |
```

That is the entire APPROVED output. No prose, no encouragement, no recommendations.

## Example 2 — REJECTED, fresh run

Scope: `src/orders/`, 4 files.

````markdown
# TypeScript Audit — REJECTED

**Scope hash:** `c7e2b4f1a8d6`
**Files audited:** 4
**Run:** fresh

## Verdict

| # | Concern                      | Status | One-line detail               |
| - | ---------------------------- | ------ | ----------------------------- |
| 1 | Automated gates              | PASS   | `pnpm validate` exit 0        |
| 2 | Test execution               | PASS   | 23/23 tests passed            |
| 3 | Implementation comprehension | REJECT | 1 finding                     |
| 4 | Test evidence                | REJECT | 1 finding                     |
| 5 | ADR/PDR compliance           | REJECT | 1 finding against 2 decisions |
| 6 | Determinism contract         | PASS   | scope frozen at Phase 0       |

## Findings

| # | File:line                           | Concern        | Root cause                                                      | Required fix                                                          |
| - | ----------------------------------- | -------------- | --------------------------------------------------------------- | --------------------------------------------------------------------- |
| 1 | src/orders/processor.ts:42          | comprehension  | processOrders tangles IO with computation                       | Extract pure computeOrderTotals; inject sendEmail via deps            |
| 2 | src/orders/processor.ts:3           | adr-compliance | Direct sendgrid import — 15-email.adr.md mandates DI            | Replace with EmailSender interface injected through deps              |
| 3 | tests/orders.scenario.l1.test.ts:18 | test-evidence  | Oracle derived from module under test (encode∘decode roundtrip) | Replace with canonical fixture imported from @testing/fixtures/orders |

## Detailed Findings

### Finding 1 — processOrders tangles IO with logic

**File:** `src/orders/processor.ts:42`
**Concern:** implementation comprehension, design coherence
**Why this fails:** Predict/verify revealed that `processOrders` both computes order totals and calls `sendgrid.send(...)` for each order. The function body does more than the name promises and the design fails the IO/logic separation rule — core computation cannot be tested without a mail server.

**Correct approach:**

```typescript
function computeOrderTotals(orders: Order[]): OrderSummary[] {
  // pure computation — no IO
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

### Finding 2 — Direct sendgrid import violates 15-email.adr.md

**File:** `src/orders/processor.ts:3`
**Concern:** ADR/PDR compliance
**Why this fails:** `import { send } from "@sendgrid/mail"` creates a hard dependency on SendGrid. `15-email.adr.md` Compliance section: "MUST inject email transport through the EmailSender interface".

**Correct approach:**

```typescript
interface EmailSender {
  send(to: string, subject: string, body: string): Promise<void>;
}

async function processOrders(
  orders: Order[],
  deps: { sendEmail: EmailSender },
): Promise<void> {
  // ...
}
```

### Finding 3 — Self-referential oracle in roundtrip test

**File:** `tests/orders.scenario.l1.test.ts:18`
**Concern:** test evidence (oracle independence)
**Why this fails:** The test asserts `expect(decodeOrder(encodeOrder(order))).toEqual(order)`. Both `encodeOrder` and `decodeOrder` live in `src/orders/codec.ts`. A shared bug — both functions strip trailing whitespace from `customerNotes` — passes the test because the roundtrip holds against the module's own behavior. The expected value must come from a source the module under test did not produce.

**Correct approach:**

```typescript
import { CANONICAL_ORDERS } from "@testing/fixtures/orders";

it("decodes the canonical wire format", () => {
  for (const { wire, decoded } of CANONICAL_ORDERS) {
    expect(decodeOrder(wire)).toEqual(decoded);
  }
});
```
````

## Example 3 — REJECTED, re-run after partial fix

Scope hash matches the prior run. The engineer fixed Finding 1 but left Finding 2 unchanged. Finding 3 was already correct in the prior run; it is not re-audited because it lives in an unchanged file.

````markdown
# TypeScript Audit — REJECTED

**Scope hash:** `c7e2b4f1a8d6`
**Files audited:** 4
**Run:** re-run

## Verdict

| # | Concern                      | Status | One-line detail                                |
| - | ---------------------------- | ------ | ---------------------------------------------- |
| 1 | Automated gates              | PASS   | `pnpm validate` exit 0                         |
| 2 | Test execution               | PASS   | 23/23 tests passed                             |
| 3 | Implementation comprehension | PASS   | prior finding resolved                         |
| 4 | Test evidence                | PASS   | prior finding resolved                         |
| 5 | ADR/PDR compliance           | REJECT | 1 finding persists from prior run              |
| 6 | Determinism contract         | PASS   | scope frozen at Phase 0; no new findings added |

## Findings

| # | File:line                 | Concern        | Root cause                                           | Required fix                                             |
| - | ------------------------- | -------------- | ---------------------------------------------------- | -------------------------------------------------------- |
| 1 | src/orders/processor.ts:3 | adr-compliance | Direct sendgrid import — 15-email.adr.md mandates DI | Replace with EmailSender interface injected through deps |

## Detailed Findings

### Finding 1 — Direct sendgrid import violates 15-email.adr.md

**File:** `src/orders/processor.ts:3`
**Concern:** ADR/PDR compliance
**Why this fails:** `import { send } from "@sendgrid/mail"` creates a hard dependency on SendGrid. `15-email.adr.md` Compliance section: "MUST inject email transport through the EmailSender interface".

**Correct approach:**

```typescript
interface EmailSender {
  send(to: string, subject: string, body: string): Promise<void>;
}

async function processOrders(
  orders: Order[],
  deps: { sendEmail: EmailSender },
): Promise<void> {
  // ...
}
```

## Resolved from prior run

| # | File:line                           | Prior root cause                                                | Status   |
| - | ----------------------------------- | --------------------------------------------------------------- | -------- |
| 1 | src/orders/processor.ts:42          | processOrders tangles IO with computation                       | RESOLVED |
| 2 | tests/orders.scenario.l1.test.ts:18 | Oracle derived from module under test (encode∘decode roundtrip) | RESOLVED |
````

Notice what the re-run does NOT do:

- It does not introduce a new finding on `src/orders/codec.ts` even though that file was untouched and Claude could plausibly find something on a fresh read.
- It does not rephrase Finding 2 into a "more comprehensive" critique.
- It does not append a "consider also" section.

The contract is: same scope hash, same finding catalog. Only resolution status changes between runs.
