<exception_implementations>

Table of contents: [exception_1](#exception_1) · [exception_2](#exception_2) · [exception_3](#exception_3) · [exception_4](#exception_4) · [exception_6](#exception_6)

<exception_1>

Retry logic, circuit breakers, error handling.

```typescript
import { FETCH_RETRY_CASES } from "@/retry-policy";
import { assertRetryPolicy } from "@testing/harnesses/http/retry";

describe("fetchWithRetry", () => {
  it("retries on timeout", async () => {
    await assertRetryPolicy(FETCH_RETRY_CASES.timeoutThenSuccess, fetchWithRetry);
  });

  it("stops retrying after max attempts", async () => {
    await assertRetryPolicy(FETCH_RETRY_CASES.alwaysTimeout, fetchWithRetry);
  });
});
```

</exception_1>

<exception_2>

Call sequences, ordering, "no extra calls."

```typescript
import { assertCachingClientDoesNotRefetch } from "@testing/harnesses/cache";
import { assertCompensatingSagaOrder } from "@testing/harnesses/saga";

describe("Saga", () => {
  it("compensates in reverse order on failure", async () => {
    await assertCompensatingSagaOrder();
  });
});

describe("CachingWrapper", () => {
  it("does not refetch cached values", async () => {
    await assertCachingClientDoesNotRefetch(CachingWrapper);
  });
});
```

</exception_2>

<exception_3>

Use `vi.useFakeTimers()` or an injected clock.

```typescript
import { assertLeaseRenewsBeforeExpiry, assertTokenRefreshesBeforeExpiry } from "@testing/harnesses/time";
import { afterEach, beforeEach, describe, it, vi } from "vitest";

describe("Lease", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("renews before expiry", async () => {
    await assertLeaseRenewsBeforeExpiry(vi);
  });
});

describe("TokenRefresher", () => {
  it("refreshes before expiry with injected clock", async () => {
    await assertTokenRefreshesBeforeExpiry(TokenRefresher);
  });
});
```

</exception_3>

<exception_4>

Record intent without executing the dangerous operation.

```typescript
import { orderWithCharge } from "@testing/generators/orders";
import { assertRefundIssuedForCancelledOrder } from "@testing/harnesses/payments";

describe("OrderProcessor", () => {
  it("issues refund for cancelled order", async () => {
    await assertRefundIssuedForCancelledOrder(orderWithCharge(), OrderProcessor);
  });
});
```

</exception_4>

<exception_6>

Capture request details the real system cannot expose.

```typescript
import { createChargeRequest } from "@testing/generators/payments";
import { assertChargeRequestCarriesIdempotencyKey } from "@testing/harnesses/http/requests";

describe("PaymentClient", () => {
  it("includes idempotency key in every request", async () => {
    await assertChargeRequestCarriesIdempotencyKey(createChargeRequest(), PaymentClient);
  });
});
```

</exception_6>

</exception_implementations>
