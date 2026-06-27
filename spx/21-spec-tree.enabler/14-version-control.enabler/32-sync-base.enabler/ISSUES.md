# Issues — sync-base

## An untracked file that collides with a base addition still maps to `conflict`

The dirty-tree precondition check excludes untracked files
(`git status --porcelain --untracked-files=no`), because an untracked file
generally does not block a rebase. One narrow case is an exception: when the
base advance adds a path the working tree already holds as an untracked file,
`git rebase` refuses to start to avoid overwriting it — the same "untracked
working tree file would be overwritten" guard `git checkout` applies.

In that case sync-base falls through to the rebase, the rebase exits non-zero
before replaying, and the existing mapping reports `conflict` with conflict
details. That is a precondition the caller clears (remove or commit the
colliding untracked file), not a content conflict to resolve — so the reported
outcome is imprecise, and the ADR's "untracked files do not block a rebase"
holds only for the non-colliding case.

Scope: narrow edge case, no regression — before the `dirty_tree` change this
same case also surfaced `conflict`. Resolving it needs a new detection step
(parse the rebase's pre-flight refusal, or pre-check the base diff against
untracked paths) distinct from the tracked-file dirty check, plus an ADR/spec
refinement of the untracked-file claim. Tracked rather than fixed in the
introducing change because it is a separable detection mechanism, not a bounded
edit to the current diff.
