# Changelog — contribute plugin

Contributions to repositories you do not control.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.1.0

### Added

- **`/open-parent-pr`** — opens one pull request against a repository you do not control, after resolving the base and head repositories and your permission, obtaining authorization in that turn, cutting the branch from the base repository's default branch, and running that repository's own declared checks.
- **`/manage-parent-pr`** — reads an open pull request's state once, verifies each review finding against the branch, appends the revision, and posts one comment stating what changed. The comment is the re-request; requesting a reviewer is a maintainer-side action a contributor's permission does not reach.
- **`/open-parent-issue`** — files one issue carrying tool versions, the base commit observed against, the exact command, and a negative control.
- **`/manage-parent-issue`** — reads a thread once and answers the maintainer's question with evidence.
- **`/sync-fork`** — brings a fork's default branch current with its parent's, distinguishing behind from diverged and never discarding commits.
- **`contribution-standards`** — the invariants every artifact obeys, loaded by the five workflow skills. It ships the target resolver those skills run before their first write.

### Requires

- `git`, the GitHub CLI (`gh`) authenticated, and a Python interpreter. No other plugin and no methodology CLI.
