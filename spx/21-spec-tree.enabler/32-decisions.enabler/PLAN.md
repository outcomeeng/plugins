# Plan: Decision-record evidence-mode enforcement + audit-adr / audit-pdr

## Purpose

Decision records declare a minimal evidence mode per compliance rule (see `spx/21-spec-tree.enabler/21-templates.enabler/PLAN.md`). The decision-record audits verify two things: every MUST/NEVER rule carries a valid mode, and a downstream spec assertion enforces each rule with evidence at or above that mode. This extends the existing downstream-flow check from **presence** of enforcement to **sufficiency** of enforcement, giving decisions teeth instead of leaving evidence strength to interpretation.

## Changes

### 1. Evidence-mode floor in the decision-record lifecycle

Each ADR/PDR compliance rule carries one of the five modes, chosen via `/testing`. The mode is the minimum the enforcing spec assertion must meet. A scenario test under a `property`-floor rule is a finding the audit raises against the decision, not a judgment call.

### 2. `audit-adr` — new, generic, language-agnostic ADR decision audit

Checks section structure, atemporal voice, per-rule mode validity, and downstream flow (each rule resolves to a spec assertion whose evidence meets or exceeds the declared mode). KISS-additive: standalone, **not** folded into the `/auditing` language orchestrator. Language-specific ADR concerns (testability-in-Compliance for DI/no-mocking, level accuracy) stay in `auditing-{lang}-architecture`. A short overlap on structure/voice is accepted now and tightened later.

### 3. `audit-pdr` — rename of `auditing-product-decisions`

Keeps the six-property model; adds the mode-floor downstream check. Rename the skill `auditing-product-decisions` → `audit-pdr` and the agent `pdr-auditor` → `audit-pdr`.

### 4. Imperative names, no command shims

`audit-adr` and `audit-pdr` use imperative names with no command shims — the gerund→imperative transition applied to these two skills only this pass. The existing eight command shims (`apply`, `author`, `bootstrap`, `clarify`, `commit`, `open-pr`, `review-changes`, `rtfm`) and the wider rename are out of scope here.

### 5. Conformance

Both skills conform to:

- `spx/21-spec-tree.enabler/16-verification.enabler` — thin wrapper agent (`model: sonnet`, `tools: Bash, Read, Skill`, `skills:` listing the skill), one structured JSON verdict + one markdown surface, verification policy in a `scripts/` CLI arbiter, persistence through the thread-store interface. No change to that node's spec; the new agents are conforming instances.
- `spx/15-audit-verdict-format.pdr.md` — JSON verdicts conforming to `verdict.py`, rendered via `emit_verdict.py`.

Verify whether the current `auditing-product-decisions` already conforms; close any gap as part of the rename.

## Spec impact

Add assertions to `decisions.md`:

- ALWAYS: every decision-record compliance rule declares a single evidence mode, chosen via `/testing` from the rule's claim shape.
- ALWAYS: the decision-record audit verifies each rule resolves to a downstream spec assertion whose evidence meets or exceeds the declared mode (extends the existing downstream-flow assertion from presence to sufficiency).
- Existence + conformance assertions for `audit-adr` and `audit-pdr`.

Evidence mode by assertion class, per `spx/15-spec-coverage.adr.md` (not an open choice): assertions about `audit-adr` / `audit-pdr` LLM judgment behavior take `[eval]` — the skills emit structured verdicts, so the ADR mandates eval evidence over `[review]`; structural-conformance assertions (verdict-schema validity, JSON emission) take `[test]`; design or intent assertions take `[review]`. Resolve the eval-case file paths during `/authoring`; do not pre-create a speculative child node.

## Files

- new: `src/plugins/spec-tree/skills/audit-adr/` (SKILL.md, references, `scripts/` arbiter as needed)
- rename: `src/plugins/spec-tree/skills/auditing-product-decisions/` → `audit-pdr/`
- new: `src/plugins/spec-tree/agents/audit-adr.md`
- rename: `src/plugins/spec-tree/agents/pdr-auditor.md` → `audit-pdr.md`
- update cross-references to `auditing-product-decisions` / `pdr-auditor` (AGENTS.md/CLAUDE.md tables, README catalog via `just docs`, any skill referencing them)
- regenerate `dist/claude` + `dist/codex` via `just build-skills`

## Implementation skills (in order)

1. `spec-tree:understanding`
2. `spec-tree:contextualizing` on `spx/21-spec-tree.enabler/32-decisions.enabler`
3. `spec-tree:authoring` for the `decisions.md` assertions
4. `develop:creating-skills` for `audit-adr`; `develop:standardizing-skills` for the `audit-pdr` rename
5. `develop:creating-subagents` for the two wrapper agents
6. `spec-tree:auditing-product-decisions` (becoming `audit-pdr`) to self-audit the amended `decisions.md`
7. `spec-tree:committing-changes`

## Audit gates

- Decision audit on amended `decisions.md` before proceeding.
- Skill audits (`develop:auditing-skills`) on `audit-adr` and `audit-pdr`.
- Subagent audit (`develop:auditing-subagents`) on the two new agents.
- `just check` (touches plugin source + catalog + dist).

## Related plans

- `spx/21-spec-tree.enabler/21-templates.enabler/PLAN.md` — the per-rule mode tag these audits read
- `spx/21-spec-tree.enabler/35-evidence.enabler/PLAN.md` — the `/testing` router that picks the mode
