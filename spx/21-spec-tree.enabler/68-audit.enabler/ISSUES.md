# Issues - Audit

Known follow-ups for the audit node. Coordination note; not spec truth.

## Implementation audit has incomplete mixed-changeset coverage

During PR 420 local verification, the `auditor` agent rejected audit setup when
the full changeset scope included `.github/workflows/spec-tree-evals.yml`:

```text
missing required skill: audit-yaml-kind
```

Checked facts:

- `actionlint .github/workflows/spec-tree-evals.yml` passed and covered workflow
  syntax.
- The `auditor` agent approved the remaining supported Python, test
  infrastructure, spec-test, and coordination-note scope after the workflow YAML
  was excluded.
- The changeset review gate still owns full-diff review, including workflow YAML,
  because the generic implementation auditor cannot currently judge that surface.

Revisit condition: when the audit-family surface work in `PLAN.md` resumes,
decide whether workflow YAML receives a dedicated YAML audit skill or routes to a
workflow-specific audit surface, then make `implementation-auditor` report that
coverage without requiring callers to split YAML out of an otherwise valid
changeset.

Run `2026-07-14_05-33-54-020-a9a65f44705b` exposed the broader terminal
behavior after the typed `implementation-auditor` became available. Its Python
code, test, and architecture units were audited with zero findings, while one
required `unsupported` unit collected the remaining workflow, generated,
fixture, eval, spec, and skill files. SPX sealed the run as `rejected` with an
authoritative finding count of zero. A gating implementation audit therefore
depends on how orchestration classifies supported language and artifact
partitions and distinguishes files outside implementation-audit ownership from
missing required implementation coverage.

Run `2026-07-14_06-34-22-620-431040668f95` later audited the same branch's
Python code, test, and architecture partitions, recorded no unsupported unit,
and sealed as `approved` with zero findings. The different coverage projections
show that mixed-changeset partitioning is not reproducible across verifier runs.
That run's terminal projection reported `sealed: true`, while the event
projection returned in the same verifier result reported `sealed: false` and
omitted the terminal event. The verifier output contract needs one
post-completion projection whose seal and event prefix agree.

## SPX audit verification contract follow-ups

The plugin implementation-auditor model records implementation-audit coverage, findings, terminal state, and projections through `spx verification run`. The remaining issues live in the SPX verification-run contract rather than in plugin-side verdict scripts.

Open gaps:

- Audit scope payloads require stable producer identity and producer provenance for every unit, but `missing-skill`, `unsupported`, and `coverage-gap` units may have no executed leaf skill and sometimes no skill or plugin version. SPX should distinguish the run driver that recorded the unit from the expected producer that would have covered it, and make provenance optional when the expected producer is absent.
- Audit unit identity and subject normalization are not specified. SPX should define deterministic `unit_id` derivation, parent/child identity stability, and normalized subject shape so findings, coverage gaps, and prior-run context converge across repeated runs.
- Audit class/kind validation needs a compatibility matrix for `instructions`, `spec`, and `implementation` classes so impossible combinations such as an implementation audit of `skill` or an instructions audit of `code` are rejected by schema validation.
- Audit terminal rollup is planned, but the public `finish` contract still speaks as caller-supplied terminal status. SPX should decide whether audit `finish` derives status without a caller value or validates a supplied value against the derived rollup, and specify the rejected mismatch behavior.
- Prior-run selection must distinguish gating runs over committed heads from advisory runs over live modified or untracked files. The run-set selector should expose run purpose directly rather than infer authority from scope payload prose.
- Finding severity vocabulary is not reconciled across the artifact-type audit skills. `audit-adr` emits the audit-run severities `blocking`/`debt`; `audit-pdr`, `audit-tests`, `audit-specs`, and `audit-eval-evidence` emit `REJECT`/`WARNING`/`INFO`. The governing authority conflicts: `/merging-standards` `<review_classification>` mandates `BLOCKING`/`DEBT` and forbids severity-rank labels, while its `<auditor_verdicts>` references a `REJECT` finding. SPX should define the single canonical finding-severity enum for audit-run verdicts, after which the four non-`blocking`/`debt` skills reconcile to it in one pass. Deferred here to avoid locking a shape before the contract exists.
