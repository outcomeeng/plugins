# Adapter Contract

Every verification surface reaches a coding-agent runtime through one adapter per runtime realizing a shared invocation contract. An invocation is parameterized by the skill selection, the prepared workspace, the trial count, and explicit bounded ceilings — budget and timeout; each trial is exactly one bounded runtime subprocess. The adapter provisions the trial's trace-sink path and returns one structured result envelope per trial carrying the runtime's machine-verifiable output verbatim plus telemetry — duration, cost, input and output tokens, cache read and creation tokens, turn count, and stop reason. Runtime-specific invocation mechanics live in the runtime substrate children; grading, conformance checking, and verdict semantics live outside the adapter.

## Rationale

One shared contract lets evaluate, audit, and review surfaces drive the real runtime behavior they verify instead of simulating a runtime per surface, and per-runtime adapters isolate invocation mechanics so a new runtime is an added substrate rather than a changed consumer. A per-case prompt call is the degenerate invocation this contract subsumes: skill selection empty, one trial, the prompt as the workspace's whole input. Trial repetition is adapter mechanics — bounded, telemetered re-invocation — while trial counting, thresholds, and verdicts stay with the eval lane, per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`'s split between deterministic execution and verdict semantics. Single bounded subprocesses follow `spx/13-plugin-and-runtime-conventions.adr.md`; verbatim telemetry follows the product-level verbatim-identity rule in `spx/outcomeeng.product.md`.

## Verification

- ALWAYS: each trial is one bounded subprocess with explicit budget and timeout ceilings, and no resident process, watcher, or polling loop survives an invocation
- ALWAYS: the result envelope carries the runtime's structured output and telemetry fields verbatim; telemetry a runtime does not expose surfaces as null, never as a fabricated zero
- NEVER: the adapter judges, grades, filters, or repairs the runtime's output — verdicts belong to the consuming verification surface
- ALWAYS: runtime-specific invocation mechanics — binary, flags, plugin loading, envelope parsing, authentication mode — live in that runtime's substrate child, and consumers depend only on the shared contract
- ALWAYS: the adapter provisions the per-trial trace-sink path and never reads or interprets the trace collected through it
- NEVER: the adapter raises a budget, timeout, trial, or worker ceiling beyond what its caller supplied — ceiling increases are operator-approved at the caller
