# Marketplace Merge Rules

Loaded by `/standardizing-merging` `<repo_local_overlay>` when working in this repository. Marketplace-specific overrides to the base merge flow.

## Merge authority

This repository follows the autonomous-merge default from `/managing-pr` `<merge_gate>`. When all gate conditions hold (no `BLOCKING` or `NEEDS-ANSWER` work, terminal-green checks, five-minute review window elapsed, branch rebased onto current base, ready PR), the agent merges immediately using the command in `## Merge command` below — no separate explicit human merge instruction is required.

## Merge command

Use a merge commit (preserves PR history; matches existing main):

```bash
gh pr merge <pr-number> --merge
git push origin --delete <branch>
gh pr view <pr-number> --json state,mergedAt,mergeCommit
```

`--delete-branch` is omitted because `gh pr merge` fails its local-cleanup phase under multi-worktree checkouts when `main` is already checked out in another worktree (the merge succeeds on the remote, but the post-merge `git checkout main` step errors with `fatal: 'main' is already used by worktree at '<path>'`). Delete the remote branch separately with `git push origin --delete <branch>`, then verify with `gh pr view`.

## Closure gate

The marketplace's closure gate is `just check`. Run it before any draft → ready promotion per `/standardizing-merging` `<draft_lifecycle>` rule 3 and before any merge authorization request.

## Post-merge

After the merge lands on `main`, refresh the local marketplace install per the [CLAUDE.md sync step](../../CLAUDE.md): `git switch main && git pull && just sync-marketplace <previous-main-ref>`.
