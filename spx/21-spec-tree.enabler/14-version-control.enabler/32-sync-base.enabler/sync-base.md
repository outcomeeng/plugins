# Sync Base

PROVIDES automatic base synchronization — fetching a branch's base, detecting when the branch is behind it, and rebasing the branch onto the fetched base
SO THAT context loading, the merge lifecycle, and session pickup
CAN read product truth, verify, and integrate against a current base without re-deriving base operations or surfacing a routine rebase as an operator decision

## Assertions

### Scenarios

- Given a branch whose HEAD is behind its fetched base, when sync-base runs, then the branch's own commits are replayed onto `origin/<base>` and the changes already merged into the base are present in the working tree ([test](tests/test_sync_base.scenario.l1.py))
- Given a branch already current with its fetched base, when sync-base runs, then it performs no rebase and reports the branch already current ([test](tests/test_sync_base.scenario.l1.py))
- Given a rebase that conflicts and cannot be resolved autonomously, when sync-base runs, then it stops and emits the `SYNC_BASE` action token naming the conflict, leaving the branch's commits and the working tree intact rather than completing or discarding work ([test](tests/test_sync_base.scenario.l1.py))
- Given a base ref that does not resolve or a detached HEAD with no branch to rebase, when sync-base runs, then it reports a hard git failure rather than rebasing onto an unresolved target ([test](tests/test_sync_base.scenario.l1.py))
- Given a caller-supplied base branch name, when sync-base runs, then it synchronizes onto that base's remote-tracking ref `origin/<base>` rather than the `origin/HEAD` default — so a stacked changeset rebases onto its actual base ([test](tests/test_sync_base.scenario.l1.py))

### Compliance

- ALWAYS: sync-base resolves the base ref and its remote-tracking form `origin/<base>` through the shared changeset-scope primitives, never re-implementing base, remote-tracking, or branch derivation ([test](tests/test_sync_base.compliance.l1.py))
- NEVER: sync-base brings a behind-base branch current with `git reset` in any mode — it rebases, preserving the branch's commits, per `spx/21-spec-tree.enabler/14-version-control.enabler/32-sync-base.enabler/13-base-sync-mechanism.adr.md` ([test](tests/test_sync_base.compliance.l1.py))
- NEVER: sync-base surfaces a routine behind-base rebase as an operator decision — the only operator touch-point is an unresolvable rebase conflict or a hard git failure, per `spx/15-merging.pdr.md` ([test](tests/test_sync_base.compliance.l1.py))
