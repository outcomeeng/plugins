# Issues

## The delta-only assertion has no cross-sibling enforcement gate

`test-verification.md` asserts that every language-specific test-standard node cites this node and `15-test-infrastructure.pdr.md` and declares only its language delta, never restating or weakening the seam rules this node owns ([audit]). No gate enforces that assertion across the sibling language nodes. The changeset reviewer (`spec-tree:changes-reviewer`), the per-language artifact auditors (`audit-{python,rust,typescript}-{tests,code,architecture}`), and `/align` each judge one node or one changeset in isolation; none compares `spx/43-python.enabler`, `spx/43-rust.enabler`, and `spx/43-typescript.enabler` against this superset or against each other. A future edit that restates a superset rule inside a language node, or lets two language nodes diverge, passes every gate — the same blind spot that let the pre-superset duplication reach the default branch unflagged.

**Resolution shape** (fix deferred by operator decision, to be scoped in the skill and agent specialization work): add cross-sibling equivalence detection to the gate set — an `/align` check that every language test-standard node cites this node and declares only deltas, an audit assertion on each language node verifying delta-only content against the cited superset, or a review dimension that compares sibling language standards.

**Evidence.** Named by the operator after observing that the seam specs of all three languages were extremely repetitive and that no auditor or changeset reviewer flagged the repetition across the changeset that carried it.

## Accepted adversarial-review findings against the shipped test-skill families

An adversarial review of the merged PR #519 changeset (`988af420b503b010d85bda6e0afa3a748b5929b5..c42fceef6ef807429e7047d043e517b5e468df0d`) produced nine valid findings; the closing verification of their spec-layer fixes is the sealed review run `2026-08-14_14-34-24-824-a1416573df24`, and the remaining findings below are verifiable directly in the shipped surfaces they name. The five spec-layer findings are resolved: the level discriminator with its boundary rewording of scenario cases 4 and 5, the provenance-bound construction laws with rejected mapping case 25, the default-runner obligation with the pytest and Vitest declarations, the assertion-type taxonomy word at the spec sites, and the realization-only rewrite of both language execution-level delta lines.

Two skill-family findings remain:

- The shipped `/audit-tests` skill does not consume the shared standard's evidence-cell criteria: it loads the legacy rule families only, extracts no declared execution level from the filename, and its finding schema carries no execution-level or filename property — a test declaring `l1` while reaching a remote dependency can still be approved. Fold the audit step and verdict-schema extension for the filename, level-floor, harness, availability, and type-permission criteria into the operator-parked audit-tests rebuild that derives graded cases from the corpus decision. Deferred as a separate larger concern because it changes the audit methodology, its verdict schema, and its eval suites together. Surfaced by the PR #522 current-head review (head 16f35be0428979373d0865e97463dacd9bb1e41b).
- The TypeScript predicate-in-harness sites and the blanket binding ban are already owned by `spx/43-typescript.enabler/25-typescript-standards.enabler/PLAN.md` and get no second record here.
