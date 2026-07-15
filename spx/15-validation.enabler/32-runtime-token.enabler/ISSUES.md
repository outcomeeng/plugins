# Issues - Runtime Token Validation

Known follow-ups for runtime-token validation. Coordination note; not spec
truth.

## Compound target predicates are outside the canonical scanner form

Review run `2026-07-15_03-20-51-675-5765b9592066` found that the runtime-token
scanner recognizes the canonical `target == '<runtime>'` and
`elif target == '<runtime>'` forms emitted by the production formatter, while a
compound or reordered predicate falls back to flat scanning and can report a
runtime name inside an otherwise target-constrained branch.

The accepted merge exception covers the canonical formatter-owned form used by
the authored plugin source and its generated evidence. Revisit when the
authoring surface permits compound or reordered target predicates: decide
whether the source contract remains canonical equality only or expands to a
parsed predicate model, then align `spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`,
the formatter, scanner, generators, and violating-case evidence in one change.
