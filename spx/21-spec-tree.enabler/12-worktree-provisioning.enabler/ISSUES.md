# Issues: Worktree Provisioning Enabler

## Repository-layout decision hardcodes `main` instead of resolving the default branch

`spx/21-spec-tree.enabler/11-repository-layout.pdr.md`, this enabler's spec, and
the `init_worktrees.py` classifier all hardcode the default branch as the literal
`main` and the tracking ref as the literal `origin/main`:

- `11-repository-layout.pdr.md` prose names "a `main` worktree tracking
  `origin/main`" and the `[mapping]` assertions repeat the literal `main` /
  `origin/main` (the `single`/`pool`/`non-compliant` rows).
- `worktree-provisioning.md` assertions name "a sibling `main` worktree tracks
  `origin/main`".
- `init_worktrees.py` `probe` identifies the main worktree by `branch == "main"`
  (line 138) and `upstream == "origin/main"` (line 148) — both literals — and
  `provision` adds the worktree at `container / "main"` tracking `origin/main`.

This contradicts the rest of the methodology, which resolves the default branch
from git so the rule holds for products whose default is not `main`:

- The spec-tree session frontmatter rule (in the consuming `spx` product,
  `spx/36-session.enabler/11-session-frontmatter.pdr.md`) states the default
  branch is resolved from git "so the rule holds for products whose default is
  not `main`".
- The `spx` product mandates resolving the product root via `git rev-parse`
  rather than a hardcoded branch name.
- A consuming product's worktree-management decision
  (`spx/15-worktree-management.pdr.md` in the `spx` product) defines the canonical
  "main checkout" as the worktree on the git-resolved default branch
  (`origin/HEAD`), whose directory basename equals that branch name, sited at the
  non-bare root or as a sibling of the bare repository — all three required. A
  product whose default is `trunk` has a valid main checkout under that rule but
  is classified non-compliant by `init_worktrees.py`.

Impact: a product whose default branch is not `main` (for example `trunk`) cannot
be provisioned or classified as a compliant pool, even though its layout is
structurally identical. The layout authority and the session/worktree rules
disagree on the same concept.

Resolution: resolve the default branch from git (`origin/HEAD`) throughout —
`11-repository-layout.pdr.md` prose and assertions, `worktree-provisioning.md`
assertions, and `init_worktrees.py` (`probe` keys on the resolved default branch
and its `origin/<default>` upstream; `provision` adds the worktree named for and
tracking the resolved default). Re-render `dist/` and update the
`scripts/init_worktrees.py` tests accordingly. Decide whether the worktree
directory is always named for the default branch (so `trunk`'s worktree is
`trunk/`) or stays a free name — the consuming worktree-management rule keys on
`basename == default branch name`, so a fixed `main/` directory name would break
a `trunk`-default product even after the branch resolution is fixed.

Surfaced while defining the `spx` product's main-checkout detection: the operator
chose git-resolved `origin/HEAD` with all three signals (branch, directory name,
bare/non-bare placement) required to agree, which the hardcoded-`main` classifier
cannot express.
