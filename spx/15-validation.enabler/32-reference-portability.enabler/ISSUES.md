# Issues: Reference Portability Validation

## Shipped content cannot name an organization repository outside the exempt pair

**Evidence:** The ALWAYS assertion in `spx/15-validation.enabler/32-reference-portability.enabler/reference-portability.md` passes the marketplace's own bare GitHub slug with no trailing path segment and enumerates `outcomeeng/plugins` and `outcomeeng/spx`. `MARKETPLACE_REPOSITORY_SLUGS` in `outcomeeng/validation/reference_portability.py` holds exactly that pair, and the `outcomeeng/…` alternative of `_NONPORTABLE_REFERENCE` exempts only those two names. Every other bare `outcomeeng/<name>` matches the toolchain-path alternative, so the detector reports `outcomeeng/methodology` as a non-portable path. The pattern cannot tell a repository slug from a toolchain package path of the same shape, such as `outcomeeng/validation`; the enumeration is the only discriminator.

**Impact:** Shipped plugin content cannot name `outcomeeng/methodology` by slug, although the shipped router tells a consumer to read `methodology.source` from their own `spx.config.yaml` and that value is `outcomeeng/methodology`. Any later mention of another organization repository in shipped content fails the gate the same way.

**Settlement condition:** Shipped content names an organization repository by bare slug and the validator passes it, while a bare toolchain package path such as `outcomeeng/validation` still fails, with compliance cases covering both.

## Sample inputs stay test-owned domain members, not source exports (resolved by decision)

A review pass proposed exporting canonical sample references from
`outcomeeng/validation/reference_portability.py` for the test to import. This is
declined: the detector's discriminator is a structural partition (numeric-prefix and
repository-segment shape), not a single source-owned constant, so the per-category
sample strings are domain members the test legitimately owns. Exporting sample data
from the source module purely for the test is the test-data-in-source anti-pattern
`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` forbids, and the test-evidence audit approved the
inline samples on that basis.
