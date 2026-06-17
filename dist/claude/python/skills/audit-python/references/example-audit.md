<examples>

<example name="approved">

Auditing `product/config/` for a CLI tool after Phase 1 and Phase 2 passed.

# CODE REVIEW

**Decision:** APPROVED

## Verdict

| # | Concern                | Status | Detail                                     |
| - | ---------------------- | ------ | ------------------------------------------ |
| 1 | Automated gates        | PASS   | the product check command -- zero warnings |
| 2 | Test execution         | PASS   | 47/47 tests, 84% coverage                  |
| 3 | Function comprehension | PASS   | 12 functions, no surprises                 |
| 4 | Design coherence       | PASS   | IO separated, DI used, SRP maintained      |
| 5 | Import structure       | PASS   | All package imports, no deep relatives     |
| 6 | ADR/PDR compliance     | PASS   | 15-database.adr.md constraints met         |

---

Code meets standards.

</example>

<example name="rejected-design-flaw">

Auditing `product/orders/` for a web service.

# CODE REVIEW

**Decision:** REJECTED

## Verdict

| # | Concern                | Status | Detail                                         |
| - | ---------------------- | ------ | ---------------------------------------------- |
| 1 | Automated gates        | PASS   | the product check command -- zero warnings     |
| 2 | Test execution         | PASS   | 23/23 tests pass                               |
| 3 | Function comprehension | REJECT | process_orders tangles IO with logic           |
| 4 | Design coherence       | REJECT | IO/logic separation violated                   |
| 5 | Import structure       | PASS   | Package imports correctly used                 |
| 6 | ADR/PDR compliance     | REJECT | ADR mandates DI for all external service calls |

---

## Findings

### process_orders tangles IO with computation

**Where:** `product/orders/processor.py:42`
**Concern:** Function comprehension, Design coherence
**Why this fails:** Predict/verify revealed `process_orders` both computes order totals AND sends confirmation emails via `sendgrid.send()`. IO and logic are tangled -- the function cannot be tested without an email server.

Predict: "Given the name `process_orders`, I predict this processes a list of orders and returns results."
Verify: The body computes totals (expected), then calls `sendgrid.send()` for each order (surprise -- IO mixed with computation).

**Correct approach:**

```python
from typing import Protocol


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


def compute_order_totals(orders: list[Order]) -> list[OrderSummary]:
    """Pure computation -- no IO."""
    ...


async def process_orders(
    orders: list[Order],
    *,
    send_email: EmailSender,
) -> None:
    summaries = compute_order_totals(orders)
    for summary in summaries:
        await send_email.send(summary.to, summary.subject, summary.body)
```

---

### Direct sendgrid import violates ADR DI constraint

**Where:** `product/orders/processor.py:3`
**Concern:** ADR/PDR compliance
**Why this fails:** `from sendgrid import SendGridAPIClient` -- `15-email.adr.md` requires all external service calls to use dependency injection. Direct import creates a hard dependency on SendGrid.

**Correct approach:**

```python
from typing import Protocol


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


# Inject dependency via function parameter
async def process_orders(
    orders: list[Order],
    *,
    send_email: EmailSender,
) -> None: ...
```

---

## Required Changes

1. Extract `compute_order_totals` as pure function (no IO)
2. Inject email sending dependency via Protocol parameter
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
| 1 | Automated gates        | REJECT | 3 ruff errors, 1 mypy      |
| 2 | Test execution         | --     | Blocked by Phase 1 failure |
| 3 | Function comprehension | --     | Blocked by Phase 1 failure |
| 4 | Design coherence       | --     | Blocked by Phase 1 failure |
| 5 | Import structure       | --     | Blocked by Phase 1 failure |
| 6 | ADR/PDR compliance     | --     | Blocked by Phase 1 failure |

---

## Required Changes

1. Fix 3 ruff errors and 1 mypy error reported by the product check command

---

Fix issues and resubmit for review.

</example>

</examples>
