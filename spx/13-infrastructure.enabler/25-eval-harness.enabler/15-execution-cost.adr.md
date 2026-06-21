# Eval Execution Cost

Eval execution treats the plugin and system prompt prefix as a shared, server-cached asset: the harness minimizes the number of distinct cached prefixes across a run and schedules prefix-sharing invocations within the prompt cache's time-to-live, so each prefix is written to cache once and read warm across the cases that share it. Each eval invocation remains one bounded `claude --print` subprocess per `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`; cache warmth is a property of the server-side prompt cache, never of a resident process.

## Rationale

A model invocation's cost over a large plugin and system prefix is dominated by that prefix, not by the case-specific suffix or the short structured-verdict output. The prompt cache prices a cold write at several times a warm read of the same prefix, so a suite's cost is set by how often each distinct prefix is written cold rather than read warm. Two factors force cold writes: the number of distinct prefixes — a workflow that points each suite at a different plugin runtime writes each one cold — and gaps longer than the cache time-to-live, which evict a prefix so the next call rewrites it. One shared prefix scheduled within a single warm window collapses both to a single write followed by warm reads for the remainder of the run; the saving grows with the number of cases that share the prefix.

The lever is the prefix cache, not the base token rate. Selecting a cheaper model per suite trades verdict quality for a second-order saving while leaving the dominant prefix-write cost untouched, so prefix reuse — not model tiering — is the primary cost control.

The bounded-subprocess invariant is preserved without tension: separate `claude --print` subprocesses share the server-side cache by sending an identical prefix within the time-to-live, so no execution path holds a process open to keep context warm. The per-run prefix-cache read and creation token aggregates recorded by the harness are the feedback signal — a run dominated by cache creation rather than cache reads indicates prefix divergence or time-to-live expiry.

## Verification

### Audit

- ALWAYS: eval execution minimizes the number of distinct cached prefixes across a run, preferring one shared context over a distinct prefix per suite ([audit])
- ALWAYS: invocations that share a prefix are scheduled within the prompt cache's time-to-live, so the prefix is written once and read warm for the remainder of the run ([audit])
- ALWAYS: prefix reuse is the primary eval cost control, and the per-run cache read and creation token aggregates are its feedback signal ([audit])
- NEVER: an eval execution path holds a long-lived or resident process to keep context warm — warmth is a property of the server-side prompt cache, not of a process; each eval invocation stays a single bounded subprocess per `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md` ([audit])
- NEVER: per-suite model tier selection substitutes for prefix reuse as the primary cost lever — the dominant cost is the prefix write, not the base token rate ([audit])
