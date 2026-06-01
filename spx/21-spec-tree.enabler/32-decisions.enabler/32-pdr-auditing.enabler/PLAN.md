# Plan (detailed): rename auditing-product-decisions → audit-pdr + mode-floor

Exact execution spec for the PDR-audit node. Parent coordination (naming overlay, `decisions.md` assertion, the `adr-auditing` sibling node, `audit-adr` skill/agent, the SCOPE-MIN vs SCOPE-FULL `16-verification.enabler` decision, commit/bump strategy) lives in `spx/21-spec-tree.enabler/32-decisions.enabler/PLAN.md`. Land the naming overlay (parent part A) before the rename here. Written for **SCOPE-MIN** (current skill/agent shape preserved).

This node is in `spx/EXCLUDE`; its `[test]`/`[eval]` links are forward references.

## A. `pdr-auditing.md` — skill-name reference updates (exact)

Three explicit `/auditing-product-decisions` occurrences become `/audit-pdr`. The other scenarios (lines 58–62) use the `when audited` shorthand and need no change.

1. Content Classification prose (currently line 24): `The`/auditing-product-decisions`skill in the spec-tree plugin classifies every statement in the PDR:` → `The`/audit-pdr`skill in the spec-tree plugin classifies every statement in the PDR:`
2. First scenario (currently line 57): `when audited by`/auditing-product-decisions`,` → `when audited by`/audit-pdr`,`
3. Conformance assertion (currently line 70): `The`/auditing-product-decisions`skill invokes`/contextualizing``→ `The `/audit-pdr` skill invokes `/contextualizing``

## B. `pdr-auditing.md` — mode-floor sufficiency (spec additions)

The existing downstream-flow assertions verify each compliance rule resolves to *some* downstream assertion (presence). Add the sufficiency half. Two additions:

Add one Scenario (the judgment case), after the existing APPROVED scenario:

```markdown
- Given a PDR whose `property`-floor compliance rule resolves only to a `scenario` spec assertion, when audited by `/audit-pdr`, then the verdict is REJECT with finding category "insufficient-evidence-mode" ([eval](evals/mode-floor/eval.toml))
```

Add one Compliance rule, after the existing `NEVER: approve a PDR whose compliance rules have zero downstream assertions`:

```markdown
- NEVER: approve a PDR whose downstream spec assertion carries evidence below the rule's declared mode — a scenario test under a property-floor rule is a finding, not a judgment call ([review])
```

Mechanism rationale (per `spx/15-spec-coverage.adr.md`): the judgment Scenario carries `[eval]` (the skill emits a structured verdict); the design Compliance rule carries `[review]`, matching the node's existing downstream-flow `[review]` assertions. Mechanism is distinct from the per-rule mode tag the audit reads in a decision record. Node EXCLUDEd → `evals/mode-floor/eval.toml` is a forward reference; build the eval when the node leaves EXCLUDE. Confirm EXCLUDE silences the forward `[eval]` link-integrity check during `/authoring`; if not, use `[review]` for the scenario this pass and record the eval as follow-up.

## C. Pre-existing evidence-mechanism gap (NOTE — out of SCOPE-MIN)

`pdr-auditing.md`'s existing behavior Scenarios + the Property assertion carry `[test]` (forward-ref `tests/test_pdr_auditing.*.py`). Per `spx/15-spec-coverage.adr.md` and `spx/21-spec-tree.enabler/16-verification.enabler`, a verification skill's LLM-judgment assertions should carry `[eval]`, not `[test]`. Re-tagging all of them (and building the evals) is the `16-verification.enabler` conformance work scoped in the parent plan's SCOPE decision. SCOPE-MIN leaves the existing `[test]` tags as-is and records the re-tag as part of that follow-up; do NOT silently change them here without the operator's SCOPE-FULL choice.

## D. Skill rename — `auditing-product-decisions` → `audit-pdr`

After the naming overlay (parent A) lands. Via `develop:standardizing-skills`:

- `git mv src/plugins/spec-tree/skills/auditing-product-decisions src/plugins/spec-tree/skills/audit-pdr`
- `audit-pdr/SKILL.md` frontmatter `name: auditing-product-decisions` → `name: audit-pdr`; keep `description: Use when asked by the user to invoke the PDR audit skill`.
- Inside `audit-pdr/SKILL.md` body + `references/pdr-evidence-model.md`: replace `/auditing-product-decisions` self-references and the `"skill": "auditing-product-decisions"` JSON example field with `audit-pdr`.
- `references/` filename `pdr-evidence-model.md` stays (descriptive, PDR-specific).

## E. Agent rename — `pdr-auditor` → `audit-pdr`

Via `develop:creating-subagents` (SCOPE-MIN keeps the current tool/model shape):

- `git mv src/plugins/spec-tree/agents/pdr-auditor.md src/plugins/spec-tree/agents/audit-pdr.md`
- Frontmatter `name: pdr-auditor` → `name: audit-pdr`; `skills: [spec-tree:auditing-product-decisions]` → `skills: [spec-tree:audit-pdr]`; keep `tools: Read, Glob, Grep` and the description. (SCOPE-FULL: `tools: Bash, Read, Skill`, add `model: sonnet`, route through a `scripts/` arbiter.)

## F. Conformance to `spx/15-audit-verdict-format.pdr.md`

The skill already emits a JSON verdict conforming to `verdict.py` and states its success criterion as the validator's exit code (`<verdict_format>`). No change needed at SCOPE-MIN beyond the `"skill"` field rename in the JSON example.

## Implementation skills (in order)

1. `spec-tree:understanding` (done)
2. `spec-tree:contextualizing` on `spx/21-spec-tree.enabler/32-decisions.enabler/32-pdr-auditing.enabler`
3. Confirm parent part A (`spx/local/standardizing-skills.md`) has landed
4. `spec-tree:authoring` for the mode-floor Scenario + Compliance additions (B) and the ref updates (A)
5. `develop:standardizing-skills` for the skill rename (D)
6. `develop:creating-subagents` for the renamed agent (E)
7. `audit-pdr` (renamed) self-audit on `pdr-auditing.md`
8. `spec-tree:committing-changes`

## Audit gates

- `audit-pdr` self-audit on `pdr-auditing.md`.
- `develop:auditing-skills` on the renamed skill — confirm the naming overlay clears the imperative-name finding.
- `just check` (once, after the single end-of-branch bump per the parent plan's part G).

## Related plans

- `spx/21-spec-tree.enabler/32-decisions.enabler/PLAN.md` — parent: naming overlay, `adr-auditing` node, `audit-adr`, the SCOPE decision, bump strategy
