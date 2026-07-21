# Issues

## The delta-only assertion has no cross-sibling enforcement gate

`test-verification.md` asserts that every language-specific test-standard node cites this node and `15-test-infrastructure.pdr.md` and declares only its language delta, never restating or weakening the seam rules this node owns ([audit]). No gate enforces that assertion across the sibling language nodes. The changeset reviewer (`spec-tree:changes-reviewer`), the per-language artifact auditors (`audit-{python,rust,typescript}-{tests,code,architecture}`), and `/align` each judge one node or one changeset in isolation; none compares `spx/43-python.enabler`, `spx/43-rust.enabler`, and `spx/43-typescript.enabler` against this superset or against each other. A future edit that restates a superset rule inside a language node, or lets two language nodes diverge, passes every gate — the same blind spot that let the pre-superset duplication reach the default branch unflagged.

**Resolution shape** (fix deferred by operator decision, to be scoped in the skill and agent specialization work): add cross-sibling equivalence detection to the gate set — an `/align` check that every language test-standard node cites this node and declares only deltas, an audit assertion on each language node verifying delta-only content against the cited superset, or a review dimension that compares sibling language standards.

**Evidence.** Named by the operator after observing that the seam specs of all three languages were extremely repetitive and that no auditor or changeset reviewer flagged the repetition across the changeset that carried it.
