# Plan: Boundary-validation router + claim-shape rule in the testing methodology

## Purpose

The `/testing` skill owns evidence-mode selection. Two additions close the gap where an agent infers the mode from an ADR's section name (`## Compliance` → `.compliance.l1.py`) instead of the claim's shape, and make `/testing` the single authority both the decision-record author and the test author route through.

## Changes

### 1. Boundary-validation router (methodology.md, Stage 1)

An assertion that rejects values outside a predicate routes by the structure of the invalid set:

- open or infinite — strings, IDs, timestamps, keys, generated names → `property` (Hypothesis strategy over values outside the predicate)
- closed and finite, source-owned — enum variants, a defined protocol set, registry members → `mapping` (parameterized over every source-owned invalid member)

One rule yields one mode. A `property`-floor rule is not satisfied by a finite mapping over a hand-picked subset.

### 2. Evidence mode comes from the claim shape, not the ADR/PDR section name

A MUST/NEVER rule living in a decision record's `## Compliance` section does not imply `compliance` evidence. `/testing` classifies the claim. This is the authority the decision-record templates defer to — the per-rule `([mode])` is `/testing`'s recorded output, not an inference from the section heading.

### 3. `/testing` is the mandatory router for mode selection

No agent hand-picks a mode. The decision-record author runs `/testing` on each compliance rule to record its `([mode])`; the test author runs `/testing` on each spec assertion to pick concrete evidence at or above the floor.

## Spec impact

`evidence.md` may gain an assertion that `/testing` is the single authority for evidence-mode selection, derived from claim shape rather than the section a rule appears in. Author through `/authoring` if added.

## Files

- `src/plugins/spec-tree/skills/testing/references/methodology.md`
- `src/plugins/spec-tree/skills/testing/SKILL.md` (only if the router needs surfacing in the workflow body)
- regenerate `dist/claude` + `dist/codex` via `just build-skills`

## Implementation skills (in order)

1. `spec-tree:understanding`
2. `spec-tree:contextualizing` on `spx/21-spec-tree.enabler/35-evidence.enabler`
3. `spec-tree:authoring` if the `evidence.md` assertion is added
4. `develop:standardizing-skills` before editing the methodology reference
5. `spec-tree:committing-changes`

## Audit gates

- `spx validation markdown` for the methodology + spec edits.
- Re-run `spec-tree:auditing-tests` reasoning against a sample assertion to confirm the router yields the expected mode.

## Related plans

- `spx/21-spec-tree.enabler/21-templates.enabler/PLAN.md` and `spx/21-spec-tree.enabler/32-decisions.enabler/PLAN.md` — consumers of the router's output
- `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/PLAN.md` — the Python-language application of the router
