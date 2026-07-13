# Plan: audit runtime activation

Coordination note; product truth lives in the governing decisions and specs.

## Prepared plugin surface

The branch `work/audit-runtime-evidence` preserves the implementation-auditor
wrapper, Python concern-skill alignment, and a checkout-local Codex runtime for
exercising unpublished plugin versions without changing user-scoped Codex
state. The local-runtime evidence exposes structured observations to typed tests
rather than returning harness-owned verdicts.

## Blocking SPX capability

Implementation-auditor activation resumes after a published SPX version provides
the deterministic applicability boundary recorded in `ISSUES.md`. Until then,
the plugin does not filter a mixed changeset heuristically, reinterpret
documentation as unsupported implementation, or create a synthetic approved run
for an empty implementation scope.

## First slice after publication

Actor: an operator dispatching `implementation-auditor` for an exact committed
Python implementation context accepted by SPX.

Invocation: the caller passes the persisted context after deterministic
verification succeeds.

Behavior: the auditor invokes `audit-python-code`, `audit-python-tests`, and
`audit-python-architecture` in one isolated context and records their coverage
and findings in one verification run.

Persisted and inspected result: the sealed projection carries stable producer
identity, plugin provenance, authoritative finding count, and terminal status.

Failure behavior: SPX rejects an empty or mixed-artifact implementation context
before creating the run journal. Missing concern skills and rejected evidence
commands follow the published run contract.

Verification:

- Run one finding-free committed Python implementation context.
- Run one finding-bearing committed Python implementation context and confirm
  all three concern skills contribute to the same sealed run.
- Feed a rendered finding explicitly into the corresponding Python fix workflow.
- Run the applicable skill, subagent, evidence, spec, implementation, and
  changeset-review gates over one clean committed head.
- Run the full deterministic gate after the agentic gates converge, then merge
  through the configured lifecycle and repeat the representative runtime check
  from the published plugin version.

## Later slices

- Add TypeScript and Rust implementation-audit runtime evidence.
- Move the remaining artifact-type auditors onto the shared verification-run
  context and persistence contract.
- Consume SPX run-set restoration so later auditors receive relevant prior runs
  from the same merge period.
