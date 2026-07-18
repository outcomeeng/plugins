# Plan: publish source-owned changeset-scope evidence

PR #451 on `work/changeset-scope-fixture-manifest` is the first merge cycle because later review and audit work consumes the canonical branch, base, commit, slug, and changed-file derivation this node owns.

## Observable result

A review, audit, or merge workflow can derive an exact committed changeset from real Git state while the tests obtain repository topology from a source-owned fixture manifest and keep assertion outcomes in the executed test file.

## Remaining work

1. Reconcile the local repaired branch with current `origin/main` while preserving the branch patch.
2. Run the focused node tests and validation.
3. Run the test-evidence auditor, implementation auditor, and changeset reviewer on one clean committed head.
4. Run the terminal full deterministic gate when the current merge overlay requires it.
5. Push the exact reviewed head to PR #451, inspect all current-head review surfaces and checks, and merge through `/manage-pr`.
6. Complete branch cleanup and marketplace-source refresh before advancing the apply merge-cycle index.

## Revisit condition

Remove this plan after PR #451 reaches `origin/main`, cleanup and release handling complete, and the next merge cycle has recomputed its scope against that new base.
