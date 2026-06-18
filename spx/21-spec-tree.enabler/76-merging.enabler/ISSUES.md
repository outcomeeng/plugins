# Issues — merging

## The base-sync step does not branch on the sync-base `dirty_tree` outcome

sync-base now returns a distinct `dirty_tree` status (exit 4) when a behind-base
branch has uncommitted changes to tracked files. The base-sync step in
`/merging-standards`, `/manage-pr`, and `/merge` runs sync-base after a commit,
so a clean tree is the normal case; add an explicit `dirty_tree` branch anyway so
a dirty tree is committed-then-re-synced rather than falling through an
unhandled status.

Full context and the cross-consumer plan live in
`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/PLAN.md`.
