# Coherence Audit Orchestration

Changeset coherence is an artifact-type audit driven by the `audit-changeset-coherence` skill and exposed through one thin `changeset-coherence-auditor` wrapper agent. The skill consumes an exact committed changeset through the shared changeset-scope primitives, applies the review-unit model in `spx/21-spec-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/15-review-unit-coherence.pdr.md`, and records coverage, findings, terminal state, and the structured result through one SPX verification run governed by `spx/21-spec-tree.enabler/16-verification.enabler/13-run-journal.adr.md` and `spx/21-spec-tree.enabler/17-audit.adr.md`.

## Rationale

Skill-owned judgment keeps the behavior portable across runtime agents, while the shared changeset-scope and verification-run surfaces provide deterministic identity and durable projection without a plugin-side state format. A standalone helper would duplicate git and run-journal behavior already owned by published SPX capabilities and would leave semantic clustering outside the artifact that eval evidence exercises.

## Invariants

- Every authored artifact in scope belongs to exactly one semantic cluster, while each deterministic generated artifact belongs to the same cluster as its producing authored artifact.
- The recommended review-unit sequence covers every semantic cluster exactly once; dependency cycles collapse into one inseparable cluster before the sequence is ordered.

## Verification

### Eval

- ALWAYS: the audit classifies semantic cohesion from behavioral claims, verification stories, rollback stories, generated-source relationships, dependencies, and independent mergeability ([eval])
- ALWAYS: the audit returns `UNKNOWN` when required evidence cannot establish a defensible classification and never treats missing evidence as approval ([eval])
- NEVER: raw line count, file count, path breadth, or an uncalibrated review-load score determines the terminal classification by itself ([eval])

### Audit

- ALWAYS: the `changeset-coherence-auditor` wrapper invokes `spec-tree:audit-changeset-coherence`, preserves the caller's exact committed scope, and relays the SPX run token and rendered projection without owning audit policy ([audit])
- ALWAYS: the audit skill derives changeset identity through the shared changeset-scope primitives and persists audit state only through `spx verification run` ([audit])
- NEVER: a plugin-side helper, tracked file, rendered comment, or wrapper prompt becomes the source of coherence state or verdict policy ([audit])
