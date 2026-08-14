# Issues

## The delta-only assertion has no cross-sibling enforcement gate

`test-verification.md` asserts that every language-specific test-standard node cites this node and `15-test-infrastructure.pdr.md` and declares only its language delta, never restating or weakening the seam rules this node owns ([audit]). No gate enforces that assertion across the sibling language nodes. The changeset reviewer (`spec-tree:changes-reviewer`), the per-language artifact auditors (`audit-{python,rust,typescript}-{tests,code,architecture}`), and `/align` each judge one node or one changeset in isolation; none compares `spx/43-python.enabler`, `spx/43-rust.enabler`, and `spx/43-typescript.enabler` against this superset or against each other. A future edit that restates a superset rule inside a language node, or lets two language nodes diverge, passes every gate — the same blind spot that let the pre-superset duplication reach the default branch unflagged.

**Resolution shape** (fix deferred by operator decision, to be scoped in the skill and agent specialization work): add cross-sibling equivalence detection to the gate set — an `/align` check that every language test-standard node cites this node and declares only deltas, an audit assertion on each language node verifying delta-only content against the cited superset, or a review dimension that compares sibling language standards.

**Evidence.** Named by the operator after observing that the seam specs of all three languages were extremely repetitive and that no auditor or changeset reviewer flagged the repetition across the changeset that carried it.

## Accepted adversarial-review findings against the merged evidence-types decision

An adversarial review of the merged PR #519 changeset (`988af420b503b010d85bda6e0afa3a748b5929b5..c42fceef6ef807429e7047d043e517b5e468df0d`), recorded at `.spx/reviews/2026-08-14-pr519-codex-adversarial.md` (pool-relative, beside the git common dir), produced nine findings, all judged valid. Five target the merged spec layer:

1. `l1` "repository-standard tools" versus `l2` "product-specific binaries" has no mutually exclusive discriminator — a repository's own CLI is undecidable between the levels, which the decision's own amendment rule makes an amendment obligation (`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md`).
2. The mapping/property construction-law clarification defines independence only against the production path, dropping the author-invention independence `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` requires — a parallel algorithm from the same mental model passes corpus cases 14, 15, and 37. Introduced by the merged changeset.
3. The canonical filename model's "default runner" has no declared owner; each language delta must declare or deterministically derive it.
4. "evidence type" survives where the taxonomy is "assertion type": the amended boundary sentence in `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` and two sites in `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/python-tests.md`.
5. Both language execution-level delta lines still enumerate the neutral `l1`/`l2`/`l3` category lists — restating rather than expressing (`spx/43-python.enabler/.../54-execution-level-guidance.enabler` and the TypeScript twin).

Four target the shipped test-skill families as renderings of the decision: the Python standards and auditor grant an `Any (fixture)` permission that approves fixture-backed Mapping and Property cells the decision forbids (fold into the Python rendering, PLAN item 5); the TypeScript family forbids every runner skip for credentialed tests, contradicting the decision's optional-evidence skip and the aligned TypeScript delta (fold into the TypeScript rendering, PLAN item 7); the TypeScript predicate-in-harness sites and the blanket binding ban are already owned by `spx/43-typescript.enabler/25-typescript-standards.enabler/PLAN.md` and get no second record here.

**Resolution shape**: one bounded spec changeset — amend the evidence-types decision (level discriminator plus boundary case, provenance-bound construction laws plus rejected case, default-runner obligation), replace the taxonomy word at its spec and skill sites, rewrite the two delta lines to language-specific realization only — with the two new skill-family findings folded into PLAN items 5 and 7, or into PLAN item 3 if that lands first.
