# Base Synchronization by Rebase

A branch behind its fetched base is brought current by rebasing the branch's own commits onto the remote-tracking base ref `origin/<base>`, never by resetting the branch pointer onto the base. Synchronization fetches the base, rebases only when the branch is behind it, and runs without operator interaction; the sole operator touch-point is a rebase conflict that cannot be resolved autonomously or a hard git failure, surfaced as the `SYNC_BASE` action token.

## Rationale

`git reset --hard origin/<base>` and `git reset --soft origin/<base>` repoint the branch to the advanced base while leaving the working tree at the old base, so the next commit silently reverts whatever the intervening merges changed, and `--hard` additionally discards uncommitted work. Rebase replays the branch's own commits onto the advanced base, preserving the branch's work while absorbing the base's movement. Composing the rebase target against the fetched `origin/<base>` through the shared `remote_tracking_ref` primitive fixes the target independent of a stale local ref, per `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md`.

Running synchronization without an operator prompt follows the product authority decided in `spx/15-merging.pdr.md`: a branch behind its base is rebased from observable git state, and the only base-sync operator touch-point is a conflict the agent cannot resolve autonomously. A routine, clean rebase is not an operator decision; surfacing one re-asks a question the product has already answered.

Rejected: `git reset` (either mode) as a synchronization mechanism — it advances the branch pointer while stranding the working tree at the old base, reverting merged work and, under `--hard`, destroying uncommitted changes; and a merge of the base into the branch — a merge commit pollutes the branch's own history, where rebase keeps the branch a clean sequence of its commits atop the current base.

## Verification

### Testing

- ALWAYS: base synchronization rebases the branch's commits onto the remote-tracking base ref `origin/<base>`, preserving those commits ([compliance])
- ALWAYS: base synchronization derives the base ref and its remote-tracking form through the shared changeset-scope primitives, never re-deriving them, per `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md` ([compliance])
- ALWAYS: a clean synchronization completes with no operator interaction; the only operator touch-point is an unresolvable rebase conflict or a hard git failure, surfaced as the `SYNC_BASE` action token, per `spx/15-merging.pdr.md` ([compliance])
- NEVER: base synchronization brings a behind-base branch current with `git reset` in any mode — the mechanism is rebase, which preserves the branch's commits ([compliance])
