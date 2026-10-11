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
[`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md) forbids, and the test-evidence audit approved the
inline samples on that basis.

## DEBT [evidence]: harness owns the reference-portability predicates (f-001 to f-005)

Five findings (all REJECT) on the evidence chain of this node:

- f-001 at `outcomeeng_testing/harnesses/reference_portability.py:23`:
  `violation_reports_file_line_reference_and_failure()` owns the whole predicate
  and returns a boolean. The linked test only runs `assert <verdict>`, and the
  expected output is produced by the production `format_violation` (oracle
  independence).
- f-002 at line 39 of the same harness:
  `portable_content_reports_nothing_and_succeeds()` computes the verdict inside
  the harness.
- f-003 at line 50 of the same harness: `every_nonportable_category_is_flagged()`
  returns `all(find_nonportable(...))`.
- f-004 at line 55 of the same harness: `every_portable_category_is_accepted()`
  returns the verdict from inside the harness.
- f-005 at `outcomeeng/distribution/build.py` (no line): the audit left the
  imports of `outcomeeng.distribution.build` and the runtime-token resolution in
  `outcomeeng_testing/generators/source_and_templating.py` uninspected, so the
  evidence chain was incomplete.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run
token.

**Resolution shape**: for f-001 to f-004, return the observation from each
harness function and move the predicate, with an independent oracle, into the
linked test. For f-005, inspect the generator's import chain through the build
and the runtime-token resolution.

**Evidence that the text lies outside the change.**
`git diff -U0 origin/main...HEAD` reports no hunk in the cited files, against
merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset adds symbols to
`outcomeeng/distribution/profiles.py` (model prices, `UsageTokenClass`,
`UnpricedModelError`, `resolve_model_price`; no existing symbol changes), narrows
the guard in `outcomeeng/validation/profile_configuration.py`, and adds
model-price and profile-binding generators, harnesses, and tests. The cited
harness drives `outcomeeng/validation/reference_portability.py` and distribution
contracts, none of which the changeset changes.

**Settlement condition**: the harness functions at lines 23, 39, 50, and 55
return observations while the linked tests own the predicates and an independent
oracle, and an audit inspects the generator's import chain through
`outcomeeng/distribution/build.py` or the generator stops importing the build.
