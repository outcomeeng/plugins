# Plan: INVALID_* smell + boundary validation in standardizing-python-tests

## Purpose

Apply the boundary-validation router (`spx/21-spec-tree.enabler/35-evidence.enabler/PLAN.md`) to Python test standards, so authors reach for a Hypothesis strategy over open domains or a source-owned enumeration over finite domains instead of a hand-picked bag of invalid inputs.

## Changes

### 1. `INVALID_*` tuples flagged as a smell

`INVALID_*_INPUTS` / `INVALID_*_CASES` tuples at module or class scope join the anti-pattern list: a hand-picked bag of invalid values. The remedy depends on the domain:

- open value space (strings, IDs, timestamps, keys, generated names) → a Hypothesis strategy generating values outside the valid predicate
- closed, source-owned set → import the source enum or registry rather than hand-copying members

### 2. Boundary-validation guidance in the property section

An assertion that a field rejects values outside a predicate is a `property` claim when the invalid set is open or infinite; a finite parameterized set is correct only when the set is closed and source-owned. Mode selection defers to `/testing` — this skill teaches the Python expression of the router's output, not a parallel decision procedure.

## Files

- `src/plugins/python/skills/standardizing-python-tests/SKILL.md`
- regenerate `dist/claude` + `dist/codex` via `just build-skills`

## Spec impact

None expected. `python-tests.md` already asserts "Python test guidance starts from the spec assertion and selected evidence type before choosing file names … evidence shape follows the claim being proved" and "variable test input domains come from generators that vary … not to hide constants." This change is skill-level implementation of those assertions; confirm during implementation that no new assertion is required.

## Implementation skills (in order)

1. `spec-tree:understanding`
2. `spec-tree:contextualizing` on `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler`
3. `python:testing-python` before changing Python test guidance
4. `develop:standardizing-skills` before editing the `SKILL.md`
5. `python:auditing-python-tests` after the change
6. `spec-tree:committing-changes`

## Audit gates

- `python:auditing-python-tests` reasoning against a sample boundary assertion.
- `just check` (touches plugin source + dist).

## Related plans

- `spx/21-spec-tree.enabler/35-evidence.enabler/PLAN.md` — the language-agnostic router this implements for Python
