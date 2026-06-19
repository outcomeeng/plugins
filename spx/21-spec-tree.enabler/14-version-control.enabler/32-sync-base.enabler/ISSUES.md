# Issues — sync-base

## An untracked file that collides with a base addition still maps to `conflict`

The dirty-tree precondition check excludes untracked files
(`git status --porcelain --untracked-files=no`), because an untracked file
generally does not block a rebase. One narrow case is an exception: when the
base advance adds a path the working tree already holds as an untracked file,
`git rebase` refuses to start to avoid overwriting it — the same "untracked
working tree file would be overwritten" guard `git checkout` applies.

In that case sync-base falls through to the rebase, the rebase exits non-zero
before replaying, and the existing mapping reports `conflict`/`SYNC_BASE`. That
is a precondition the caller clears (remove or commit the colliding untracked
file), not a content conflict to resolve — so the reported outcome is
imprecise, and the ADR's "untracked files do not block a rebase" holds only for
the non-colliding case.

Scope: narrow edge case, no regression — before the `dirty_tree` change this
same case also surfaced `conflict`. Resolving it needs a new detection step
(parse the rebase's pre-flight refusal, or pre-check the base diff against
untracked paths) distinct from the tracked-file dirty check, plus an ADR/spec
refinement of the untracked-file claim. Tracked rather than fixed in the
introducing change because it is a separable detection mechanism, not a bounded
edit to the current diff.

## A detached HEAD behind the base is waved through as "not applicable" instead of brought current

`sync_base.py` returns `git_failure` with detail `detached HEAD: no branch to
rebase` whenever the worktree is detached, and `/contextualize`'s SYNC step and
`/pickup`'s checkout treat that outcome as "not applicable — proceed." The
common case the rule was written for is a pool worktree parked detached at the
default-branch tip, which is genuinely current. But a detached worktree can also
sit at a commit that is **behind** `origin/<default>`: a stale checkout, or a
worktree fast-forwarded earlier in a long session while the remote advanced.
Nothing checks. Context then loads from a stale base — superseded specs and
decisions — and any work built on it is built on the wrong foundation, surfacing
only at merge time as a heavy rebase against a base that moved underneath the
whole change. This is the exact failure mode that produced a stale-base
changeset in the session that wired the SessionStart hook to the spx hook
runner.

Fix: on a detached HEAD, before reporting `git_failure`, fetch `origin/<default>`
and compare. When the detached commit is an ancestor of `origin/<default>`
(behind) and the tree is clean, advance the worktree to the current tip
(`git switch --detach origin/<default>`) and report `rebased`/`already_current`
as appropriate; when behind but dirty, report `dirty_tree` (the caller commits
then re-syncs); only when there is no resolvable remote default does the
detached case stay a true `git_failure`. `/contextualize`'s SYNC step and
`/pickup`'s checkout then act on the advanced state rather than proceeding on a
stale commit. A no-remote or genuinely-current detached HEAD must still proceed
without blocking — the fix narrows "proceed" to the current case, it does not
turn a non-rebasable checkout into a merge gate.

Scope: a behavior change to `sync_base.py` plus the governing sync-base spec and
its tests, with aligned wording in `/contextualize`'s SYNC step
(`spx/21-spec-tree.enabler/18-context-loading.enabler`) and `/pickup`'s checkout
(`spx/21-spec-tree.enabler/76-sessions.enabler`). Needs the test-evidence and
skill auditor gates. Tracked rather than rushed at the end of the hook-runner
session because it is a core-skill change that must not ship half-audited.
