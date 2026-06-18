# Plan — wire sync-base consumers to the `dirty_tree` outcome

The sync-base enabler emits a `dirty_tree` status (exit 4) for a behind-base
branch with uncommitted changes to tracked files. The consuming flows do not yet
branch on it — they enumerate `already_current`, `rebased`, `conflict`, and
`git_failure` only — so the new status reaches them without a defined handling
path. The primitive is correct and tested; the consumer wiring is downstream
work created by the new status.

Why this is a separate slice, not part of the sync-base change: each consumer
lives in its own node with its own spec and skill-audit gate, so the wiring is
multi-node work, not a bounded edit to this node's diff. The sync-base change
does not regress these consumers — before it, a dirty behind-base tree surfaced
a misleading `conflict`/`SYNC_BASE`; now it surfaces the accurate `dirty_tree`.

Downstream work, by consumer:

- `spx/21-spec-tree.enabler/18-context-loading.enabler` — `/contextualize` Step
  SYNC runs sync-base before reading context, when the working tree may be
  dirty. Define the `dirty_tree` branch: commit through `/commit-changes` then
  re-run, or proceed treating context as possibly stale. This is the scenario
  that motivated the primitive change.
- `spx/21-spec-tree.enabler/76-merging.enabler` — the base-sync step in
  `/merging-standards`, `/manage-pr`, and `/merge` runs sync-base after a commit,
  so a clean tree is expected; add an explicit `dirty_tree` branch anyway so a
  dirty tree is committed-then-re-synced rather than falling through.

Each consumer change aligns the consumer node's spec/assertions and re-runs the
skill auditor.
