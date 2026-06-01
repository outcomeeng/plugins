# Plan: Decision-record evidence-mode enforcement + audit-adr / audit-pdr

## Purpose

Decision records declare a minimal evidence mode per compliance rule (see `spx/21-spec-tree.enabler/21-templates.enabler/PLAN.md`). The decision-record audits verify two things: every MUST/NEVER rule carries a valid mode, and a downstream spec assertion enforces each rule with evidence at or above that mode. This extends the existing downstream-flow check from **presence** of enforcement to **sufficiency** of enforcement, giving decisions teeth instead of leaving evidence strength to interpretation.

## Node structure

The decision-record audits live as child nodes under this node:

- `audit-pdr` (rename of `auditing-product-decisions`) is governed by the **existing** child `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler` — see its `PLAN.md` for the rename specifics.
- `audit-adr` is governed by a **new** sibling child parallel to `32-pdr-auditing.enabler` (e.g. `NN-adr-auditing.enabler`), created via `/authoring`. Its behavior assertions live in that node's spec, mirroring `pdr-auditing.md`.
- The parent `decisions.md` carries only the lifecycle-level rule (every decision rule declares a mode). The audit-behavior assertions live in the child auditing nodes, not in `decisions.md`.

## Changes

### 1. Evidence-mode floor in the decision-record lifecycle

Each ADR/PDR compliance rule carries one of the five modes, chosen via `/testing`. The mode is the minimum the enforcing spec assertion must meet. A scenario test under a `property`-floor rule is a finding the audit raises against the decision, not a judgment call.

### 2. `audit-adr` — new, generic, language-agnostic ADR decision audit

Checks section structure, atemporal voice, per-rule mode validity, and downstream flow (each rule resolves to a spec assertion whose evidence meets or exceeds the declared mode). Governed by a new sibling auditing node (above). KISS-additive: standalone, **not** folded into the `/auditing` language orchestrator. Language-specific ADR concerns (testability-in-Compliance for DI/no-mocking, level accuracy) stay in `auditing-{lang}-architecture`. A short overlap on structure/voice is accepted now and tightened later.

### 3. `audit-pdr` — rename of `auditing-product-decisions`

Keeps the six-property model; adds the mode-floor downstream-sufficiency check. Rename the skill `auditing-product-decisions` → `audit-pdr` and the agent `pdr-auditor` → `audit-pdr`. The governing node `32-pdr-auditing.enabler` names the old skill in its assertions and tests; those references are updated as part of the rename (see that node's `PLAN.md`).

### 4. Imperative names, no command shims

`audit-adr` and `audit-pdr` use imperative names with no command shims — the gerund→imperative transition applied to these two skills only this pass. The existing eight command shims (`apply`, `author`, `bootstrap`, `clarify`, `commit`, `open-pr`, `review-changes`, `rtfm`) and the wider rename are out of scope here.

### 5. Conformance

Both skills conform to:

- `spx/21-spec-tree.enabler/16-verification.enabler` — thin wrapper agent (`model: sonnet`, `tools: Bash, Read, Skill`, `skills:` listing the skill), one structured JSON verdict + one markdown surface, verification policy in a `scripts/` CLI arbiter, persistence through the thread-store interface. No change to that node's spec; the new agents are conforming instances.
- `spx/15-audit-verdict-format.pdr.md` — JSON verdicts conforming to `verdict.py`, rendered via `emit_verdict.py`.

Verify whether the current `auditing-product-decisions` already conforms; close any gap as part of the rename.

### 6. Authorize imperative audit-skill names (repo-local)

`develop/skills/standardizing-skills` prefers gerund form, so `/auditing-skills` would flag `audit-adr` / `audit-pdr` against their own names. Add `spx/local/standardizing-skills.md` (the repo-local overlay `standardizing-skills` already reads) authorizing imperative form for standalone audit skills in this marketplace. This keeps the shipped `develop` plugin gerund-preferred for consumers (marketplace-visibility boundary) while the marketplace transitions. Prerequisite before creating/renaming the two skills.

## Spec impact

- `decisions.md` (parent): ALWAYS — every decision-record compliance rule declares a single evidence mode, chosen via `/testing` from the rule's claim shape.
- `32-pdr-auditing.enabler/pdr-auditing.md`: add the mode-floor downstream-sufficiency assertion (extends its existing downstream-flow assertions); update `/auditing-product-decisions` → `/audit-pdr` references.
- new adr-auditing node spec: `audit-adr` behavior assertions (structure, voice, per-rule mode validity, downstream sufficiency), mirroring `pdr-auditing.md`.

Evidence for the assertions that govern `audit-adr` / `audit-pdr`'s own behavior follows the **mechanism** axis (`[test]` / `[review]` / `[eval]`) — distinct from the per-rule **mode** tag those audits read in a decision record (see `spx/21-spec-tree.enabler/21-templates.enabler/PLAN.md`; `[eval]` is never a per-rule mode tag). Per `spx/15-spec-coverage.adr.md` (not an open choice): assertions about the audits' LLM judgment behavior carry the `[eval]` mechanism — the skills emit structured verdicts, so the ADR mandates eval over `[review]`; structural-conformance assertions (verdict-schema validity, JSON emission) carry `[test]`; design or intent assertions carry `[review]`. Resolve the eval-case file paths during `/authoring`; do not pre-create a speculative child node.

## Files

- new node: `spx/21-spec-tree.enabler/32-decisions.enabler/NN-adr-auditing.enabler/` (spec + `tests/`) via `/authoring`
- update: `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/pdr-auditing.md` — `/auditing-product-decisions` → `/audit-pdr` (prose at line 24, scenario at line 57, conformance at line 70) + mode-floor assertion
- update: `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/tests/` — `/auditing-product-decisions` references inside the test bodies
- new: `src/plugins/spec-tree/skills/audit-adr/` (SKILL.md, references, `scripts/` arbiter as needed)
- rename: `src/plugins/spec-tree/skills/auditing-product-decisions/` → `audit-pdr/`
- new: `src/plugins/spec-tree/agents/audit-adr.md`
- rename: `src/plugins/spec-tree/agents/pdr-auditor.md` → `audit-pdr.md`
- new: `spx/local/standardizing-skills.md` (authorize imperative audit-skill names)
- update cross-references to `auditing-product-decisions` / `pdr-auditor` (AGENTS.md/CLAUDE.md tables, README catalog via `just docs`, any skill referencing them)
- regenerate `dist/claude` + `dist/codex` via `just build-skills`

## Implementation skills (in order)

1. `spec-tree:understanding`
2. `spec-tree:contextualizing` on `spx/21-spec-tree.enabler/32-decisions.enabler`
3. Create `spx/local/standardizing-skills.md` (Change 6) authorizing imperative form for standalone audit skills in this marketplace — prerequisite for the step 5 rename so `/auditing-skills` does not flag `audit-adr` / `audit-pdr`
4. `spec-tree:authoring` for the new adr-auditing node, the `pdr-auditing.md` mode-floor assertion, and the `decisions.md` lifecycle assertion
5. `develop:creating-skills` for `audit-adr`; `develop:standardizing-skills` for the `audit-pdr` rename (after the step 3 naming overlay lands)
6. `develop:creating-subagents` for the two wrapper agents
7. `audit-pdr` (the renamed skill) to self-audit the amended decision specs
8. `spec-tree:committing-changes`

## Audit gates

- Decision audit (`audit-adr` / `audit-pdr`) on the amended decision specs before proceeding.
- Skill audits (`develop:auditing-skills`) on `audit-adr` and `audit-pdr` — confirm the repo-local naming overlay clears the imperative-name finding.
- Subagent audit (`develop:auditing-subagents`) on the two new agents.
- `just check` (touches plugin source + catalog + dist).

## Related plans

- `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/PLAN.md` — the `audit-pdr` rename specifics
- `spx/21-spec-tree.enabler/21-templates.enabler/PLAN.md` — the per-rule mode tag these audits read
- `spx/21-spec-tree.enabler/35-evidence.enabler/PLAN.md` — the `/testing` router that picks the mode
