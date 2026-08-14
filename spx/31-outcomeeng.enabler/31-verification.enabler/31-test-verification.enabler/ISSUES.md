# Issues

## The delta-only assertion has no cross-sibling enforcement gate

`test-verification.md` asserts that every language-specific test-standard node cites this node and `15-test-infrastructure.pdr.md` and declares only its language delta, never restating or weakening the seam rules this node owns ([audit]). No gate enforces that assertion across the sibling language nodes. The changeset reviewer (`spec-tree:changes-reviewer`), the per-language artifact auditors (`audit-{python,rust,typescript}-{tests,code,architecture}`), and `/align` each judge one node or one changeset in isolation; none compares `spx/43-python.enabler`, `spx/43-rust.enabler`, and `spx/43-typescript.enabler` against this superset or against each other. A future edit that restates a superset rule inside a language node, or lets two language nodes diverge, passes every gate — the same blind spot that let the pre-superset duplication reach the default branch unflagged.

**Resolution shape** (fix deferred by operator decision, to be scoped in the skill and agent specialization work): add cross-sibling equivalence detection to the gate set — an `/align` check that every language test-standard node cites this node and declares only deltas, an audit assertion on each language node verifying delta-only content against the cited superset, or a review dimension that compares sibling language standards.

**Evidence.** Named by the operator after observing that the seam specs of all three languages were extremely repetitive and that no auditor or changeset reviewer flagged the repetition across the changeset that carried it.

## Five accepted adversarial-review findings against the merged evidence-types decision

An adversarial review of the merged PR #519 changeset (`988af420b503b010d85bda6e0afa3a748b5929b5..c42fceef6ef807429e7047d043e517b5e468df0d`), recorded at `.spx/reviews/2026-08-14-pr519-codex-adversarial.md` (pool-relative, beside the git common dir), produced five findings, all judged valid:

1. `l1` "repository-standard tools" versus `l2` "product-specific binaries" has no mutually exclusive discriminator — a repository's own CLI is undecidable between the levels, which the decision's own amendment rule makes an amendment obligation (`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md`).
2. The mapping/property construction-law clarification defines independence only against the production path, dropping the author-invention independence `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` requires — a parallel algorithm from the same mental model passes corpus cases 14, 15, and 37. Introduced by the merged changeset.
3. The canonical filename model's "default runner" has no declared owner; each language delta must declare or deterministically derive it.
4. "evidence type" survives where the taxonomy is "assertion type": the amended boundary sentence in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` and two sites in `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/python-tests.md`.
5. Both language execution-level delta lines still enumerate the neutral `l1`/`l2`/`l3` category lists — restating rather than expressing (`spx/43-python.enabler/.../54-execution-level-guidance.enabler` and the TypeScript twin).

**Resolution shape**: one bounded changeset — amend the evidence-types decision (level discriminator plus boundary case, provenance-bound construction laws plus rejected case, default-runner obligation), replace the taxonomy word at the three sites, rewrite the two delta lines to language-specific realization only. A second adversarial review of the same changeset against the shipped `python-test-standards`/`test-python` and TypeScript test-skill surfaces is in flight; fold its findings into the same changeset, or into PLAN item 3 if that lands first.
