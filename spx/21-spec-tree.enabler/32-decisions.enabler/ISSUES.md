# Issues: Decisions Enabler

## 16-verification.enabler conformance for adr-auditor / pdr-auditor (deferred)

`audit-adr` and `audit-pdr` (skills + agents) landed at SCOPE-MIN per `spx/21-spec-tree.enabler/32-decisions.enabler/PLAN.md` — the established read-only verdict-producer shape shared by the other spec-tree audit agents. They do NOT yet conform to `spx/21-spec-tree.enabler/16-verification.enabler`:

- The wrapper agents use `tools: Read, Glob, Grep` and no `model:` field; `16-verification.enabler` requires `model: sonnet` and `tools: Bash, Read, Skill`.
- No `scripts/` CLI arbiter module encodes the verification policy (schema conformance) for the wrapper agent to invoke; the verdict schema is described in skill prose.
- No thread-store persistence of the machine-readable result + markdown surface.
- The audit skills' LLM-judgment scenarios carry forward-referenced `[test]` in `pdr-auditing.md` and `[eval]` in `adr-auditing.md`; per `16-verification.enabler` the `[test]` ones should be `[eval]`, and the eval suites themselves are unbuilt (both `21-adr-auditing.enabler` and `32-pdr-auditing.enabler` are in `spx/EXCLUDE`). The specific unbuilt fixtures these scenarios reference — including the `evidence-type-mismatch` scenarios — are `evals/mode-validity/eval.toml` under `21-adr-auditing.enabler` and `tests/test_pdr_auditing.scenario.l1.py` under `32-pdr-auditing.enabler`; build them as part of this migration (the `evals/mode-validity/` directory and `invalid-mode-tag`/`invalid-tag` identifier rename are governed by the terminology-propagation entry below).

This conformance is an architecture migration that applies to the whole audit-skill family, not just these two, and is independent of the per-rule-evidence-type feature. Address it as its own change: build the `scripts/` arbiter, reshape the audit agents to `model: sonnet` + `Bash, Read, Skill`, wire thread-store persistence, and build the eval suites. Until then, adr-auditor/pdr-auditor run as read-only verdict producers in the established pre-conformance pattern.

## ADR `### Audit` rules mirror implementing-spec `[test]`/`[eval]` lanes (deferred)

The `/audit-adr` pass on `21-script-decomposition.adr.md` surfaced a cross-spec lane divergence (an observation, not a tag-validity finding — the audit-adr skill validates the tag against its subsection, not against the implementing spec's lane). Two of the three rules under `### Audit` in that ADR mirror assertions whose implementing lanes in `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md` are not `[audit]`:

- ADR "reviewer emits no `decision`/verdict" (`[audit]`) mirrors spec line tagged `[test](tests/test_review_result.scenario.l1.py)`.
- ADR "wrapper agent never hand-validates emitted JSON" (`[audit]`) mirrors spec line tagged `[eval](evals/wrapper-protocol/eval.toml)`.

The third `### Audit` rule (no intermediate file when stdin/stdout suffices) has no corresponding assertion under any non-`[audit]` lane in `reviewing-changes.md`, so it is not part of this divergence. Reconcile whether the two mirrored ADR rules belong under `### Testing` / `### Eval` (mirroring the implementing spec's lanes) rather than `### Audit`. Audit gate: `/adr-auditor` on the record clean after any move.

## Verdict-row keys in `auditing-{lang}-architecture` skills lack conformance evidence (FOLLOW-UP)

The `auditing-{lang}-architecture` skills declare their verdict-row keys (`section-structure`, `testability-in-verification`, `atemporal-voice`, …) as prose in the JSON output schema, with no conformance test or eval pinning the key names — a rename or revert (such as a `testability-in-compliance` → `testability-in-verification` rename) would go undetected. This is the same class as the `[eval]`-migration candidates tracked in `spx/43-typescript.enabler/25-typescript-standards.enabler/ISSUES.md`; fold verdict-row-key assertions into that language-auditor eval work rather than testing one renamed key in isolation.

## Evidence-type terminology not yet propagated to language plugins and verdict identifiers (deferred)

The terminology pass realigned the spec-tree plugin's decision-record, template, audit, and testing-methodology wording from `claim-shape mode` / `evidence mode` to the foundation term **evidence type** (the five values `scenario`/`mapping`/`conformance`/`property`/`compliance`), keeping **mechanism** for the `[test]`/`[eval]`/`[audit]` lanes and **verdict mode** for the deterministic/agentic axis. Two surfaces still carry the old wording and were left for follow-up PRs:

- **Language test-standard skills** — `standardizing-python-tests`, `standardizing-typescript-tests`, `standardizing-rust-tests`, `testing-rust`, `testing-typescript`, the `typescript-simplifier` agent, and `architecting-python/references/testability-patterns.md` (the "Evidence mode" table header) still say `evidence mode` for the `<evidence>` filename segment. Each rename is a plugin-distribution change carrying that plugin's own version bump, so it travels as its own PR rather than widening the spec-tree-only first PR.
- **Audit verdict-contract identifiers** — the audit-adr/audit-pdr verdict row name `mode-validity`, the finding category `invalid-mode-tag`, and the `evals/mode-validity/` eval directory referenced by `adr-auditing.md` still use the old word. These are machine identifiers tied to the unbuilt audit eval suites; rename them to tag-based names (`tag-validity`, `invalid-tag`, `evals/tag-validity/`) when the `16-verification.enabler` conformance migration above builds those suites, so the rename and the suite land together.
