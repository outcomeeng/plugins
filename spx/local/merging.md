# Marketplace Merge Rules

Loaded by `/standardizing-merging` `<repo_local_overlay>` when working in this repository. Marketplace-specific overrides to the base merge flow.

## Merge authority

This repository follows the gate-green-autonomous default for both promotion and merge from `/standardizing-merging` `<pr_authority_gate>`. When the gate's predicates hold for the applicable action (closure gate passed, required checks terminal-green, current-head four-class review with no `BLOCKING` or `NEEDS-ANSWER`, five-minute settle window elapsed, branch hygiene including upstream-safety, no production-class markers, plus the merge-only predicates for merge), the agent runs the action's command immediately using the command in `## Merge command` below — no separate explicit human instruction is required for promotion or merge.

## Merge command

Use a merge commit (preserves PR history; matches existing main):

```bash
gh pr merge <pr-number> --merge
git push origin --delete <branch>
gh pr view <pr-number> --json state,mergedAt,mergeCommit
```

`--delete-branch` is omitted because `gh pr merge` fails its local-cleanup phase under multi-worktree checkouts when `main` is already checked out in another worktree (the merge succeeds on the remote, but the post-merge `git checkout main` step errors with `fatal: 'main' is already used by worktree at '<path>'`). Delete the remote branch separately with `git push origin --delete <branch>`, then verify with `gh pr view`.

## Closure gate

The marketplace's closure gate is `just check`. Run it before any push that approaches ready or merge; it is the project-specific closure-gate predicate of `/standardizing-merging` `<pr_authority_gate>` for both promotion-time and merge-time evaluation.

## Post-merge

After the merge lands on `main`, refresh the local marketplace install per the [CLAUDE.md sync step](../../CLAUDE.md): `git switch main && git pull && just sync-marketplace <previous-main-ref>`.
