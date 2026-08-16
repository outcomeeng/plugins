# Issues: Decisions Enabler

## Artifact-type auditors do not yet persist verification runs

`implementation-auditor` is the first audit wrapper moving to `spx verification run`. The artifact-type wrappers — `adr-auditor`, `pdr-auditor`, `spec-auditor`, `test-evidence-auditor`, and `eval-evidence-auditor` — still return their skill verdict directly and do not yet record scope, findings, terminal state, or prior-run context through the shared verification-run lifecycle.

Required handling:

- Keep each wrapper thin and runtime-neutral while implementation audit proves the single-run contract.
- Move artifact-type auditors onto `spx verification run` in the later slice recorded by `spx/21-spec-tree.enabler/68-audit.enabler/PLAN.md`.
- Preserve each artifact audit's existing verdict schema until the SPX payload contract for that audit kind is specified.

## Audit-skill family carries codebase-wide standards deviations (FOLLOW-UP)

These patterns span the **entire** audit-skill family — every `audit-*` SKILL.md plus the `instructions` audit skills (`audit-skill`, `audit-subagent`) — and the shared verification-run payload vocabulary. Fixing any one skill without the family-wide pass would diverge it from its siblings, so the family-wide change is tracked here. Per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` property 7 a single-site fix stands only when a sweep shows no parallel instance:

- **`<quick_start>` on validator skills.** `skill-standards` says omit `<quick_start>` for validator/gate/reference skills, yet every language implementation-code audit skill (`audit-python-code`, `audit-typescript-code`, `audit-rust-code`) carries one. Either the convention is an accepted exception for the language code auditors or they need a sweep; decide once and apply uniformly.
- **Audit verdict vocabulary.** Every audit skill states a human conclusion as `APPROVED`/`REJECT` in prose while the SPX verification-run payload contract owns the machine verdict and terminal projection. The dual vocabulary must either be reconciled at the verification-run payload boundary or applied consistently across every audit skill, not as a per-skill edit. This is the same reconciliation as the finding-severity enum in `spx/21-spec-tree.enabler/68-audit.enabler/ISSUES.md`, and lands with the verification-run migration that rewrites the same skills.
- **Auditor-skeleton shape.** The language auditors (`audit-{python,typescript,rust}-{code|tests|architecture}`) do not yet carry the auditor-skeleton shape: verdict-shaped `<objective>` naming its finding categories, soundness `<success_criteria>`, a read-only/verdict-only `<constraints>` block, and the canonical section names (`<audit_workflow>`, `<verdict_format>`, `<failure_modes>`, no `<quick_start>`). Sequenced after reconciling with the audit verification-run migration in `spx/21-spec-tree.enabler/68-audit.enabler/PLAN.md`.

## ADR `### Audit` rules mirror implementing-spec `[test]`/`[eval]` lanes (deferred)

The `/audit-adr` pass on `21-script-decomposition.adr.md` surfaced a cross-spec lane divergence (an observation, not a tag-validity finding — the audit-adr skill validates the tag against its subsection, not against the implementing spec's lane). One rule under `### Audit` in that ADR mirrors an assertion whose implementing lane in `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md` is not `[audit]`:

- ADR "reviewer emits no `decision`/verdict" (`[audit]`) mirrors spec line tagged `[test](tests/test_review_result.scenario.l1.py)`.

The ADR's other `### Audit` rules have no corresponding assertion under a non-`[audit]` lane in `reviewing-changes.md`, so they are not part of this divergence. Reconcile whether the mirrored ADR rule belongs under `### Testing` (mirroring the implementing spec's lane) rather than `### Audit`. Audit gate: `/audit-adr` on the record clean after any move.

## Verdict-row keys in `audit-{lang}-architecture` skills lack conformance evidence (FOLLOW-UP)

The `audit-{lang}-architecture` skills declare their verdict-row keys (`section-structure`, `testability-in-verification`, `atemporal-voice`, …) as prose in the JSON output schema, with no conformance test or eval pinning the key names — a rename or revert (such as a `testability-in-compliance` → `testability-in-verification` rename) would go undetected. This is the same class as the `[eval]`-migration candidates tracked in `spx/43-typescript.enabler/25-typescript-standards.enabler/ISSUES.md`; fold verdict-row-key assertions into that language-auditor eval work rather than testing one renamed key in isolation.

## Assertion-type terminology not yet propagated to every language surface (deferred)

The terminology pass aligns decision-record, template, audit, and test-methodology wording to the foundation term **assertion type** (the five values `scenario`/`mapping`/`conformance`/`property`/`compliance`), keeps **verification type** for test/evaluate/audit, and keeps **verdict mode** for the deterministic/agentic axis. The decision-audit skills, specs, eval prompts, and verdict identifier `assertion-type-mismatch` conform. One surface still carries older wording and remains a follow-up:

- **Language test-standard skills** — `python-test-standards`, `typescript-test-standards`, `rust-test-standards`, `test-rust`, `test-typescript`, the `typescript-simplifier` agent, and `architect-python/references/testability-patterns.md` (the "Evidence mode" table header) still say `evidence mode` for the `<evidence>` filename segment. Each rename is a plugin-distribution change carrying that plugin's own version bump, so it travels as its own PR rather than widening the spec-tree-only first PR.

The PDR audit verdict-contract identifiers `tag-validity`, `invalid-tag`, and `assertion-type-mismatch` are aligned with the shipped eval suites.
