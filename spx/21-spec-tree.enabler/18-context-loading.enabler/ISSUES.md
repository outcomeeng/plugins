# Issues — context loading

## `/contextualize` Step SYNC does not branch on the sync-base `dirty_tree` outcome

sync-base now returns a distinct `dirty_tree` status (exit 4) when a behind-base
branch has uncommitted changes to tracked files. `/contextualize` Step SYNC runs
sync-base before reading context — exactly when the working tree may be dirty —
but branches only on `already_current`, `rebased`, `conflict`, and `git_failure`.
Define the `dirty_tree` branch: commit through `/commit-changes` then re-run, or
proceed treating context as possibly stale. This is the scenario that motivated
the sync-base change.

Full context and the cross-consumer plan live in
`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/PLAN.md`.
