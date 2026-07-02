<exception_implementations>

Table of contents: [exception_1](#exception_1) · [exception_2](#exception_2) · [exception_3](#exception_3) · [exception_4](#exception_4) · [exception_6](#exception_6)

<exception_1>

Retry logic, circuit breakers, error handling.

```typescript
import { FETCH_RETRY_CASES } from "@/retry-policy";
import { withRetryingHttpClient } from "@testing/harnesses/http/retry";

describe("fetchWithRetry", () => {
  it("retries on timeout", async () => {
    await withRetryingHttpClient(FETCH_RETRY_CASES.timeoutThenSuccess, async (client, expected) => {
      await expect(fetchWithRetry(expected.url, client)).resolves.toMatchObject(expected.response);
      expect(client.attempts()).toBe(expected.attempts);
    });
  });

  it("stops retrying after max attempts", async () => {
    await withRetryingHttpClient(FETCH_RETRY_CASES.alwaysTimeout, async (client, expected) => {
      await expect(fetchWithRetry(expected.url, client, expected.options)).rejects.toThrow(TimeoutError);
    });
  });
});
```

</exception_1>

<exception_2>

Call sequences, ordering, "no extra calls."

```typescript
import { withCachingClient } from "@testing/harnesses/cache";
import { withCompensatingSaga } from "@testing/harnesses/saga";

describe("Saga", () => {
  it("compensates in reverse order on failure", async () => {
    await withCompensatingSaga(async (saga, recorder) => {
      await expect(saga.run()).rejects.toThrow();
      expect(recorder.calls()).toEqual(recorder.expectedCompensationOrder());
    });
  });
});

describe("CachingWrapper", () => {
  it("does not refetch cached values", async () => {
    await withCachingClient(async (client, expected) => {
      await new CachingWrapper(client).getUser(expected.userId);
      await new CachingWrapper(client).getUser(expected.userId);
      await new CachingWrapper(client).getUser(expected.userId);

      expect(client.fetchCount()).toBe(expected.fetchCount);
    });
  });
});
```

</exception_2>

<exception_3>

Use `vi.useFakeTimers()` or an injected clock.

```typescript
import { withInjectedClock, withLeaseRenewalRecorder } from "@testing/harnesses/time";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("Lease", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("renews before expiry", async () => {
    await withLeaseRenewalRecorder(async (lease, recorder) => {
      await vi.advanceTimersByTimeAsync(recorder.beforeRenewalMs());
      expect(recorder.renewCount()).toBe(recorder.beforeRenewalCount());

      await vi.advanceTimersByTimeAsync(recorder.renewalDeltaMs());
      expect(recorder.renewCount()).toBe(recorder.afterRenewalCount());
    });
  });
});

describe("TokenRefresher", () => {
  it("refreshes before expiry with injected clock", async () => {
    await withInjectedClock(async (clock, recorder) => {
      new TokenRefresher(recorder.refresherOptions(clock)).tick();
      expect(recorder.refreshed()).toBe(false);

      clock.advanceToRefreshPoint();
      new TokenRefresher(recorder.refresherOptions(clock)).tick();
      expect(recorder.refreshed()).toBe(true);
    });
  });
});
```

</exception_3>

<exception_4>

Record intent without executing the dangerous operation.

```typescript
import { orderWithCharge } from "@testing/generators/orders";
import { withRefundRecordingProvider } from "@testing/harnesses/payments";

describe("OrderProcessor", () => {
  it("issues refund for cancelled order", async () => {
    await withRefundRecordingProvider(async (payment, recorder) => {
      await new OrderProcessor({ payment }).cancelOrder(orderWithCharge());
      expect(recorder.refunds()).toEqual(recorder.expectedRefunds());
    });
  });
});
```

</exception_4>

<exception_6>

Capture request details the real system cannot expose.

```typescript
import { createChargeRequest } from "@testing/generators/payments";
import { withRequestRecordingHttpClient } from "@testing/harnesses/http/requests";

describe("PaymentClient", () => {
  it("includes idempotency key in every request", async () => {
    await withRequestRecordingHttpClient(async (http, recorder) => {
      await new PaymentClient({ http }).charge(createChargeRequest());

      expect(recorder.requests()).toHaveLength(recorder.expectedRequestCount());
      expect(recorder.firstRequestHeaders()).toHaveProperty(recorder.idempotencyHeader());
    });
  });
});
```

</exception_6>

</exception_implementations>
