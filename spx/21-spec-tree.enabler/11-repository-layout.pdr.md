# Repository Layout

A product checkout governed by the Spec Tree methodology conforms to one of two git layouts: a single working tree, or a bare-repository worktree pool. The pool is a bare `{repo}.git` repository whose git-common-dir has, as siblings, a `main` worktree tracking `origin/main` and the shared `.spx/` operational directory; additional pool worktrees are created detached at the `origin/main` tip and default to siblings of the git-common-dir, though their location is otherwise free. A checkout that attaches linked worktrees to a non-bare repository, or a pool that lacks the bare root, the `main` worktree sibling tracking `origin/main`, or `.spx/` beside the git-common-dir, is non-compliant.

## Rationale

The bare-repository pool is the only multi-worktree form that keeps `main` unattached and claimable by any worktree while every worktree resolves one shared `.spx/` beside the git-common-dir — the topology the session, review, and merge workflows require; a single working tree stays compliant so a checkout that never runs concurrent worktrees pays none of the pool's setup.

## Product properties

1. Two layouts conform: a single working tree, and a bare-repository pool whose git-common-dir carries the `main` worktree and `.spx/` as siblings.
2. In the pool, `main` tracks `origin/main` and additional worktrees are created detached at the `origin/main` tip; a pool worktree's location is free and defaults to a sibling of the git-common-dir.
3. `.spx/` resolves to the one directory beside the git-common-dir from every worktree in the pool, so sessions, reviews, and audit state are shared across the pool.

## Verification

### Testing

- ALWAYS: a checkout whose only working tree is the repository root, with no linked worktrees, classifies as a compliant single-working-tree layout ([mapping])
- ALWAYS: a bare `{repo}.git` repository with a `main` worktree sibling tracking `origin/main` and `.spx/` beside the git-common-dir classifies as a compliant pool layout ([mapping])
- ALWAYS: from every worktree in a pool, the resolved `.spx/` path is the directory beside the git-common-dir ([property])
- ALWAYS: provisioning the pool over a prior non-bare checkout relocates that checkout's `.spx/` to sit beside the new git-common-dir with its contents preserved byte-for-byte ([scenario])
- NEVER: a checkout that attaches one or more linked worktrees to a non-bare repository classifies as compliant ([mapping])
- NEVER: a bare-repository pool that lacks the `main` worktree sibling, lacks `main`-to-`origin/main` tracking, or places `.spx/` anywhere other than beside the git-common-dir classifies as compliant ([mapping])

### Audit

- ALWAYS: provisioning that removes or replaces a prior checkout first confirms every commit and branch is present on the remote, and carries `.spx/` across as the only state not recoverable from the remote ([audit])
- ALWAYS: the two compliant layouts and the non-compliance boundary hold for any product governed by this methodology, independent of this marketplace's tooling ([audit])
- NEVER: delete a prior non-bare checkout's working tree before `.spx/` has been relocated beside the new git-common-dir and the remote presence of every branch is verified ([audit])
