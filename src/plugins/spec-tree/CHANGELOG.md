# Changelog — spec-tree plugin

Spec Tree methodology skills and agents: `/understand`, `/contextualize`, `/author`, `/decompose`, `/refactor`, `/align`, `/apply`, `/verify`, the audit family, and the merge lifecycle.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

This plugin delivers the methodology but is versioned separately from it. What changed in the **methodology** is in `METHODOLOGY-CHANGELOG.md` beside this file — a methodology release keeps its identity regardless of which plugin version delivers it.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.87.2

### Changed

- **Merge cleanup recognizes rebase-merged local branches as merged.** The close-phase branch cleanup deletes a local feature branch whose remote ref is absent, which no live worktree checks out, and whose work is fully upstream — its tip an ancestor of the fetched base, or every branch commit patch-equivalent to an upstream commit (a successful `git cherry` reporting no `+` commit, the state a rebase merge or single-commit squash leaves behind). Previously the merged-proof was ancestry only, so every rebase-merged branch was retained. The patch-equivalence path deletes with `git branch -D` because `-d` re-checks ancestry; a branch carrying any unmatched commit, a multi-commit squash, or a `git cherry` invocation that fails keeps the branch retained with its evidence.

## 0.87.1

### Changed

- **`/handoff` closeout reports only operator-actionable session mechanics.** The propose and execute workflows drop internal bookkeeping from the operator-facing closeout.

## 0.87.0

### Changed

- **`[review]` is no longer tolerated as a spelling of `[audit]`.** The foundation described it as the legacy spelling of the `[audit]` assertion tag. That description is gone: the assertion tags are `[test]`, `[eval]`, and `[audit]`, and review is an open-ended changeset gate that backs no assertion tag. An assertion still carrying `([review])` now reports an invalid tag under `/audit-specs`, and `/audit-tests` no longer lists it among the tags it skips. Migrate `([review])` to `([audit])` — the assertion text is unchanged, only the tag spelling.

  This enforces a rule methodology 3.1.0 already states rather than introducing one, so no artifact that was valid becomes invalid: review has backed no assertion tag since that release, and the tolerance was a delivery lag behind it. A spec carrying `([review])` was already outside the tag vocabulary; from this version an audit reaching one says so. `METHODOLOGY-CHANGELOG.md` records the rule; this line records where enforcement begins.

### Added

- **`help` names where the changelogs are.** The lifecycle skill's `help` verb reports the marketplace, plugin, and methodology changelog paths. Each is read from disk, without network access.
- **`METHODOLOGY-CHANGELOG.md` ships beside this file.** What changed in the **methodology** is recorded separately from what changed in this plugin, because a methodology release keeps its identity regardless of which plugin version delivers it.

This changelog begins here; earlier history predates the line.
