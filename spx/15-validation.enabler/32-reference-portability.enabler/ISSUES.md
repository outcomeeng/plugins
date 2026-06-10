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
stays portable — but the same lookahead also passes every deeper `outcomeeng/spx/…` path,
which the validator's ALWAYS assertion (passes only references a consumer resolves) does
not bless. No such reference remains in shipped content: the one the review surfaced
(`~/Code/outcomeeng/spx/src/types.ts`, a personal local-checkout path in the typescript
vocabulary-registry reference) is removed in this change.

Open refinement: narrow the exclusion to the bare slug (no trailing path segment) so a
future deep `outcomeeng/spx/…` path is flagged, and add a matching `NONPORTABLE` sample to
`tests/test_reference_portability.compliance.l1.py`. The trade-off is that narrowing would
also flag a legitimate `outcomeeng/plugins/blob/main/…` GitHub URL in install docs (none
exist today), so the bare-slug semantics deserve a deliberate decision rather than a rushed
regex change.
