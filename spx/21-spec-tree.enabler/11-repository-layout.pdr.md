# Repository Layout

A product checkout governed by the Spec Tree methodology conforms to one of two git layouts: a single working tree, or a bare-repository worktree pool. The pool is a bare `{repo}.git` repository whose git-common-dir has, as siblings, a **main checkout** and the shared `.spx/` operational directory. The main checkout is the working tree whose directory basename equals the `origin` remote's repository name (`<pool>/<repo-name>`, e.g. `spx/spx`), placed beside the git-common-dir, with `git config --get core.bare` on the common dir selecting the pool layout — the main checkout is designated by the repository name and its sibling placement, independent of the checked-out or default branch. Provisioning sets the main checkout to track the git-resolved default branch `origin/<default>`, never a literal `origin/main`; classifying an existing pool reads the repository name, sibling placement, and bareness only, and does not re-verify the tracking ref. Additional pool worktrees are created detached at the `origin/<default>` tip and default to siblings of the git-common-dir, though their location is otherwise free. A pool whose git-common-dir has no sibling worktree named for the repository has no main checkout — the expected path stays derivable from the repository name for diagnostics and never falls back to a branch-named directory. A checkout that attaches linked worktrees to a non-bare repository, or a pool that lacks the bare root, the repository-name main checkout sibling, or `.spx/` beside the git-common-dir, is non-compliant.

## Rationale

The bare-repository pool is the only multi-worktree form that keeps the default branch unattached and claimable by any worktree while every worktree resolves one shared `.spx/` beside the git-common-dir — the topology the session, review, and merge workflows require; a single working tree stays compliant so a checkout that never runs concurrent worktrees pays none of the pool's setup. Designating the main checkout by the `origin` repository name and sibling placement, not by the default branch, gives a developer working across repositories a distinct `<repo>/<repo>` location per product rather than every product's main checkout sitting in an identically named `main/`, and keeps the designation branch-agnostic so a product whose default branch is `trunk` provisions and classifies identically to one defaulting to `main`. The default branch is resolved from git only where a branch ref is genuinely needed — the ref the main checkout tracks and the tip new worktrees detach at — so the layout authority and the session and worktree workflows agree on one git-resolved default rather than a hardcoded `main`.

## Product properties

1. Two layouts conform: a single working tree, and a bare-repository pool whose git-common-dir carries the repository-name main checkout and `.spx/` as siblings.
2. The main checkout is the sibling worktree whose basename equals the origin repository name, designated for classification by that name plus sibling placement plus the common dir's bareness, independent of branch and of what it tracks. Provisioning sets the main checkout to track the git-resolved default branch `origin/<default>` and creates additional worktrees detached at the `origin/<default>` tip; classification does not re-verify the tracking ref. A pool worktree's location is free and defaults to a sibling of the git-common-dir.
3. `.spx/` resolves to the one directory beside the git-common-dir from every worktree in the pool, so sessions, reviews, and audit state are shared across the pool.
4. A pool with no sibling worktree named for the repository has no main checkout; the expected path is derived from the repository name for diagnostics, never a branch-named directory.

## Verification

### Testing

- ALWAYS: a checkout whose only working tree is the repository root, with no linked worktrees, classifies as a compliant single-working-tree layout ([mapping])
- ALWAYS: a bare `{repo}.git` repository whose sibling main checkout's basename equals the origin repository name, with `.spx/` beside the git-common-dir, classifies as a compliant pool layout independent of the branch checked out in that worktree ([mapping])
- ALWAYS: from every worktree in a pool, the resolved `.spx/` path is the directory beside the git-common-dir ([property])
- Given a request to provision the pool for `{repo}`, when `init-worktrees` completes, then the main checkout sits at the repository-name sibling tracking the git-resolved default branch `origin/<default>`, and additional worktrees are detached at the `origin/<default>` tip ([scenario])
- Given a prior non-bare checkout carrying `.spx/`, when `init-worktrees` provisions the pool, then `.spx/` sits beside the new git-common-dir with its contents preserved byte-for-byte ([scenario])
- NEVER: a checkout that attaches one or more linked worktrees to a non-bare repository classifies as compliant ([mapping])
- NEVER: a bare-repository pool that lacks a sibling worktree named for the repository, or places `.spx/` anywhere other than beside the git-common-dir, classifies as compliant ([mapping])

### Audit

- ALWAYS: provisioning that removes or replaces a prior checkout first confirms every commit and branch is present on the remote, and carries `.spx/` across as the only state not recoverable from the remote ([audit])
- ALWAYS: the two compliant layouts and the non-compliance boundary hold for any product governed by this methodology, independent of this marketplace's tooling and of which branch the product's default is ([audit])
- NEVER: delete a prior non-bare checkout's working tree before `.spx/` has been relocated beside the new git-common-dir and the remote presence of every branch is verified ([audit])
