---
id: 01a0ebba-5f5f-742b-b02e-ad53749f5da2
malleability: spec
---

# Changeset Scope

PROVIDES the canonical git-derived changeset primitives — branch identity, addressing slug, base-ref resolution, concrete commit-OID resolution, and merge-base diff scope
SO THAT implementation-audit orchestration, the review-changes skill, and base synchronization
CAN derive every changeset's branch, slug, base ref, head/base commit IDs, and changed-file set from one source rather than re-implementing or re-exporting git derivation across skills

## Assertions

### Test.Scenario: primitives

- [base-ref-detected](tests/test_changeset_scope.scenario.l1.py):
  - Given `refs/remotes/origin/HEAD` resolves
  - When `detect_base_ref` runs
  - Then it returns the bare base branch name configured there
- [base-ref-unset](tests/test_changeset_scope.scenario.l1.py):
  - Given `refs/remotes/origin/HEAD` is unset
  - When `detect_base_ref` runs
  - Then it raises `BaseRefNotConfiguredError`, and the committed-scope command reports the failure with a nonzero exit and no JSON result rather than guessing a consumer repository's default branch
- [remote-tracking-range](tests/test_changeset_scope.scenario.l1.py):
  - Given a bare base name
  - When `remote_tracking_ref` runs
  - Then it composes the remote-tracking ref `origin/<base>`, and `branch_scope` diffs the three-dot range `origin/<base>...HEAD`, returning the changed-file set since the merge base
- [stale-local-ref-ignored](tests/test_changeset_scope.scenario.l1.py):
  - Given a local branch ref that lags its remote-tracking ref
  - When the committed-scope command resolves `HEAD` or an explicit three-dot range against `origin/<base>`
  - Then it returns full endpoint identities, and the changed-file set excludes commits already merged into the base, so a stale local ref does not widen the scope
- [current-branch](tests/test_changeset_scope.scenario.l1.py):
  - Given a checkout on a named branch
  - When `detect_current_branch` runs
  - Then it returns that branch name, and on a detached HEAD it raises `DetachedHeadError` rather than returning the `HEAD` placeholder
- [commit-oid](tests/test_changeset_scope.scenario.l1.py):
  - Given a git ref that resolves to a commit
  - When `commit_oid` runs
  - Then it returns the full object ID of that commit, so journal run-state identity is stamped with concrete commit IDs rather than symbolic refs
- [slug-collision](tests/test_changeset_scope.scenario.l1.py):
  - Given a `state_dir` whose state file at the base-slug path records a different branch
  - When `branch_slug` runs
  - Then it returns the base slug with the deterministic `--<sha8>` collision suffix, and with no such state file it returns the bare base slug

### Test.Scenario: stale base

- [stale-head-refused](tests/test_stale_base.scenario.l1.py):
  - Given a branch whose head is behind the fetched `origin/<base>` tip
  - When the committed-scope command resolves `HEAD`
  - Then it exits with the stale-base code, emits no scope, and its diagnostic names the fetched tip, the merge base, and the count of base commits the head lacks
- [fetch-before-compare](tests/test_stale_base.scenario.l1.py):
  - Given a checkout whose local `origin/<base>` remote-tracking ref lags the remote while the head carries one feature commit past that local ref
  - When the committed-scope command resolves `HEAD`
  - Then it fetches before comparing, so the refusal names the remote's tip rather than the local ref
- [current-head-scoped](tests/test_stale_base.scenario.l1.py):
  - Given a head that descends from the fetched `origin/<base>` tip
  - When the committed-scope command resolves `HEAD`
  - Then it returns the scope whose base identity is that tip
- [symbolic-base-fetched](tests/test_stale_base.scenario.l1.py):
  - Given an explicit range whose base is the symbolic `origin/HEAD`, and a remote whose base has advanced
  - When the committed-scope command resolves the range
  - Then it fetches the configured base branch by refspec and refuses with the remote's tip, because a bare `git fetch origin HEAD` writes only `FETCH_HEAD`
- [local-base-exact](tests/test_stale_base.scenario.l1.py):
  - Given an explicit range whose base names a local ref that lags `origin/<base>`
  - When the committed-scope command resolves the range
  - Then it returns the scope whose base identity is that local ref's commit, not the remote's tip, with no refusal, because an explicit range is the caller's exact endpoint pair
- [local-base-unrefused](tests/test_stale_base.scenario.l1.py):
  - Given an explicit range whose base names a local ref the head does not descend from
  - When the committed-scope command resolves the range
  - Then it returns the scope whose base identity is that local ref's commit and applies no stale-base refusal, because the refusal reads only a git-derived or `origin/` base
- [head-before-fetch](tests/test_stale_base.scenario.l1.py):
  - Given `FETCH_HEAD` names a feature commit one commit past `origin/<base>`, and the base fetch rewrites `FETCH_HEAD` to the base tip
  - When the committed-scope command resolves `origin/<base>...FETCH_HEAD`
  - Then its head identity is the feature commit, and its changed-file set holds exactly the paths that commit changes

### Test.Mapping: [remediation](tests/test_changeset_scope_remediation.mapping.l1.py)

Each failure the primitives report maps to the error and the message its case names, so the operator learns the remedy from the message alone.

| Case              | Failure                                                      | Error and message                                                                                                                                                                                        |
| ----------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| origin-head-unset | `refs/remotes/origin/HEAD` is unset                          | `BaseRefNotConfiguredError`, naming the repository and the remedies `git remote set-head origin --auto` and `git remote set-head origin <branch>`                                                        |
| origin-head-shape | `refs/remotes/origin/HEAD` holds a value of unexpected shape | `BaseRefNotConfiguredError`, quoting the value, stating the expected `refs/remotes/origin/` prefix, and naming the remedy `git remote set-head origin --auto`                                            |
| detached-head     | a detached HEAD                                              | `DetachedHeadError`, naming the repository and the remedies `git switch <branch>` and `git switch -c <new-branch>`                                                                                       |
| silent-git        | a git failure with empty stderr during selector resolution   | `ScopeResolutionError`, naming the failed command and its exit status, and directing the operator to verify each ref with `git rev-parse --verify <ref>` and to confirm that `git fetch origin` succeeds |
| git-stderr        | a git failure with stderr during selector resolution         | `ScopeResolutionError`, carrying that stderr                                                                                                                                                             |

### Test.Compliance: refusal and head identity

- [classifier-unrefused](tests/test_stale_base.compliance.l1.py): ALWAYS: the merge classifier resolves a branch behind the fetched `origin/<base>` tip to its changed paths without the stale-base refusal, because classification partitions paths rather than verifying them
- [sync-unrefused](tests/test_stale_base.compliance.l1.py): ALWAYS: base synchronization resolves a branch behind the fetched `origin/<base>` tip through the primitives without the stale-base refusal and rebases it, because it is the refusal's remedy
- [head-resolved-first](tests/test_stale_base.compliance.l1.py): ALWAYS: resolving a committed selector resolves its head to a full commit id before any fetch, and the stale-base comparison and the changed-file set read only that id, so a fetch that rewrites `FETCH_HEAD` or a remote-tracking ref moves no head
