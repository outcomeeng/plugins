# Issues: Decisions Enabler

## 16-verification.enabler conformance for adr-auditor / pdr-auditor / test-evidence-auditor (deferred — NEXT change after the collapse)

The auditor collapse (PR `feat/auditor-collapse`: composition mechanism + removal of the 10 language auditor agents + doc reconciliation) shipped without this conformance, exactly as scoped here: it is an audit-skill-family migration independent of the collapse. `adr-auditor` and `test-evidence-auditor` gained `Skill` (for composition) but otherwise remain at the established read-only verdict-producer shape; `pdr-auditor` is unchanged. They do NOT yet conform to `spx/21-spec-tree.enabler/16-verification.enabler`:

- The wrapper agents now declare `model: sonnet` but still use `tools: Read, Glob, Grep` (`adr-auditor`, `pdr-auditor`) or `tools: Read, Bash, Glob, Grep` (`test-evidence-auditor`); `16-verification.enabler` requires `tools: Bash, Read, Skill`.
- No `scripts/` CLI arbiter module encodes the verification policy (schema conformance) for the wrapper agent to invoke; the verdict schema is described in skill prose.
- No thread-store persistence of the machine-readable result + markdown surface.
- The audit skills' LLM-judgment scenarios carry forward-referenced `[test]` in `pdr-auditing.md`; per `16-verification.enabler` those should be `[eval]`, and the PDR-auditing suites remain unbuilt (`32-pdr-auditing.enabler` remains in `spx/EXCLUDE`). The specific unbuilt fixture still referenced is `tests/test_pdr_auditing.scenario.l1.py` under `32-pdr-auditing.enabler`; build it as part of this migration. ADR-auditing now declares eval suites under `evals/structure/`, `evals/voice/`, and `evals/tag-validity/`, with `invalid-tag` as the bare-mechanism finding category; external execution for the new tag-validity suite is separate validation evidence, not a remaining missing-link issue.

This conformance is an architecture migration that applies to the whole audit-skill family, not just these three, and is independent of the per-rule-evidence-type feature. Address it as its own change: build the `scripts/` arbiter, give the audit agents `tools: Bash, Read, Skill`, wire thread-store persistence, and build the eval suites. Until then, adr-auditor/pdr-auditor/test-evidence-auditor run as read-only verdict producers in the established pre-conformance pattern.

## Audit-skill family carries two codebase-wide standards deviations (FOLLOW-UP, surfaced by skill-auditor during the collapse)

The `develop:skill-auditor` pass over the collapse changeset surfaced two pre-existing patterns that span the **entire** audit-skill family — every `audit-*` SKILL.md plus the `develop` audit skills (`audit-skills`, `audit-commands`, `audit-subagents`) — and the shared `verdict.py` schema. Both predate the collapse and are out of scope for it; fixing either in one skill would diverge it from its siblings, so they are tracked as their own family-wide change:

- **`<quick_start>` on validator skills.** `skill-standards` says omit `<quick_start>` for validator/gate/reference skills, yet every language code-audit skill (`audit-python`, `audit-typescript`, `audit-rust`) and the `develop` audit skills carry one — including `audit-skills` itself. Either the convention is an accepted exception for these skills or the family needs a sweep; decide once and apply uniformly.
- **Audit verdict vocabulary.** Every audit skill states a human conclusion as `APPROVED`/`REJECT` in prose while the JSON schema (canonical `verdict.py`) uses `PASS`/`FAIL`/`UNKNOWN` for `overall` and rows, and `REJECT` doubles as a finding severity. The dual vocabulary is consistent across the family; if it is to be reconciled, it is a `verdict.py`-plus-every-audit-skill change, not a per-skill edit.

## ADR `### Audit` rules mirror implementing-spec `[test]`/`[eval]` lanes (deferred)

The `/audit-adr` pass on `21-script-decomposition.adr.md` surfaced a cross-spec lane divergence (an observation, not a tag-validity finding — the audit-adr skill validates the tag against its subsection, not against the implementing spec's lane). Two of the three rules under `### Audit` in that ADR mirror assertions whose implementing lanes in `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/review-changes.md` are not `[audit]`:

- ADR "reviewer emits no `decision`/verdict" (`[audit]`) mirrors spec line tagged `[test](tests/test_review_result.scenario.l1.py)`.
- ADR "wrapper agent never hand-validates emitted JSON" (`[audit]`) mirrors spec line tagged `[eval](evals/wrapper-protocol/eval.toml)`.

The third `### Audit` rule (no intermediate file when stdin/stdout suffices) has no corresponding assertion under any non-`[audit]` lane in `reviewing-changes.md`, so it is not part of this divergence. Reconcile whether the two mirrored ADR rules belong under `### Testing` / `### Eval` (mirroring the implementing spec's lanes) rather than `### Audit`. Audit gate: `/audit-adr` on the record clean after any move.

## Verdict-row keys in `audit-{lang}-architecture` skills lack conformance evidence (FOLLOW-UP)

The `audit-{lang}-architecture` skills declare their verdict-row keys (`section-structure`, `testability-in-verification`, `atemporal-voice`, …) as prose in the JSON output schema, with no conformance test or eval pinning the key names — a rename or revert (such as a `testability-in-compliance` → `testability-in-verification` rename) would go undetected. This is the same class as the `[eval]`-migration candidates tracked in `spx/43-typescript.enabler/25-typescript-standards.enabler/ISSUES.md`; fold verdict-row-key assertions into that language-auditor eval work rather than testing one renamed key in isolation.

## Evidence-type terminology not yet propagated to language plugins and verdict identifiers (deferred)

The terminology pass realigned the spec-tree plugin's decision-record, template, audit, and test-methodology wording from `claim-shape mode` / `evidence mode` to the foundation term **evidence type** (the five values `scenario`/`mapping`/`conformance`/`property`/`compliance`), keeping **mechanism** for the `[test]`/`[eval]`/`[audit]` lanes and **verdict mode** for the deterministic/agentic axis. Two surfaces still carry the old wording and were left for follow-up PRs:

- **Language test-standard skills** — `python-test-standards`, `typescript-test-standards`, `rust-test-standards`, `test-rust`, `test-typescript`, the `typescript-simplifier` agent, and `architect-python/references/testability-patterns.md` (the "Evidence mode" table header) still say `evidence mode` for the `<evidence>` filename segment. Each rename is a plugin-distribution change carrying that plugin's own version bump, so it travels as its own PR rather than widening the spec-tree-only first PR.
- **PDR audit verdict-contract identifiers** — the audit-pdr verdict row name `mode-validity` and finding category `invalid-mode-tag` still use the old word. These machine identifiers are tied to the unbuilt PDR audit eval suites; rename them to tag-based names (`tag-validity`, `invalid-tag`) when the `16-verification.enabler` conformance migration above builds those suites, so the rename and the suite land together.
