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

## Re-audit migrated records for universal-claim evidence-type fit (deferred)

The migration above predates the evidence-type-fit check that `/audit-adr` and `/audit-pdr` now enforce (a `### Testing` rule whose claim is universal — ALWAYS/NEVER/"for all"/"for every"/"no input" — is never `scenario`; mismatch is an `evidence-type-mismatch` REJECT). Two migrated records carry universal claims under `### Testing` tagged `([scenario])` that the new rule rejects:

- `spx/21-spec-tree.enabler/17-auditing.adr.md` — 3 ALWAYS rules under `### Testing` tagged `[scenario]`.
- `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/21-script-decomposition.adr.md` — 6 ALWAYS rules under `### Testing` tagged `[scenario]`.

These predate the new rule, so they are not regressions of this branch and sit outside its diff. Run a re-audit pass: route each universal claim through `/testing` (most are `compliance` — a structural rule every conformant implementation must always satisfy — or `property`) and retag, then confirm `/audit-adr` returns APPROVED. Audit gate: `/audit-adr` on both records clean.

## ADR-authoring skills still teach the pre-`## Verification` layout (Rust outstanding)

The TypeScript and Python ADR producer **and** validator skills now teach the decision-first canonical layout — title + decision stated directly, Rationale, Invariants, `## Verification` (`### Audit` / `### Eval` / `### Testing`) with per-rule evidence-type tags (`([audit])` for the DI/mocking architecture rules):

- `/architecting-typescript` (+ `references/adr-patterns.md`), `/standardizing-typescript-architecture`, `/auditing-typescript-architecture` (+ `references/example-audit.md`).
- `/architecting-python` (+ `references/testability-patterns.md`, `references/test-infrastructure-patterns.md`), `/standardizing-python-architecture`, `/auditing-python-architecture` (+ `references/example-audit.md`).

The original scope named only the producers; the validators were migrated in lockstep because `/auditing-*-architecture` enforces an ADR against the standardizing skill's section list and `## Compliance` shape — leaving them on the legacy layout would make the auditor deterministically REJECT correctly-authored ADRs.

**Rust outstanding**: `/standardizing-rust-architecture` and `/auditing-rust-architecture` (plus the Rust `references/example-audit.md`) still carry the legacy `<testability_in_compliance>` tag, the `testability-in-compliance` verdict row, and the `## Compliance` / `([review])` structure. Migrate them the same way — decision-first + `## Verification` / `### Audit` / `([audit])` — when the Rust architecture surface is next touched. Audit gate: `just check-skills` after the sweep; re-grep `src/plugins/rust/` for `([review])` and `testability_in_compliance`.

**Verdict-row-key coverage gap**: the `auditing-{lang}-architecture` skills declare their verdict-row keys (`section-structure`, `testability-in-verification`, `atemporal-voice`, …) as prose in the JSON output schema, with no conformance test or eval pinning the key names — a rename or revert (such as the `testability-in-compliance` → `testability-in-verification` rename above) would go undetected. This is the same class as the `[eval]`-migration candidates tracked in `spx/43-typescript.enabler/25-typescript-standards.enabler/ISSUES.md`; fold verdict-row-key assertions into that language-auditor eval work rather than testing one renamed key in isolation.

## Evidence-type terminology not yet propagated to language plugins and verdict identifiers (deferred)

The terminology pass realigned the spec-tree plugin's decision-record, template, audit, and testing-methodology wording from `claim-shape mode` / `evidence mode` to the foundation term **evidence type** (the five values `scenario`/`mapping`/`conformance`/`property`/`compliance`), keeping **mechanism** for the `[test]`/`[eval]`/`[audit]` lanes and **verdict mode** for the deterministic/agentic axis. Two surfaces still carry the old wording and were left for follow-up PRs:

- **Language test-standard skills** — `standardizing-python-tests`, `standardizing-typescript-tests`, `standardizing-rust-tests`, `testing-rust`, and the `typescript-simplifier` agent still say `evidence mode` for the `<evidence>` filename segment. Each rename is a plugin-distribution change carrying that plugin's own version bump, so it travels as its own PR rather than widening the spec-tree-only first PR.
- **Audit verdict-contract identifiers** — the audit-adr/audit-pdr verdict row name `mode-validity`, the finding category `invalid-mode-tag`, and the `evals/mode-validity/` eval directory referenced by `adr-auditing.md` still use the old word. These are machine identifiers tied to the unbuilt audit eval suites; rename them to tag-based names (`tag-validity`, `invalid-tag`, `evals/tag-validity/`) when the `16-verification.enabler` conformance migration above builds those suites, so the rename and the suite land together.
