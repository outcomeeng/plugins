# Issues: Decisions Enabler

## 16-verification.enabler conformance for audit-adr / audit-pdr (deferred)

`audit-adr` and `audit-pdr` (skills + agents) landed at SCOPE-MIN per `spx/21-spec-tree.enabler/32-decisions.enabler/PLAN.md` — the established read-only verdict-producer shape shared by the other spec-tree audit agents. They do NOT yet conform to `spx/21-spec-tree.enabler/16-verification.enabler`:

- The wrapper agents use `tools: Read, Glob, Grep` and no `model:` field; `16-verification.enabler` requires `model: sonnet` and `tools: Bash, Read, Skill`.
- No `scripts/` CLI arbiter module encodes the verification policy (schema conformance) for the wrapper agent to invoke; the verdict schema is described in skill prose.
- No thread-store persistence of the machine-readable result + markdown surface.
- The audit skills' LLM-judgment assertions carry forward-referenced `[eval]` (the new mode-floor scenarios) alongside pre-existing `[test]` scenarios in `pdr-auditing.md`; the full re-tag to `[eval]` and the eval suites themselves are unbuilt (both `21-adr-auditing.enabler` and `32-pdr-auditing.enabler` are in `spx/EXCLUDE`).

This conformance is an architecture migration that applies to the whole audit-skill family, not just these two, and is independent of the per-rule-evidence-mode feature. Address it as its own change: build the `scripts/` arbiter, reshape the audit agents to `model: sonnet` + `Bash, Read, Skill`, wire thread-store persistence, and build the eval suites. Until then, audit-adr/audit-pdr run as read-only verdict producers in the established pre-conformance pattern.

## Mode-tag migration for existing decision records (deferred)

The per-rule-evidence-mode feature declares (in `decisions.md`) that every decision-record compliance rule names one of `scenario`, `mapping`, `conformance`, `property`, `compliance`, and the ADR/PDR templates require the tag. The marketplace's own existing ADRs and PDRs still carry bare `([review])` mechanism tags on their Compliance MUST/NEVER rules, so `/audit-adr` and `/audit-pdr` deterministically REJECT them at the mode-validity step (`invalid-mode-tag`) until each rule is migrated.

Records to migrate — for each rule, route the claim shape through `/testing` to pick its mode, then replace the bare mechanism tag:

- `spx/13-plugin-and-runtime-conventions.adr.md`
- `spx/15-spec-coverage.adr.md`
- `spx/15-test-language.adr.md`
- `spx/15-audit-verdict-format.pdr.md`
- `spx/15-test-infrastructure.pdr.md`
- `spx/15-agent-pr-authority.pdr.md`
- `spx/16-evidence-execution-lanes.adr.md`
- `spx/21-spec-tree.enabler/17-auditing.adr.md`
- `spx/18-plugin-build.enabler/15-build-architecture.adr.md`
- `spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md`
- `spx/15-validation.enabler/32-skill-frontmatter.enabler/15-frontmatter-validation.adr.md`
- `spx/15-validation.enabler/65-gate.enabler/15-process-injection.adr.md`
- `spx/32-distribution.enabler/21-bump.enabler/15-bump-shape.adr.md`
- `spx/13-infrastructure.enabler/32-installation.enabler/21-codex-cache-preservation.adr.md`
- `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/21-script-decomposition.adr.md`

This is a repo-wide reconciliation triggered by the new declaration — too large to belong in the feature PR. Migrate the records as its own change; the declaration leads and the records follow.
