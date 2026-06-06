# Issues: Decisions Enabler

## 16-verification.enabler conformance for audit-adr / audit-pdr (deferred)

`audit-adr` and `audit-pdr` (skills + agents) landed at SCOPE-MIN per `spx/21-spec-tree.enabler/32-decisions.enabler/PLAN.md` — the established read-only verdict-producer shape shared by the other spec-tree audit agents. They do NOT yet conform to `spx/21-spec-tree.enabler/16-verification.enabler`:

- The wrapper agents use `tools: Read, Glob, Grep` and no `model:` field; `16-verification.enabler` requires `model: sonnet` and `tools: Bash, Read, Skill`.
- No `scripts/` CLI arbiter module encodes the verification policy (schema conformance) for the wrapper agent to invoke; the verdict schema is described in skill prose.
- No thread-store persistence of the machine-readable result + markdown surface.
- The audit skills' LLM-judgment scenarios carry forward-referenced `[test]` in `pdr-auditing.md` and `[eval]` in `adr-auditing.md`; per `16-verification.enabler` the `[test]` ones should be `[eval]`, and the eval suites themselves are unbuilt (both `21-adr-auditing.enabler` and `32-pdr-auditing.enabler` are in `spx/EXCLUDE`). The specific unbuilt fixtures these scenarios reference — including the `evidence-type-mismatch` scenarios — are `evals/mode-validity/eval.toml` under `21-adr-auditing.enabler` and `tests/test_pdr_auditing.scenario.l1.py` under `32-pdr-auditing.enabler`; build them as part of this migration (the `evals/mode-validity/` directory and `invalid-mode-tag`/`invalid-tag` identifier rename are governed by the terminology-propagation entry below).

This conformance is an architecture migration that applies to the whole audit-skill family, not just these two, and is independent of the per-rule-evidence-type feature. Address it as its own change: build the `scripts/` arbiter, reshape the audit agents to `model: sonnet` + `Bash, Read, Skill`, wire thread-store persistence, and build the eval suites. Until then, audit-adr/audit-pdr run as read-only verdict producers in the established pre-conformance pattern.

## Evidence-type-tag migration for existing decision records (RESOLVED)

Thirteen records were migrated to the `## Verification` structure (`### Testing`/`### Eval`/`### Audit` with per-rule evidence-type or `[audit]` tags) and the lean decision template (decision stated in the opening; no `## Purpose`/`## Context`/`## Trade-offs accepted`/`### Recognized by`), under atemporal voice. `spx/15-test-infrastructure.pdr.md` — the fourteenth listed record — was already migrated to `## Verification`/`### Audit` (with Go-language support) on `origin/main` before this branch, so it is not part of this branch's diff. Functional code behavior routed to `### Testing` with the claim-shape evidence type (aligned to each implementing spec); architecture, dependency-injection, and skill/methodology/design rules routed to `### Audit`; `[eval]` deferred to the audit-eval-suite migration. The PDRs' `## Product invariants` headings were renamed to `## Product properties` (all items kept).

**Resolution evidence**: `spx validation markdown` passes; the two exemplars (`spx/32-distribution.enabler/21-bump.enabler/15-bump-shape.adr.md`, `spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md`) audited APPROVED via `/audit-adr` and `/audit-pdr`; the remaining 12 confirmed clean for temporal voice, bare `([review])`/`([test])` tags, double-tagged or untagged rule lines, and legacy section headings.

## Re-audit migrated records for universal-claim evidence-type fit (RESOLVED)

The migration predated the evidence-type-fit check that `/audit-adr` and `/audit-pdr` now enforce (a `### Testing` rule whose claim ranges over an open or large case-space is never `scenario`; a single concrete structural or behavioral fact may be `scenario`; mismatch is an `evidence-type-mismatch` REJECT). The re-audit pass ran `/audit-adr` on the two candidate records:

- `spx/21-spec-tree.enabler/17-auditing.adr.md` — two genuine mismatches, retagged: the `save_state` / `RunLock` rule asserts lock release on "every context-manager exit path" (ranges over the exit-path set) → `[scenario]`→`[compliance]` (an ALWAYS safety rule exercised against violating cases — atomic-write crash, exception exit); the `compute_verdict_diff` rule asserts an identity-keying invariant ("excluding `id` and `severity`" must hold across all regenerated/re-severitied findings, an open domain) → `[scenario]`→`[property]`. The remaining `### Testing` rule — a regression reopening its original finding ID after one resolved-then-reopened cycle — is a single concrete interaction and stays valid `scenario`.
- `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/21-script-decomposition.adr.md` — APPROVED as-is. Its six `[scenario]` rules each assert a single concrete structural or behavioral fact (one module's declared symbols, one schema's absent field, one script's behavior, the frozen-dataclass fact), not a ranged universal, and its eight `[compliance]` rules are correct. The earlier count of "9 mis-tagged across 2 records" over-applied the rule by reading every `ALWAYS:` prefix as a quantifier; the audit caveat (a single concrete fact may be `scenario`; do not relitigate a choice the router leaves open) corrects it to one real fix.

**Resolution evidence**: `/audit-adr` returns APPROVED on both records after the single `17-auditing.adr.md` retag.

## ADR `### Audit` rules mirror implementing-spec `[test]`/`[eval]` lanes (deferred)

The `/audit-adr` pass on `21-script-decomposition.adr.md` surfaced a cross-spec lane divergence (an observation, not a tag-validity finding — the audit-adr skill validates the tag against its subsection, not against the implementing spec's lane). Two of the three rules under `### Audit` in that ADR mirror assertions whose implementing lanes in `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md` are not `[audit]`:

- ADR "reviewer emits no `decision`/verdict" (`[audit]`) mirrors spec line tagged `[test](tests/test_review_result.scenario.l1.py)`.
- ADR "wrapper agent never hand-validates emitted JSON" (`[audit]`) mirrors spec line tagged `[eval](evals/wrapper-protocol/eval.toml)`.

The third `### Audit` rule (no intermediate file when stdin/stdout suffices) has no corresponding assertion under any non-`[audit]` lane in `reviewing-changes.md`, so it is not part of this divergence. Reconcile whether the two mirrored ADR rules belong under `### Testing` / `### Eval` (mirroring the implementing spec's lanes) rather than `### Audit`. Audit gate: `/audit-adr` on the record clean after any move.

## ADR-authoring skills still teach the pre-`## Verification` layout (Rust outstanding)

The TypeScript and Python ADR producer **and** validator skills now teach the decision-first canonical layout — title + decision stated directly, Rationale, Invariants, `## Verification` (`### Audit` / `### Eval` / `### Testing`) with per-rule evidence-type tags (`([audit])` for the DI/mocking architecture rules):

- `/architecting-typescript` (+ `references/adr-patterns.md`), `/standardizing-typescript-architecture`, `/auditing-typescript-architecture` (+ `references/example-audit.md`).
- `/architecting-python` (+ `references/testability-patterns.md`, `references/test-infrastructure-patterns.md`), `/standardizing-python-architecture`, `/auditing-python-architecture` (+ `references/example-audit.md`).

The original scope named only the producers; the validators were migrated in lockstep because `/auditing-*-architecture` enforces an ADR against the standardizing skill's section list and `## Compliance` shape — leaving them on the legacy layout would make the auditor deterministically REJECT correctly-authored ADRs.

**Rust outstanding**: all three Rust architecture skills are still on the legacy layout — `/architecting-rust` (+ `references/adr-patterns.md`, which prescribes `Purpose, Context, … Compliance` and emits `## Compliance` / `### MUST` / `### NEVER` / `([review])` example ADRs), `/standardizing-rust-architecture` (the `<testability_in_compliance>` tag and `## Compliance` shape), and `/auditing-rust-architecture` (the `testability-in-compliance` verdict row, plus `references/example-audit.md`). Migrate all three the same way — decision-first + `## Verification` / `### Audit` / `([audit])` — when the Rust architecture surface is next touched. Audit gate: `just check-skills` after the sweep; re-grep `src/plugins/rust/` for `([review])` and `testability_in_compliance`.

**Verdict-row-key coverage gap**: the `auditing-{lang}-architecture` skills declare their verdict-row keys (`section-structure`, `testability-in-verification`, `atemporal-voice`, …) as prose in the JSON output schema, with no conformance test or eval pinning the key names — a rename or revert (such as the `testability-in-compliance` → `testability-in-verification` rename above) would go undetected. This is the same class as the `[eval]`-migration candidates tracked in `spx/43-typescript.enabler/25-typescript-standards.enabler/ISSUES.md`; fold verdict-row-key assertions into that language-auditor eval work rather than testing one renamed key in isolation.

## Evidence-type terminology not yet propagated to language plugins and verdict identifiers (deferred)

The terminology pass realigned the spec-tree plugin's decision-record, template, audit, and testing-methodology wording from `claim-shape mode` / `evidence mode` to the foundation term **evidence type** (the five values `scenario`/`mapping`/`conformance`/`property`/`compliance`), keeping **mechanism** for the `[test]`/`[eval]`/`[audit]` lanes and **verdict mode** for the deterministic/agentic axis. Two surfaces still carry the old wording and were left for follow-up PRs:

- **Language test-standard skills** — `standardizing-python-tests`, `standardizing-typescript-tests`, `standardizing-rust-tests`, `testing-rust`, `testing-typescript`, the `typescript-simplifier` agent, and `architecting-python/references/testability-patterns.md` (the "Evidence mode" table header) still say `evidence mode` for the `<evidence>` filename segment. Each rename is a plugin-distribution change carrying that plugin's own version bump, so it travels as its own PR rather than widening the spec-tree-only first PR.
- **Audit verdict-contract identifiers** — the audit-adr/audit-pdr verdict row name `mode-validity`, the finding category `invalid-mode-tag`, and the `evals/mode-validity/` eval directory referenced by `adr-auditing.md` still use the old word. These are machine identifiers tied to the unbuilt audit eval suites; rename them to tag-based names (`tag-validity`, `invalid-tag`, `evals/tag-validity/`) when the `16-verification.enabler` conformance migration above builds those suites, so the rename and the suite land together.
