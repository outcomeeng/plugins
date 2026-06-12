# Marketplace Merge Rules

Loaded by `/standardizing-merging` `<repo_local_overlay>` when working in this repository, and by `/merge` for transport selection. Marketplace-specific overrides to the base merge flow.

## Transport selection

This repository uses the **GitHub-PR transport** by default — feature work, spec/decision/implementation/test/doc changes, and anything that needs review all ship as a pull request through `/github-pr`.

A **coordination-note-only changeset** — every changed path is a `PLAN.md` or `ISSUES.md` — routes to the **direct-push transport** automatically, per `/merge`'s classification and the marketplace guidance that node-local coordination files may be committed directly so collaborators see the coordination state immediately. There is no explicit `transport:` override; the changeset heuristic governs.

The sections below split into the per-transport blocks `/merge` and the lifecycle skills consume: **Production-relevance recognition**, **Merge command**, **Deterministic verification**, and **Mention-reviewer trigger phrase** configure the GitHub-PR transport; **Direct-push transport** configures the direct-push path; **Post-merge** applies to both.

## Production-relevance recognition

This repository declares **no** production-relevance recognition mechanism: every change is treated as not production-relevant, so `PRODUCTION_READINESS` holds by default and `MERGE_READINESS` holding is sufficient authority to merge autonomously. The marketplace ships methodology and plugin sources; a merge to `main` publishes the next marketplace version, which the post-merge sync step picks up — no per-PR human merge approval is required.

The agent merges the moment `MERGE_READINESS` holds and **NEVER asks the operator whether to merge, for merge approval, or whether to hold for human review** — there is no merge-approval decision for the operator to make in this repository, so surfacing one (through the runtime's structured-question tool or in prose) violates this overlay. The only operator-facing pauses in the whole flow are the explicit `<action_tokens>` an unresolved condition emits — an unresolvable rebase conflict (`SYNC_BASE`) or a mention-review edge case (`MENTION_REVIEW_NEEDED`) — never a discretionary "should I merge?".

## Merge command

Use a merge commit (preserves PR history; matches existing main):

```bash
gh pr merge <pr-number> --merge --delete-branch=false
git push origin --delete <branch>
gh pr view <pr-number> --json state,mergedAt,mergeCommit
```

`--delete-branch=false` is passed explicitly rather than omitted: omitting the flag relies on `gh`'s default for it, which varies by `gh` version and config and is unknowable across environments, and a host whose default is on (or whose repository auto-deletes head branches) makes `gh` run its local-cleanup phase, which fails under multi-worktree checkouts when `main` is already checked out in another worktree (the merge succeeds on the remote, but the post-merge `git checkout main` step errors with `fatal: 'main' is already used by worktree at '<path>'`). `=false` guarantees `gh` never attempts that step. Delete the remote branch separately with `git push origin --delete <branch>` (tolerating a host that already auto-deleted it), then verify with `gh pr view`.

## Deterministic verification

The marketplace's full deterministic-verification command is `just check`. It is the `REVIEW_READINESS` deterministic-verification predicate of `/standardizing-merging` `<authority_gates>`: run it (green) before opening the PR, and re-run it before any follow-up push and before any `--force-with-lease` push that follows a base-sync rebase.

## Mention-reviewer trigger phrase

`@spec-tree` (the value `.github/workflows/spec-tree-review.yml` configures via `trigger_phrase`, with `SPEC_TREE_REVIEW_TRIGGER_PHRASE` as the repository-variable override). The managing flow posts `@spec-tree review` as a PR-level comment when the `spec-tree-review / spec-tree-review` workflow reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file (GitHub Actions' identical-workflow-content gate), per `/standardizing-merging` `<authority_gates>` reviewer-skipped-by-design exception. Any other skip cause (path filter, branch filter, manual skip) emits `WAIT_FOR_REVIEW` and does not post the trigger phrase.

## Direct-push transport

A coordination-note-only changeset publishes straight to `main` with no pull request, per `/merge`'s transport classification and `spx/21-spec-tree.enabler/76-merging.enabler/32-direct-push.enabler/direct-push.md`. The three gates are unchanged; only the predicate bindings differ.

**Deterministic verification.** A coordination-note-only changeset touches only Markdown coordination notes, so the spec lane is sufficient: `spx validation markdown` and `spx spec status --format json` (per the [AGENTS.md spec-only validation rule](../../AGENTS.md)). The full `just check` is not required when no implementation, test, validation config, or generated catalog file changed.

**Review predicate.** No CI review exists on this path. The local `changes-reviewer` review (converged at `REVIEW_READINESS`) is the `MERGE_READINESS` review predicate. `PRODUCTION_READINESS` holds — this repository declares no production-relevance mechanism (above).

**Push command.** Once `REVIEW_READINESS` holds (spec-lane verification green and the local review converged), publish to trunk with the explicit destination ref:

```bash
git push origin HEAD:refs/heads/main
```

The agent never opens a PR and never waits on CI for this transport. Post-merge follows the section below; a coordination-note-only change touches no plugin distribution files, so `just sync-marketplace` exits without refreshing.

## Post-merge

After the merge lands on `main`, refresh the local marketplace install with `just sync-marketplace <previous-main-ref>` (the [CLAUDE.md sync step](../../CLAUDE.md)).

Update the current worktree to the merged `main` by **detaching**, never by attaching the branch:

```bash
git fetch origin main
git switch --detach origin/main
just sync-marketplace <previous-main-ref>
```

This repository is a multi-worktree checkout where `main` is kept checked out in no worktree so every worktree can reach it. `git switch main` attaches `main` to the current worktree and pins it there — a later `git switch main` in another worktree then fails with `fatal: 'main' is already used by worktree at <path>`, the same multi-worktree cleanup failure the separate `git push origin --delete <branch>` above already avoids. The `--detach` form lands HEAD on the merged commit without claiming the branch. The CLAUDE.md sync step carries the same detach form; this overlay is the authoritative source for the multi-worktree rationale.
