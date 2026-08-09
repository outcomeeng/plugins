# Changelog — spec-tree plugin

Spec Tree methodology skills and agents: `/understand`, `/contextualize`, `/author`, `/decompose`, `/refactor`, `/align`, `/apply`, `/verify`, the audit family, and the merge lifecycle.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

A version missing below shipped without an entry. Read the gap as an absent entry, never as an absent release.

An entry is written by the changeset that ships the change. A later changeset adds one only for a release its own diff modifies or reverses, and names that release's commit — the entry is then checkable against the diff carrying it. The entry covers that commit whole, because checkability comes from naming a commit a reader can open rather than from matching lines; a commit large enough that this reaches unfamiliar content is a commit whose entry belongs to whoever shipped it. Any other backfill reconstructs what a release's consumers needed from commits and diffs alone, which produces a guess, and a guess in this file is indistinguishable from a record. A gap not reachable that way stays open.

## 0.88.7

### Removed

- **Branch cleanup no longer advances the checkout that holds the base branch.** 0.88.4 added a step that fast-forwarded that checkout after every merge, on every transport. It was the wrong home: the base checkout predates the changeset and outlives it, while cleanup removes only what the lifecycle created, and reaching it meant writing outside the assigned worktree — which the merge lifecycle otherwise never does. Advancing a base checkout mutates local environment state and publishes nothing, which is the boundary `DEPLOY` sits on, so it becomes a deploy action a repository declares in `spx/local/merging.md` under `DEPLOYMENT_READINESS`. The branch-state closeout record drops its base-checkout-refresh field with the step.

  **Migration.** From 0.88.4 through 0.88.6 this ran for every repository on every transport, with nothing to declare. It now runs only where a repository declares it, and `DEPLOY` is a no-op where none is declared — so a base checkout that was being advanced automatically will stay at its pre-merge commit, as it did before 0.88.4. A repository that wants the behavior declares it as a deploy action; one that never relied on it needs no change.

## 0.88.4

Recorded by 0.88.7, which reverses this release's base-checkout refresh. Shipped in commit `dbd7b429cdc3744f7288553d1be8a4e91b76ab40`.

### Changed

- **The default merge strategy is a merge commit.** `gh pr merge` defaults to `--merge` rather than `--rebase`; `--rebase` and `--squash` remain available through the overlay's merge-flag declaration. A merge commit keeps every branch commit reachable, so the merged tip is a true ancestor of the base and `git branch -d` alone proves the branch deletable. The rewriting strategies reach that proof only through the patch-equivalence fallback, which a multi-commit squash fails outright. A repository that declares its own merge flag sees no change.

## 0.88.2

### Fixed

- **A project with no test files yet no longer receives empty per-language sections.** Two spans of the router introduce per-language content while carrying no per-language block of their own: the `## Test Naming Convention` heading with its preamble, and the paragraph introducing the composed per-language audit-skill tables. A project whose spec tree holds no test file — every project before its first test — rendered both above nothing, since the same render dropped every table they announce. Both are now gated on at least one enabled language and omitted whole when none is. A project that already has test files sees no change.

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
