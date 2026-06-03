# Issues: Decisions Enabler

## 16-verification.enabler conformance for audit-adr / audit-pdr (deferred)

`audit-adr` and `audit-pdr` (skills + agents) landed at SCOPE-MIN per `spx/21-spec-tree.enabler/32-decisions.enabler/PLAN.md` — the established read-only verdict-producer shape shared by the other spec-tree audit agents. They do NOT yet conform to `spx/21-spec-tree.enabler/16-verification.enabler`:

- The wrapper agents use `tools: Read, Glob, Grep` and no `model:` field; `16-verification.enabler` requires `model: sonnet` and `tools: Bash, Read, Skill`.
- No `scripts/` CLI arbiter module encodes the verification policy (schema conformance) for the wrapper agent to invoke; the verdict schema is described in skill prose.
- No thread-store persistence of the machine-readable result + markdown surface.
- The audit skills' LLM-judgment scenarios carry forward-referenced `[test]` in `pdr-auditing.md` and `[eval]` in `adr-auditing.md`; per `16-verification.enabler` the `[test]` ones should be `[eval]`, and the eval suites themselves are unbuilt (both `21-adr-auditing.enabler` and `32-pdr-auditing.enabler` are in `spx/EXCLUDE`).

This conformance is an architecture migration that applies to the whole audit-skill family, not just these two, and is independent of the per-rule-evidence-type feature. Address it as its own change: build the `scripts/` arbiter, reshape the audit agents to `model: sonnet` + `Bash, Read, Skill`, wire thread-store persistence, and build the eval suites. Until then, audit-adr/audit-pdr run as read-only verdict producers in the established pre-conformance pattern.

## Evidence-type-tag migration for existing decision records (deferred)

`decisions.md` declares that every decision-record rule sits under `## Verification`, grouped by verification type into `### Testing`, `### Eval`, and `### Audit` — a `### Testing` rule carries a `/testing`-routed evidence type (`scenario`/`mapping`/`conformance`/`property`/`compliance`), an `### Eval` rule carries `[eval]`, and an `### Audit` rule carries `[audit]`. The marketplace's own existing ADRs and PDRs still carry bare `([review])` tags under a `## Compliance` section, so `/audit-adr` and `/audit-pdr` deterministically REJECT them at the tag-validity step (`invalid-mode-tag`) until each is migrated to the `## Verification` structure.

Records to migrate — move each `## Compliance` section to `## Verification`, place each rule under the subsection matching its verification type, and replace the bare `([review])` tag: a `### Testing` rule routes its claim shape through `/testing`; a rule governing a Spec Tree skill, agent, or decision goes under `### Audit` (`[audit]`) or `### Eval` (`[eval]`):

- `spx/13-plugin-and-runtime-conventions.adr.md`
- `spx/15-spec-coverage.adr.md`
- `spx/15-test-language.adr.md`
- `spx/15-audit-verdict-format.pdr.md`
- `spx/15-test-infrastructure.pdr.md`
- `spx/15-agent-pr-authority.pdr.md`
- `spx/21-spec-tree.enabler/17-auditing.adr.md`
- `spx/18-plugin-build.enabler/15-build-architecture.adr.md`
- `spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md`
- `spx/15-validation.enabler/32-skill-frontmatter.enabler/15-frontmatter-validation.adr.md`
- `spx/15-validation.enabler/21-subprocess-execution.adr.md`
- `spx/32-distribution.enabler/21-bump.enabler/15-bump-shape.adr.md`
- `spx/13-infrastructure.enabler/32-installation.enabler/21-codex-cache-preservation.adr.md`
- `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/21-script-decomposition.adr.md`

This is a repo-wide reconciliation triggered by the new declaration — too large to belong in the feature PR. Migrate the records as its own change; the declaration leads and the records follow. The PDR files in this list (`15-audit-verdict-format.pdr.md`, `15-test-infrastructure.pdr.md`, `15-agent-pr-authority.pdr.md`, `21-compact-continuity.pdr.md`) also carry `## Product invariants` headings; rename each to `## Product properties` during the same migration to match the PDR template and `/audit-pdr`.

## ADR-authoring skills still teach the pre-`## Verification` layout (deferred)

`/architecting-python`, `/architecting-typescript`, and their `standardizing-*-architecture` references teach the pre-`## Verification` ADR layout — `Purpose` / `Context` / `Decision` / `Compliance` with bare `([review])` tags. An ADR authored through them is then deterministically REJECTED by `/audit-adr` at the tag-validity step, the same gap the record migration above closes for existing files.

Update the language architecting and `standardizing-*-architecture` skills to teach the `## Verification` structure (`### Testing` / `### Eval` / `### Audit` with per-rule evidence-type tags) as part of the same migration. These skill edits are plugin-distribution changes carrying their own version bump, so they travel with the record migration rather than a feature PR.

## Evidence-type terminology not yet propagated to language plugins and verdict identifiers (deferred)

The terminology pass realigned the spec-tree plugin's decision-record, template, audit, and testing-methodology wording from `claim-shape mode` / `evidence mode` to the foundation term **evidence type** (the five values `scenario`/`mapping`/`conformance`/`property`/`compliance`), keeping **mechanism** for the `[test]`/`[eval]`/`[audit]` lanes and **verdict mode** for the deterministic/agentic axis. Two surfaces still carry the old wording and were left for follow-up PRs:

- **Language test-standard skills** — `standardizing-python-tests`, `standardizing-typescript-tests`, `standardizing-rust-tests`, `testing-rust`, and the `typescript-simplifier` agent still say `evidence mode` for the `<evidence>` filename segment. Each rename is a plugin-distribution change carrying that plugin's own version bump, so it travels as its own PR rather than widening the spec-tree-only first PR.
- **Audit verdict-contract identifiers** — the audit-adr/audit-pdr verdict row name `mode-validity`, the finding category `invalid-mode-tag`, and the `evals/mode-validity/` eval directory referenced by `adr-auditing.md` still use the old word. These are machine identifiers tied to the unbuilt audit eval suites; rename them to tag-based names (`tag-validity`, `invalid-tag`, `evals/tag-validity/`) when the `16-verification.enabler` conformance migration above builds those suites, so the rename and the suite land together.
