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

`src/plugins/spec-tree/skills/sync-base/scripts/sync_base.py` runs to 1344 lines
— base-ref and remote-tracking resolution, behind-base detection, the
attached-branch rebase and the detached-head advance, the dirty-tree
precondition, structured conflict reporting, the readiness-preservation
proof, and the stack record with its restack and topology derivation. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script
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
Carry the rebase-never-reset invariant, the stack record and restack contract
(`branch.<name>.stackPredecessor` and `branch.<name>.stackTip`, the predecessor
states, topology derivation, and the `--onto` replay), and the
untracked-collision gap above into the ported surface rather than leaving any
behind. Revisit when the capability publishes.

## The derivation rule's evidence is an identity probe with no violating case

`spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/sync-base.md` declares
`ALWAYS: the synchronization primitive resolves the base ref and its remote-tracking form through
the shared changeset-scope primitives, never re-implementing base, remote-tracking, or branch
derivation` as `[test]` evidence. The linked test proves the three re-exported names are the
canonical objects; it exercises no violating case, so a private re-derivation added elsewhere in
`src/plugins/spec-tree/skills/sync-base/scripts/sync_base.py` would leave the test green.

**Impact.** The compliance test rejects one class of violation (replacing the re-exports) and not
the other (a parallel derivation beside them). The re-implementation prohibition is also carried as
`[audit]` evidence by
`spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md`,
so the gap narrows the deterministic half only.

**Settlement condition.** An enforcement mechanism that scans the shipped script for base-ref,
remote-tracking, or branch derivation outside the import seam, exercised against a violating
source fixture, replaces or joins the identity probe. That mechanism is a separate detection
concern with its own fixture design, not a bounded edit to the current evidence.

Surfaced by the test-evidence audit on head `7fab40984c8e47aabb1e8f357746a1868bff1a90`.
