# ISSUES — changeset-scope

## 1. Co-locate moved-function path coverage in this node (FOLLOW-UP)

`changeset_scope.py` owns `detect_current_branch` and `branch_slug`, but this
node's `test_changeset_scope.scenario.l1.py` does not exercise two of their
paths: `detect_current_branch` raising `DetachedHeadError` on detached HEAD,
and `branch_slug`'s `state_dir` collision-disambiguation suffix. Both paths
remain covered by `spx/21-spec-tree.enabler/68-auditing.enabler/tests/test_auditing.scenario.l1.py`
through the re-bound symbols, so behavior is verified — the gap is only that the
owning node does not co-locate the evidence.

Required handling: port the `DetachedHeadError` and `state_dir`-collision cases
into this node's scenario test (source-owned values from `changeset_scope`),
so the node that owns the functions owns their path coverage.

Surfaced by the local `reviewing-changes` review and confirmed by the
`test-evidence-auditor` (finding f-002, INFO) on `feat/changeset-scope`. The
language audit gates (`/auditing-python`, `/auditing-python-tests`,
`/auditing-tests`) ran on this branch and returned APPROVED; only this
coverage co-location remains.
