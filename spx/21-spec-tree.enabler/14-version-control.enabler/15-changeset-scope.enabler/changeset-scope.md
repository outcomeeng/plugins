# Changeset Scope

PROVIDES the canonical git-derived changeset primitives — branch identity, addressing slug, base-ref resolution, concrete commit-OID resolution, and merge-base diff scope
SO THAT implementation-audit orchestration, the review-changes skill, and base synchronization
CAN derive every changeset's branch, slug, base ref, head/base commit IDs, and changed-file set from one source rather than re-implementing or re-exporting git derivation across skills

## Assertions

### Scenarios

- Given `refs/remotes/origin/HEAD` resolves, when `detect_base_ref` runs, then it returns the bare base branch name configured there ([test](tests/test_changeset_scope.scenario.l1.py))
- Given `refs/remotes/origin/HEAD` is unset, when `detect_base_ref` runs, then it raises `BaseRefNotConfiguredError` rather than guessing a consumer repository's default branch ([test](tests/test_changeset_scope.scenario.l1.py))
- Given a bare base name, when `remote_tracking_ref` runs, then it composes the remote-tracking ref `origin/<base>`, and `branch_scope` diffs the three-dot range `origin/<base>...HEAD` returning the changed-file set since the merge base ([test](tests/test_changeset_scope.scenario.l1.py))
- Given a local branch ref that lags its remote-tracking ref, when the changeset is scoped against `origin/<base>`, then the changed-file set excludes commits already merged into the base — a stale local ref does not widen the scope ([test](tests/test_changeset_scope.scenario.l1.py))
- Given a checkout on a named branch, when `detect_current_branch` runs, then it returns that branch name; on a detached HEAD it raises `DetachedHeadError` rather than returning the `HEAD` placeholder ([test](tests/test_changeset_scope.scenario.l1.py))
- Given a git ref that resolves to a commit, when `commit_oid` runs, then it returns the full object ID of that commit so journal run-state identity is stamped with concrete commit IDs rather than symbolic refs ([test](tests/test_changeset_scope.scenario.l1.py))
- Given a `state_dir` whose state file at the base-slug path records a different branch, when `branch_slug` runs, then it returns the base slug with the deterministic `--<sha8>` collision suffix; with no such state file it returns the bare base slug ([test](tests/test_changeset_scope.scenario.l1.py))
