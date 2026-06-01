# Plan (detailed): INVALID_* smell + boundary validation in standardizing-python-tests

Exact execution spec. Applies the language-agnostic boundary-validation router (`spx/21-spec-tree.enabler/35-evidence.enabler`, landed) to Python test standards. Skill-level only: teaches the Python expression of `/testing`'s router, not a parallel decision procedure.

File: `src/plugins/python/skills/standardizing-python-tests/SKILL.md` (a reference skill, `user-invocable: false`). Tier-3; depends on tier 1's `/testing` router. `python` plugin bump = `patch` (modified SKILL.md), taken in the single end-of-branch bump per `spx/21-spec-tree.enabler/32-decisions.enabler/PLAN.md` part G.

## A. `<anti_patterns>` — add the INVALID_* bullet

Add one bullet to the `<anti_patterns>` list, after the existing `- Hand-picked test cases — …` bullet:

```markdown
- `INVALID_*_INPUTS` / `INVALID_*_CASES` tuples, or any module- or class-scope bag of invalid values — a hand-picked set standing in for the invalid domain. Remedy by domain: an open or infinite invalid space (arbitrary strings, identifiers, timestamps, keys, generated names) takes a Hypothesis strategy generating values *outside* the valid predicate; a closed, source-owned invalid set (enum variants, a defined protocol set, registry members) imports the source enum or registry rather than hand-copying members
```

## B. New `<boundary_validation>` section

Insert a new XML section immediately AFTER `<property_based_testing>` and BEFORE `<anti_patterns>`. Exact content:

```markdown
<boundary_validation>
An assertion that a field, parser, or constructor rejects values outside a predicate routes by the shape of the invalid set, not by a hand-picked bag of bad inputs.

- Open or infinite invalid space — arbitrary strings, identifiers, timestamps, keys, generated names — is a `property` claim. The evidence is a Hypothesis strategy generating values outside the valid predicate (for example `st.text().filter(lambda s: not s.isidentifier())`), asserting rejection across the generated domain.
- Closed, source-owned invalid set — enum variants, a defined protocol set, registry members — is a `mapping` claim. The evidence parameterizes over every source-owned invalid member, imported from the owning module, never hand-copied.

A `property`-floor rejection rule is not satisfied by a finite parametrize over a hand-picked subset of an open space. Mode selection is `/testing`'s authority (see the boundary-validation router in `/testing`'s methodology); this standard teaches only the Python expression of that router's output.
</boundary_validation>
```

(Blank line before the closing `</boundary_validation>` tag per the `fix-xml-spacing` rule, since the section ends on a list.)

## C. Spec impact — confirm none

`spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/python-tests.md` already asserts that Python test guidance starts from the spec assertion and selected evidence type, that evidence shape follows the claim being proved, and that variable test input domains come from generators that vary rather than hide constants. This change is skill-level implementation of those assertions. During implementation, read `python-tests.md` and confirm no new assertion is required; if the INVALID_* smell needs a dedicated assertion, author it via `/authoring` (it would be a Compliance `[review]` rule mirroring the existing generator/variation assertions).

## Implementation skills (in order)

1. `spec-tree:understanding` (done)
2. `spec-tree:contextualizing` on `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler`
3. `python:testing-python` before changing Python test guidance
4. `develop:standardizing-skills` before editing the `SKILL.md`
5. `python:auditing-python-tests` reasoning against a sample boundary assertion after the change
6. `spec-tree:committing-changes`

## Audit gates

- `python:auditing-python-tests` reasoning against a sample boundary assertion (open-domain rejection → expects `property` + Hypothesis strategy; closed source-owned → expects `mapping` over the imported set).
- `just check` (once, after the single end-of-branch bump).

## Related plans

- `spx/21-spec-tree.enabler/35-evidence.enabler/PLAN.md` — the language-agnostic router this implements for Python (landed)
