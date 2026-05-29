# Marketplace Merge Rules

Loaded by `/standardizing-merging` `<repo_local_overlay>` when working in this repository. Marketplace-specific overrides to the base merge flow.

## Production-relevance recognition

This repository declares **no** production-relevance recognition mechanism: every change is treated as not production-relevant, so `PRODUCTION_READINESS` holds by default and `MERGE_READINESS` holding is sufficient authority to merge autonomously. The marketplace ships methodology and plugin sources; a merge to `main` publishes the next marketplace version, which the post-merge sync step picks up — no per-PR human merge approval is required.

## Merge command

Use a merge commit (preserves PR history; matches existing main):

```bash
gh pr merge <pr-number> --merge
git push origin --delete <branch>
gh pr view <pr-number> --json state,mergedAt,mergeCommit
```

`--delete-branch` is omitted because `gh pr merge` fails its local-cleanup phase under multi-worktree checkouts when `main` is already checked out in another worktree (the merge succeeds on the remote, but the post-merge `git checkout main` step errors with `fatal: 'main' is already used by worktree at '<path>'`). Delete the remote branch separately with `git push origin --delete <branch>`, then verify with `gh pr view`.

## Deterministic verification

The marketplace's full deterministic-verification command is `just check`. It is the `REVIEW_READINESS` deterministic-verification predicate of `/standardizing-merging` `<authority_gates>`: run it (green) before opening the PR, and re-run it before any follow-up push and before any `--force-with-lease` push that follows a base-sync rebase.

## Mention-reviewer trigger phrase

`@spec-tree` (the value `.github/workflows/spec-tree-review.yml` configures via `trigger_phrase`, with `SPEC_TREE_REVIEW_TRIGGER_PHRASE` as the repository-variable override). The managing flow posts `@spec-tree review` as a PR-level comment when the `spec-tree-review / spec-tree-review` workflow reports `conclusion: skipped` per `/standardizing-merging` `<authority_gates>` reviewer-skipped-by-design exception.

## Post-merge

After the merge lands on `main`, refresh the local marketplace install with `just sync-marketplace <previous-main-ref>` (the [CLAUDE.md sync step](../../CLAUDE.md)).

Update the current worktree to the merged `main` by **detaching**, never by attaching the branch:

```bash
git fetch origin main
git switch --detach origin/main
just sync-marketplace <previous-main-ref>
```

This repository is a multi-worktree checkout where `main` is kept checked out in no worktree so every worktree can reach it. `git switch main` attaches `main` to the current worktree and pins it there — a later `git switch main` in another worktree then fails with `fatal: 'main' is already used by worktree at <path>`, the same multi-worktree cleanup failure the separate `git push origin --delete <branch>` above already avoids. The `--detach` form lands HEAD on the merged commit without claiming the branch. The CLAUDE.md sync step carries the same detach form; this overlay is the authoritative source for the multi-worktree rationale.
