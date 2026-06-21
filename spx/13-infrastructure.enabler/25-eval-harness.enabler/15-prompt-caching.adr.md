# Prompt Caching

Eval execution holds one prompt prefix constant across a run so the model's prompt cache serves it warm. The harness issues a run's invocations against a single shared plugin-and-system prefix: the first invocation writes the prefix to the cache, and every later invocation in the run reads it warm. Each invocation remains one bounded `claude --print` subprocess (the single-bounded-invocation rule is owned by `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`, per `spx/13-plugin-and-runtime-conventions.adr.md`) — so cache warmth comes from the server-side prompt cache, never from a resident process this decision would otherwise tempt the harness to hold open.

## Rationale

The prompt prefix dominates a model invocation's cost: a large plugin-and-system prefix far outweighs the case-specific suffix and the short structured-verdict output. The prompt cache prices a cold write at several times a warm read of the same prefix, so a run's cost is governed by how many distinct prefixes it writes cold rather than reads warm. Holding one prefix across a run collapses the cost to a single write followed by warm reads, and the saving grows with the number of cases that share it.

Two forces break the amortization. Distinct prefixes — pointing each suite at a different plugin runtime — write each one cold. Gaps longer than the cache time-to-live evict a prefix, so the next invocation rewrites it. The harness therefore keeps one prefix and issues a run's prefix-sharing invocations within a single warm window.

Prefix reuse, not per-suite model tiering, is the cost lever. A cheaper model per suite trades verdict quality for a second-order saving while leaving the dominant prefix-write cost untouched.

The measurable target is the per-run equivalent API cost the harness records — `total_cost_usd`, derived from the cache read and creation token aggregates (per `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`); cache creation dominating cache reads across a run shows that equivalent cost rising from prefix divergence or time-to-live expiry. Execution stays on the `claude --print` path so this figure is a comparable equivalent cost rather than a real per-token bill — routing eval calls to metered provider APIs to seize cache control would convert the signal into actual spend for control the cached `claude --print` path already provides, while subscription capacity and rate limits are not observable to the harness and so are not a target it optimizes.

## Verification

### Testing

- ALWAYS: a run's invocations are issued against a single shared prompt prefix — a recording runner capturing a run's invocations observes one distinct prefix, written by the first invocation and read warm by the rest ([compliance])

### Audit

- ALWAYS: the harness accepts its model runner as a dependency-injected parameter implementing the `ModelRunner` Protocol, so a recording implementation substitutes the real `claude --print` runner and captures a run's invocations for the `### Testing` rules above ([audit])
- ALWAYS: the per-run cache read and creation token aggregates the harness records — surfaced as `total_cost_usd`, `cost_summary`, and `history.jsonl` per `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md` — are the feedback signal for prefix-reuse effectiveness: cache creation dominating cache reads across a run marks prefix divergence or time-to-live expiry ([audit])
- NEVER: per-suite model-tier selection is the primary eval cost mechanism in place of prefix reuse — the dominant cost is the prefix write, not the base token rate, so the cost strategy stays prefix reuse ([audit])
