<exception_implementations>

Contents: `<exception_1>`, `<exception_2>`, `<exception_3>`, `<exception_4>`, `<exception_6>`

<exception_1>

Retry logic, circuit breakers, error handling.

```typescript
import { fetchWithRetry } from "@/http/retry";
import { FETCH_RETRY_CASES } from "@/retry-policy";
import { assertRetryPolicy } from "@testing/harnesses/http/retry";
import { describe, it } from "vitest";

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
import { CachingWrapper } from "@/cache/caching-wrapper";
import { assertCachingClientDoesNotRefetch } from "@testing/harnesses/cache";
import { assertCompensatingSagaOrder } from "@testing/harnesses/saga";
import { describe, it } from "vitest";

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
import { TokenRefresher } from "@/auth/token-refresher";
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
import { OrderProcessor } from "@/orders/order-processor";
import { orderWithCharge } from "@testing/generators/orders";
import { assertRefundIssuedForCancelledOrder } from "@testing/harnesses/payments";
import { describe, it } from "vitest";

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
import { PaymentClient } from "@/payments/client";
import { createChargeRequest } from "@testing/generators/payments";
import { assertChargeRequestCarriesIdempotencyKey } from "@testing/harnesses/http/requests";
import { describe, it } from "vitest";

describe("PaymentClient", () => {
  it("includes idempotency key in every request", async () => {
    await assertChargeRequestCarriesIdempotencyKey(createChargeRequest(), PaymentClient);
  });
});
```

</exception_6>

</exception_implementations>
