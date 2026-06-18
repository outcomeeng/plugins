---
name: sync-base
description: >-
  ALWAYS invoke this skill to bring a branch behind its base current — before reading product truth, before verifying, and before every merge push. NEVER rebase a behind-base branch by hand or bring it current with git reset.
allowed-tools: Bash, Read
---

<objective>
Bring the current branch current with its fetched base by rebasing, so context loading reads current product truth, verification scopes against a current base, and a merge integrates onto the latest base. The mechanism is rebase, never `git reset`: rebase replays the branch's own commits onto the advanced base; reset repoints the branch while leaving the working tree at the old base, silently reverting merged work. A clean rebase runs with no operator interaction; a conflict that cannot be resolved autonomously surfaces the `SYNC_BASE` token and stops; uncommitted changes to tracked files yield `dirty_tree`, which the caller clears by committing and re-running.
</objective>

<workflow>

Run the synchronizer against the repository working tree (default: the current directory):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/sync_base.py" [repo] [--base <branch>]
```

It resolves the base ref and `origin/<base>` through the shared changeset-scope primitives, fetches the base, and rebases the branch when it is behind. The base defaults to `origin/HEAD`; pass `--base <branch>` when the changeset tracks a non-default base (a stacked pull request whose base is another feature branch). It prints a JSON result (`status`, `base_ref`, `remote_ref`, `branch`, `detail`, `action_token`, and `preservation` on a clean outcome) and exits:

| `status`          | exit | meaning                                                                                                                                                          | how Claude acts                                                                                                          |
| ----------------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `already_current` | 0    | the branch is not behind the base                                                                                                                                | proceed                                                                                                                  |
| `rebased`         | 0    | the branch was rebased onto `origin/<base>`                                                                                                                      | proceed; re-run only the verification and review the base movement invalidated — `<readiness_preservation>` scopes which |
| `conflict`        | 3    | the rebase conflicts; it is aborted with the branch and tree intact, and `action_token` is `SYNC_BASE`                                                           | stop and surface `SYNC_BASE` for the operator to resolve the conflict — never fall back to `git reset`                   |
| `dirty_tree`      | 4    | the branch is behind, but uncommitted changes to tracked files block the rebase; no rebase is attempted and the tree is left untouched; `action_token` is absent | commit the working changes through `/commit-changes`, then re-run sync-base — never stash, never surface `SYNC_BASE`     |
| `git_failure`     | 1    | detached HEAD, an unresolved base, or a failed fetch                                                                                                             | report `detail`; do not rebase                                                                                           |

Resolve `dirty_tree` autonomously rather than asking the operator: sync-base never commits or stashes on the caller's behalf, so commit policy stays with `/commit-changes`.

Pass `--no-fetch` only when the remote-tracking ref is already current and a fetch would be redundant.

</workflow>

<readiness_preservation>

On `rebased` or `already_current`, the result carries a `preservation` object so a caller can avoid re-running pre-push readiness work the base movement did not invalidate, rather than treating every rebase as invalidating everything:

- `old_base_oid`, `new_base_oid`, `old_head_oid`, `new_head_oid` — full OIDs before and after the sync.
- `base_delta_paths` — the files the base advanced over.
- `branch_paths_before`, `branch_paths_after` — the branch's own changed paths against the old and new base.
- `path_overlap` — base-delta paths the branch also changed.
- `branch_patch_changed` — whether the branch's patch identity differs across the sync.
- `branch_diff_unchanged` — the git-only reuse signal: the branch patch is unchanged and the base delta does not overlap the branch.

Read `branch_diff_unchanged` to consider a prior local review reusable — and **also** confirm, against the project's overlay, that no `base_delta_paths` entry is a governance surface the reviewer judges against. For deterministic verification, run the project overlay's narrowest lane covering `base_delta_paths`, falling back to the full gate when any path is unclassified or `path_overlap` is non-empty. The proof carries no lane name — lane mapping is the project overlay's.

The proof scopes pre-push local work only. It never satisfies a merge gate: current-head pull-request checks and the current-head CI review still decide `MERGE_READINESS` after the push.

</readiness_preservation>

<invariants>

- Rebase, never reset — a behind-base branch is brought current only by replaying its own commits onto `origin/<base>`.
- No operator decision for a clean rebase — the only operator touch-point is a `SYNC_BASE` conflict or a hard git failure.
- A dirty tree is a precondition, never a conflict — uncommitted tracked changes yield `dirty_tree`, cleared by committing, never by stashing and never surfaced as `SYNC_BASE`.
- sync-base only fetches and rebases — it never commits or stashes the working tree.
- One base derivation — the base ref and `origin/<base>` come from the changeset-scope primitives, never re-derived here.

</invariants>

<success_criteria>

- A behind-base branch ends rebased onto `origin/<base>` with its own commits preserved, or stopped at a `SYNC_BASE` conflict with the branch and working tree intact.
- A behind-base branch with uncommitted tracked changes ends reported as `dirty_tree` with the working tree untouched and no `SYNC_BASE` token, leaving the caller to commit and re-run.
- No `git reset` synchronizes a branch, and no commit or stash clears a dirty tree from inside sync-base.
- A clean rebase completes with no operator prompt.
- A clean outcome carries a `preservation` proof of git facts only — full OIDs, base delta, branch paths, overlap, patch identity — naming no lane and never satisfying a merge gate.

</success_criteria>
