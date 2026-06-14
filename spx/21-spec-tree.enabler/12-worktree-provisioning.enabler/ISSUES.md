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
  (`spx/15-worktree-management.pdr.md` in the `spx` product, now merged) designates
  the bare-pool "main checkout" by two signals that must agree — sibling placement
  beside the bare repository and `basename == the origin remote's repository name`
  (`<pool>/<repo-name>`, e.g. `spx/spx`) — with `git config --get core.bare`
  selecting the layout, independent of the checked-out or default branch. It is
  named for the repository, NOT the default branch, so that a developer working
  across repositories gets a distinct `project/project` location rather than every
  product's main checkout sitting in an identically named `main/`. `init_worktrees.py`
  instead provisions the main worktree at `container / "main"` (line 204) and
  identifies it by `branch == "main"` (line 138), expressing neither the
  repository-name directory nor the branch-agnostic designation the merged rule
  requires.

Impact: a product whose default branch is not `main` (for example `trunk`) cannot
be provisioned or classified as a compliant pool, even though its layout is
structurally identical. The layout authority and the session/worktree rules
disagree on the same concept.

Resolution (the directory-naming question the original note left open is now
settled by the merged `spx/15-worktree-management.pdr.md`):

- Designate and name the main checkout by the `origin` repository name, not the
  default branch. `provision` adds the main worktree at `container / <repo-name>`
  (e.g. `spx/spx`), not `container / "main"`; `probe`/`classify` identify it by
  sibling placement plus `basename == <origin repository name>` rather than
  `branch == "main"`, independent of the checked-out branch.
- Still resolve the default branch from git only where a branch ref is genuinely
  needed: the main worktree tracks `origin/<default>` (resolved from `origin/HEAD`),
  not a literal `origin/main`. Apply the same fix to the literal `main` /
  `origin/main` in `11-repository-layout.pdr.md` prose and assertions and
  `worktree-provisioning.md` assertions.
- Re-render `dist/` and update the `scripts/init_worktrees.py` tests accordingly.

Surfaced while defining the `spx` product's main-checkout detection and confirmed
by its now-merged `spx/15-worktree-management.pdr.md`: the bare-pool main checkout
is designated by two signals that must agree — `basename == <origin repository
name>` and sibling placement beside the bare repository, with `git config --get
core.bare` selecting the layout — branch-agnostic, which the hardcoded-`main`
classifier cannot express.
