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

## Synchronizer extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/sync-base/scripts/sync_base.py` runs to 785 lines
— base-ref and remote-tracking resolution, behind-base detection, the
attached-branch rebase and the detached-head advance, the dirty-tree
precondition, structured conflict reporting, and the readiness-preservation
proof. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script
debt whose logic moves into the SPX CLI once the script proves its value; the
synchronizer has proven its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository.

**Resolution shape**: port base movement, conflict structuring, and the
preservation proof into the SPX CLI, publish it, advance the floor, and reduce
the shipped skill to its instruction with no script. The derivation this script
shares with its siblings extracts with the primitives tracked in
`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/ISSUES.md`.
Carry the rebase-never-reset invariant and the untracked-collision gap above
into the ported surface rather than leaving either behind. Revisit when the
capability publishes.
