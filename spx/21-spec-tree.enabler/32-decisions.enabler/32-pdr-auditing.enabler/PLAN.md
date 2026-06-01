# Plan: Rename auditing-product-decisions → audit-pdr + mode-floor check

## Purpose

This node governs the PDR audit. The rename to `audit-pdr` and the new mode-floor downstream-sufficiency check land here. `audit-adr` is the parallel ADR audit under a new sibling node — see `spx/21-spec-tree.enabler/32-decisions.enabler/PLAN.md`.

## Changes

### 1. Rename the skill and agent

`auditing-product-decisions` → `audit-pdr` (skill); `pdr-auditor` → `audit-pdr` (agent). Imperative name authorized by the repo-local `spx/local/standardizing-skills.md` overlay introduced in the parent plan — land that overlay before the rename so `/auditing-skills` does not flag the new name.

### 2. Update this node's references to the old skill name

`pdr-auditing.md` names `/auditing-product-decisions` in the Content Classification prose (line 24), one scenario assertion (line 57), and the conformance assertion (line 70). The other scenarios (lines 58–62) use the `when audited` shorthand and carry no skill-name reference. Update the three explicit occurrences to `/audit-pdr`, and the same references inside `tests/test_pdr_auditing.*.py` bodies.

### 3. Add the mode-floor downstream-sufficiency assertion

The existing downstream-flow assertions verify each compliance rule resolves to *some* downstream spec assertion (presence). Add the sufficiency half: the audit verifies the downstream assertion's evidence meets or exceeds the rule's declared mode (see `spx/21-spec-tree.enabler/21-templates.enabler/PLAN.md` for the per-rule mode tag). A scenario test under a `property`-floor rule is a finding, not a judgment call.

### 4. Conformance

`audit-pdr` conforms to `spx/21-spec-tree.enabler/16-verification.enabler` (thin wrapper agent, structured JSON verdict + markdown surface, `scripts/` CLI arbiter, thread-store persistence) and `spx/15-audit-verdict-format.pdr.md` (canonical `verdict.py` schema via `emit_verdict.py`). Verify whether the current skill already conforms; close any gap as part of the rename rather than carrying it forward.

## Spec impact

- `pdr-auditing.md`: update `/auditing-product-decisions` → `/audit-pdr`; add the mode-floor downstream-sufficiency assertion.
- Evidence mechanism for assertions about `audit-pdr`'s own LLM judgment behavior is `[eval]` per `spx/15-spec-coverage.adr.md` (the skill emits a structured verdict); structural-conformance assertions carry `[test]`; design assertions carry `[review]`. Mechanism is distinct from the per-rule mode tag.

## Files

- `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/pdr-auditing.md`
- `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler/tests/` (skill-name references in test bodies)
- rename: `src/plugins/spec-tree/skills/auditing-product-decisions/` → `audit-pdr/`
- rename: `src/plugins/spec-tree/agents/pdr-auditor.md` → `audit-pdr.md`

## Implementation skills (in order)

1. `spec-tree:understanding`
2. `spec-tree:contextualizing` on `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler`
3. `spec-tree:authoring` for the mode-floor assertion
4. `develop:standardizing-skills` for the rename — only after the repo-local naming overlay `spx/local/standardizing-skills.md` lands (created in the parent plan `spx/21-spec-tree.enabler/32-decisions.enabler/PLAN.md` step 3; complete that step first)
5. `develop:creating-subagents` for the renamed agent
6. `audit-pdr` (the renamed skill) to self-audit `pdr-auditing.md`
7. `spec-tree:committing-changes`

## Audit gates

- `audit-pdr` self-audit on `pdr-auditing.md`.
- `develop:auditing-skills` on the renamed skill — confirm the repo-local naming overlay clears the imperative-name finding.
- `just check`.

## Related plans

- `spx/21-spec-tree.enabler/32-decisions.enabler/PLAN.md` — parent coordination: the `audit-adr` sibling node and the naming overlay
