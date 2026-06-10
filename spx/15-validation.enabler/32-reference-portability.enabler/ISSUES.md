# Issues: Reference Portability Validation

## Sample inputs stay test-owned domain members, not source exports (resolved by decision)

A review pass proposed exporting canonical sample references from
`outcomeeng/validation/reference_portability.py` for the test to import. This is
declined: the detector's discriminator is a structural partition (numeric-prefix and
repository-segment shape), not a single source-owned constant, so the per-category
sample strings are domain members the test legitimately owns. Exporting sample data
from the source module purely for the test is the test-data-in-source anti-pattern
`spx/15-test-infrastructure.pdr.md` forbids, and the test-evidence audit approved the
inline samples on that basis.

## The `outcomeeng/spx` exclusion passes the whole subtree, not just the bare slug

The discriminator excludes `outcomeeng/spx` (and `outcomeeng/plugins`) via the negative
lookahead `outcomeeng/(?!plugins(?![\w-])|spx(?![\w-]))…`, so the GitHub org/repo slug
stays portable. The same lookahead passes every `outcomeeng/spx/…` path, including a deep
local-checkout path such as `~/Code/outcomeeng/spx/src/types.ts` that resolves in no
consumer checkout. Narrowing the exclusion to the bare slug (no trailing path segment)
would flag those, but would also flag legitimate `outcomeeng/plugins/blob/main/…` GitHub
URL paths in install docs. Evaluate whether the exclusion should be narrowed to the bare
slug only, and migrate any genuine local-path references that surface — the file the
review cited (`src/plugins/typescript/skills/coding-typescript/references/vocabulary-registry-pattern.md`)
is one such reference outside this change's diff.
