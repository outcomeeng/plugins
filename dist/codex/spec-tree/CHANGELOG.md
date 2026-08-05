# Changelog — spec-tree plugin

Spec Tree methodology skills and agents: `/understand`, `/contextualize`, `/author`, `/decompose`, `/refactor`, `/align`, `/apply`, `/verify`, the audit family, and the merge lifecycle.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.88.1

### Added

- **A root instruction file that only points at the other one is detected and resolved by answer, not by guess.** A repository whose `AGENTS.md` says little more than "see the other root instruction file" previously read as divergence: the two bodies shared almost nothing, so nothing was wrapped as a `shared` region and each file kept its own harness's router under a pointer to the other file's differently rendered one — sending a reader to the wrong harness's instructions. `/update-instruction-block` now reports such a file as a delegation candidate and holds the surface `stale` until the operator names the side both files take. Candidacy is decided from two facts about the file — the body names the other root instruction file, and its text stays within an absolute character bound — never from a reading of what the prose means, because adoption replaces a whole body and a wrong guess costs that file its instructions.

- **`--adopt {claude|codex}` applies that answer.** It requires `--write`, and it refuses four answers it cannot apply, each exiting nonzero and leaving both root files untouched: naming a side whose own body is a pointer, discarding a body carrying content of its own, arriving after the bootstrap pass has closed, and arriving with no write to apply it.

### Changed

- **The router block gained two sections, so they land in both root instruction files on the next run.** `### Agent identity in generated artifacts` bans naming the agent or its runtime in an operational artifact — a branch name, commit message, pull-request title or body, review comment, or authorship marker — while explicitly exempting instruction content that documents agent behavior as its subject. `### Operator questions` requires an operator question to go through the harness's structured-question tool rather than free-text prose, and reserves it for an answer that changes what happens next.

- **The five ambiguity reports read the same way.** Each now carries the same Detected/Recommend/Apply shape instead of five differing prose forms.

## 0.88.0

### Added

- `MARKETPLACE-CHANGELOG.md`, previously shipped in every plugin

### Removed

- `METHODOLOGY-CHANGELOG.md`
- `Skill` from the lifecycle skill's `allowed-tools`

### Changed

- `help` reports two changelogs instead of three

## 0.87.2

### Changed

- **Merge cleanup recognizes rebase-merged local branches as merged.** The close-phase branch cleanup deletes a local feature branch whose remote ref is absent, which no live worktree checks out, and whose work is fully upstream — its tip an ancestor of the fetched base, or every branch commit patch-equivalent to an upstream commit (a successful `git cherry` reporting no `+` commit, the state a rebase merge or single-commit squash leaves behind). Previously the merged-proof was ancestry only, so every rebase-merged branch was retained. The patch-equivalence path deletes with `git branch -D` because `-d` re-checks ancestry; a branch carrying any unmatched commit, a multi-commit squash, or a `git cherry` invocation that fails keeps the branch retained with its evidence.

## 0.87.1

### Changed

- **`/handoff` closeout reports only operator-actionable session mechanics.** The propose and execute workflows drop internal bookkeeping from the operator-facing closeout.

## 0.87.0

### Changed

- **`[review]` is no longer tolerated as a spelling of `[audit]`.** The foundation described it as the legacy spelling of the `[audit]` assertion tag. That description is gone: the assertion tags are `[test]`, `[eval]`, and `[audit]`. An assertion still carrying `([review])` now reports an invalid tag under `/audit-specs`, and `/audit-tests` no longer lists it among the tags it skips. Migrate `([review])` to `([audit])` — the assertion text is unchanged, only the tag spelling.

  The tolerance was this plugin's own. An assertion carrying `([review])` is migration debt against the methodology version a repository declares, and resolving it to `([audit])` never made that artifact valid.

### Added

- **`help` names where the changelogs are.** The lifecycle skill's `help` verb reports this plugin's changelog and the marketplace changelog. Each is read from disk, without network access.

This changelog begins here; earlier history predates the line.
