# Issues - Audit

Known follow-ups for the audit node. Coordination note; not spec truth.

## Compliance-lane tests read as `assert harness_call()`

`spec-tree:test-evidence-standards` `<predicate_seam>` and
`python:python-test-standards` `<predicate_and_oracle_litmus>` reject a test whose
body is a bare `assert helper(...)`: the harness computes the verdict, no
behavioral predicate is visible in the executed test, a failure reports only
`assert False` with no observed-versus-expected diagnostic, and inverting the
claim requires editing the harness rather than the test.

The scenario lane of this node is converted — `observe_implementation_audit_lifecycle`
and `observe_mismatched_terminal_status_finish` expose observations, and
`tests/test_implementation_audit_contract.scenario.l1.py` owns every predicate.
The compliance lane still carries the rejected shape:

- `spx/21-spec-tree.enabler/68-audit.enabler/tests/test_implementation_audit_contract.compliance.l1.py` — 16 functions
- `spx/21-spec-tree.enabler/68-audit.enabler/21-state-surface.enabler/tests/test_implementation_audit_runtime.compliance.l1.py`
- `spx/21-spec-tree.enabler/16-verification.enabler/15-verdict-toolchain.enabler/tests/test_verification_run_payload_contract.compliance.l1.py`

**Why this is a separate larger concern.** Each of those functions backs a
different compliance assertion, and the harness functions behind them return a
boolean derived from a distinct check — surface validation, filename rejection,
payload rejection, trio completeness. Converting them is not one mechanical
rename: every function needs its own observation shape designed against the
assertion it backs, and the surrounding assertions in three nodes across two
subtrees are re-audited against those shapes. The scenario-lane conversion
landed with the finding that surfaced it because that lane's evidence was
already being changed; the compliance lane is untouched by that change.

**Resolution shape**: convert one compliance file at a time, designing each
harness function's observation from the assertion it backs, and gate each file
with `spec-tree:test-evidence-auditor` before moving to the next.

**Evidence.** Surfaced by `spec-tree:test-evidence-auditor` on the
implementation-audit idempotency-key changeset, which audited the scenario
assertion and named the same defect class in the other two functions of that
file.

## Implementation audit has incomplete mixed-changeset coverage

The implementation auditor has no skill covering workflow YAML, so a changeset
scope including `.github/workflows/*.yml` rejects audit setup with
`missing required skill: audit-yaml-kind`. `actionlint` covers workflow syntax,
and the changeset review gate owns full-diff review of that surface meanwhile.

Open decision: whether workflow YAML receives a dedicated YAML audit skill or
routes to a workflow-specific audit surface. Once decided,
`implementation-auditor` reports that coverage without requiring callers to
split YAML out of an otherwise valid changeset.

Two further gaps block a gating implementation audit:

- Mixed-changeset partitioning is not reproducible across verifier runs. The
  same branch yields different coverage projections — one run collecting
  unsupported files into a required `unsupported` unit and sealing `rejected`
  with zero findings, another recording no unsupported unit and sealing
  `approved`. Gating depends on how orchestration classifies supported language
  and artifact partitions, and on distinguishing files outside
  implementation-audit ownership from missing required implementation coverage.
- The verifier output contract needs one post-completion projection whose seal
  and event prefix agree; a terminal projection reporting `sealed: true`
  alongside an event projection reporting `sealed: false` and omitting the
  terminal event leaves no single authoritative read.

## SPX audit verification contract follow-ups

The plugin implementation-auditor model records implementation-audit coverage, findings, terminal state, and projections through `spx verification run`. The remaining issues live in the SPX verification-run contract rather than in plugin-side verdict scripts.

Open gaps:

- Audit scope payloads require stable producer identity and producer provenance for every unit, but `missing-skill`, `unsupported`, and `coverage-gap` units may have no executed leaf skill and sometimes no skill or plugin version. SPX should distinguish the run driver that recorded the unit from the expected producer that would have covered it, and make provenance optional when the expected producer is absent.
- The `coverage-gap` audit kind the skill contract documents is rejected by the installed CLI. `spx` 0.6.22 fails a `scope add` payload carrying `auditKind: "coverage-gap"` with `spx verification run scope add payload failed verification-type validation`, so a run that records a not-applicable language partition must substitute a concern-matching kind (`code`, `tests`, `architecture`) with `coverageStatus: "not-applicable"`. Either the CLI accepts the documented value or the skill contract drops it; until then every implementation-audit run over a single-language changeset carries a silent substitution. Observed while auditing `spx/13-infrastructure.enabler/13-host-readiness.enabler`.
- Audit unit identity and subject normalization are not specified. SPX should define deterministic `unit_id` derivation, parent/child identity stability, and normalized subject shape so findings, coverage gaps, and prior-run context converge across repeated runs.
- Audit class/kind validation needs a compatibility matrix for `instructions`, `spec`, and `implementation` classes so impossible combinations such as an implementation audit of `skill` or an instructions audit of `code` are rejected by schema validation.
- Audit terminal rollup is planned, but the public `finish` contract still speaks as caller-supplied terminal status. SPX should decide whether audit `finish` derives status without a caller value or validates a supplied value against the derived rollup, and specify the rejected mismatch behavior.
- Prior-run selection must distinguish gating runs over committed heads from advisory runs over live modified or untracked files. The run-set selector should expose run purpose directly rather than infer authority from scope payload prose.
- Finding severity vocabulary is not reconciled across the artifact-type audit skills. `audit-adr` emits the audit-run severities `blocking`/`debt`; `audit-pdr`, `audit-tests`, `audit-specs`, and `audit-eval-evidence` emit `REJECT`/`WARNING`/`INFO`. The governing authority conflicts: `/merging-standards` `<review_classification>` mandates `BLOCKING`/`DEBT` and forbids severity-rank labels, while its `<auditor_verdicts>` references a `REJECT` finding. SPX should define the single canonical finding-severity enum for audit-run verdicts, after which the four non-`blocking`/`debt` skills reconcile to it in one pass — a sub-task of the verification-run migration in `PLAN.md`, not independent work, because that migration rewrites the same skills.
