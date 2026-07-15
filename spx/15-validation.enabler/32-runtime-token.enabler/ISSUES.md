# Issues - Runtime Token Validation

Known follow-ups for runtime-token validation. Coordination note; not spec
truth.

## Compound target predicates are outside the canonical scanner form

Review run `2026-07-15_03-20-51-675-5765b9592066` found that the runtime-token
scanner recognizes the canonical `target == '<runtime>'` and
`elif target == '<runtime>'` forms emitted by the production formatter, while a
compound or reordered predicate falls back to flat scanning and can report a
runtime name inside an otherwise target-constrained branch.

The scanner contract currently covers the canonical formatter-owned form used
by authored plugin source and its generated evidence. Revisit when the authoring
surface permits compound or reordered target predicates: decide whether the
source contract remains canonical equality only or expands to a parsed predicate
model, then align `spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`,
the formatter, scanner, generators, and violating-case evidence in one change.

## Bare-else target scoping lacks generated evidence

PR #432 current-head review comment
`https://github.com/outcomeeng/plugins/pull/432#issuecomment-4982176438`
confirmed that `outcomeeng_testing/generators/runtime_tokens.py` generates
single-branch, nested, and explicit target-branch cases without generating a
bare `{!% else %!}` branch. The missing case leaves the complement-target logic
in `outcomeeng/validation/runtime_tokens.py::_update_else_frame` without an
independent targeted oracle even though bare `if`/`else` conditionals are the
dominant authored-source form.

This is an evidence defect against the clean-conditional scenario in
`spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`: the
whole-corpus zero-violation assertion cannot distinguish correct target
complement scoping from a scanner that silently permits the same corpus for the
wrong reason.

Required handling:

- Extend the source-owned runtime-token generator with matching and mismatching
  bare-`else` cases for every enforced runtime name.
- Assert that the `else` branch is scoped to the parent target set minus every
  target matched by preceding branches.
- Run the focused runtime-token tests and a test-evidence audit over the repaired
  generator chain before removing this issue.
