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

Resolving it needs a new detection step (parse the rebase's pre-flight refusal,
or pre-check the base diff against untracked paths) distinct from the
tracked-file dirty check, plus an ADR/spec refinement of the untracked-file
claim.

## Readiness-preservation evidence uses a noncanonical filename token

The readiness-preservation scenarios link
`tests/test_sync_base.preservation.l1.py`. `preservation` is outside the
canonical evidence vocabulary: scenario, mapping, conformance, property, and
compliance.

Reclassify the assertions through `/test`, rename the linked evidence file to
the selected canonical token, and rerun the node's deterministic and
test-evidence gates.
