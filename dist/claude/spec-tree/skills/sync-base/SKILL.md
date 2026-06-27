---
name: sync-base
description: >-
  ALWAYS invoke this skill to bring a branch behind its base current — before reading product truth, before verifying, and before every merge push. NEVER rebase a behind-base branch by hand or bring it current with git reset.
allowed-tools: Bash, Read
---

<objective>
The current branch brought current with its fetched base by a clean rebase.
</objective>

<workflow>

Run the synchronizer against the repository working tree (default: the current directory):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/sync_base.py" [repo] [--base <branch>]
```

It resolves the base ref and `origin/<base>` through the shared changeset-scope primitives, fetches the base, and rebases the branch when it is behind. The base defaults to `origin/HEAD`; pass `--base <branch>` when the changeset tracks a non-default base (a stacked pull request whose base is another feature branch). It prints a JSON result (`status`, `base_ref`, `remote_ref`, `branch`, `detail`, `preservation` on a clean outcome, and `conflict` on an active rebase conflict) and exits:

| `status`          | exit | meaning                                                                                                                                              | how Claude acts                                                                                                                                                             |
| ----------------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `already_current` | 0    | the branch is not behind the base                                                                                                                    | proceed                                                                                                                                                                     |
| `rebased`         | 0    | the branch was rebased onto `origin/<base>`                                                                                                          | proceed; re-run only the verification and review the base movement invalidated — `<readiness_preservation>` scopes which                                                    |
| `conflict`        | 3    | the rebase stopped with active conflict state; the result's `conflict` object names the conflicted paths, git facts, git conflict text, and options  | reconcile per `<conflict_reconciliation>`; stop for the operator only after deterministic evidence cannot decide product intent, leaving the rebase active                  |
| `dirty_tree`      | 4    | the branch is behind, but uncommitted changes to tracked files block the rebase; no rebase is attempted and the tree is left untouched               | resolve autonomously per `<dirty_tree_resolution>` — commit the changes to the right branch and re-run; never stash, never surface it as a conflict, never ask the operator |
| `git_failure`     | 1    | a diverged detached HEAD carrying its own commits, an unresolved base, or a failed fetch — a clean behind-base detached HEAD is advanced, not failed | report `detail`; do not rebase                                                                                                                                              |

A `dirty_tree` is Claude's to resolve, never the operator's: `<dirty_tree_resolution>` gives the step-by-step, and `<invalid_operator_escalations>` lists every base-sync stop that is Claude's rather than the operator's. sync-base itself never commits or stashes, so commit policy stays with `/commit-changes`.

Pass `--no-fetch` only when the remote-tracking ref is already current and a fetch would be redundant.

</workflow>

<dirty_tree_resolution>

A `dirty_tree` outcome means uncommitted tracked changes block the rebase — almost always a file Claude created earlier this session, not a content conflict. A coordination note (`PLAN.md` / `ISSUES.md`) Claude wrote is the canonical case. A dirty tree is never a reason to stop and ask the operator, and never a reason to stash — stash is forbidden, and committing is what clears the tree. Resolve it in place:

1. **Recognize the changes as Claude's.** Changes Claude made this session are Claude's to commit. (Operator work-in-progress Claude did not author is the one exception — see the read-only caller note below — and is still never a merge-conflict question to the operator.)
2. **Classify the change against the session's objective, then commit it through `/commit-changes`:**
   - **Related to the objective** → commit to the session's change branch. When the worktree is detached or sitting on the default branch, create the change branch from the current commit first — never commit the objective onto the default branch.
   - **An unrelated coordination note** — a `PLAN.md` / `ISSUES.md` recording future work that is not part of the objective → commit it onto its own local branch, and record in the imperfection ledger that the branch is pending `/merge`. At session end `/merge` routes a coordination-note-only changeset to the default branch on origin through its direct-push transport, exactly as the merge guidance prescribes for such a changeset.
3. **Re-run sync-base.** With the tree clean and the work carried on a branch, sync-base rebases (or advances) normally.

The branch routing above is the merge lifecycle's routing applied early — the same destinations `/merge` selects at session end.

**Read-only caller note.** `/contextualize` loads context read-only: on a `dirty_tree` outcome it surfaces that loaded context may be stale and proceeds, committing nothing — neither the operator's work-in-progress nor a file Claude created this session. The mutating caller that next runs sync-base (the merge lifecycle or `/pickup`) performs the commit per the steps above; this `/contextualize` dirty_tree outcome is the read-only caller's concern, not sync-base's, and is never a rebase conflict.

</dirty_tree_resolution>

<conflict_reconciliation>

A `conflict` outcome means a rebase is active. Do not abort it reflexively. Read the `conflict` object, inspect the repository state, and reconcile every conflict that deterministic evidence can decide:

1. Inspect:
   - `git status`
   - `git diff`
   - `git ls-files -u`
   - `git show :1:<path>`, `git show :2:<path>`, and `git show :3:<path>` for conflicted paths when stage contents are needed.
2. Classify each conflicted path by portable role, never by repository-local path names:
   - **source of truth** — the project-declared authoritative source for a behavior or derived artifact.
   - **generated artifact** — a file produced from source by a project-declared regeneration command.
   - **coordination note** — `PLAN.md`, `ISSUES.md`, session notes, or the project's declared equivalents.
   - **governance surface** — specs, decisions, review policy, merge policy, or project-declared control files.
   - **ordinary implementation or test** — code or evidence governed by the loaded spec node and decisions.
3. Resolve autonomously when evidence decides:
   - Version or manifest bumps choose the monotonic/latest valid value, then run the project's declared version or manifest validation.
   - Generated artifacts are resolved by resolving their source of truth first, then running the project-declared regeneration command. Never hand-merge generated output when regeneration is available.
   - Redundant edits keep the change that supersedes the other by product truth, branch chronology, or source contract; remove the redundant text rather than preserving both.
   - Nearby independent edits are combined when both are compatible with the loaded specs, decisions, and tests.
   - Coordination notes are reconciled to still-true facts; stale, duplicate, or superseded notes are removed or archived through the relevant session/note workflow.
4. After resolving a file, run `git add <resolved-paths>`.
5. Continue with `git rebase --continue`.
6. Run the narrowest deterministic verification the project overlay declares for the resolved paths; fall back to the full deterministic gate when the overlay cannot classify the paths.

Stop for the operator only when the remaining conflict is a product-intent conflict: specs, decisions, tests, newer session state, and git facts do not choose which behavior should survive. The human-facing report must say `Base sync stopped: rebase conflict requires reconciliation`, list conflicted paths, summarize every attempted reconciliation class, explain why evidence did not decide, and present the exact manual options from the `conflict.operator_options` list. Leave the rebase active. The operator can inspect, resolve and continue, or run `git rebase --abort`.

</conflict_reconciliation>

<git_command_policy>

Allowed commands:

- Read state: `git status`, `git rev-parse`, `git symbolic-ref --short HEAD`, `git merge-base`, `git rev-list`, `git diff --name-only`, `git diff`, `git ls-files -u`, `git show :1:<path>`, `git show :2:<path>`, `git show :3:<path>`.
- Sync: `git fetch origin <base>`, `git rebase origin/<base>`.
- Resolve: edit files, run project-declared regeneration commands, `git add <resolved-paths>`, `git rebase --continue`.

Explicitly disallowed:

- `git reset --hard`, `git reset --merge`, or any `git reset` as a base-sync mechanism.
- `git stash`.
- `git checkout .` or `git restore .` to wipe conflict state.
- Blanket `git checkout --ours .` or `git checkout --theirs .`.
- Creating another worktree to escape the assigned one.
- Running `git rebase --abort` automatically at operator handoff. Offer it as an operator option instead.

Use `--ours` or `--theirs` only for a specific path after classification has already decided the product result. The checkout flag is the mechanical file update, never the decision.

</git_command_policy>

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
- No operator decision for a clean rebase — the only operator touch-point is a product-intent conflict that deterministic evidence cannot resolve, or a hard git failure.
- A dirty tree is a precondition, never a conflict — uncommitted tracked changes yield `dirty_tree`, cleared by committing, never by stashing and never surfaced as a conflict.
- A dirty tree from Claude's own session changes is Claude's to clear per `<dirty_tree_resolution>` — committed to the right branch and re-synced, never stashed and never escalated to the operator.
- sync-base only fetches and rebases — it never commits or stashes the working tree.
- A conflicted rebase remains active at operator handoff — Claude offers `git rebase --abort` as an option and does not run it automatically.
- One base derivation — the base ref and `origin/<base>` come from the changeset-scope primitives, never re-derived here.

</invariants>

<invalid_operator_escalations>

A base-sync stop reaches the operator for exactly one reason: a product-intent conflict the rebase cannot resolve autonomously, or a hard git failure that leaves no autonomous path (a diverged detached HEAD carrying its own commits, an unresolved base, a failed fetch). Every other stop is Claude's to resolve. None of the following is a valid reason to ask the operator:

- A dirty tree from a file Claude created this session — commit it per `<dirty_tree_resolution>` and re-run.
- A coordination note (`PLAN.md` / `ISSUES.md`) Claude wrote that now makes the tree dirty — commit it to its own branch, record the pending `/merge` in the imperfection ledger, and re-run.
- A conflict in a coordination note where one side is stale or superseded — reconcile the note to still-true facts and continue the rebase.
- A conflict in a generated artifact whose source of truth can be resolved — resolve the source, regenerate through the project-declared command, and continue the rebase.
- A version bump conflict with an objectively monotonic/latest valid value — choose it, verify it, and continue the rebase.
- "Stash is forbidden, so the tree cannot be cleared" — committing clears it; the forbidden tool is not a blocker.
- A detached worktree with no branch to commit onto — create a local branch from the current commit and commit there.
- Uncertainty about which branch a change belongs on — objective work goes on the change branch, an unrelated coordination note on its own branch routed by `/merge`.
- A clean behind-base detached HEAD — sync-base advances it to the base tip; it returns `rebased` / `already_current`, not a stop.

A product-intent conflict is the only thing on the other side. Name it precisely; resolve everything else.

</invalid_operator_escalations>

<success_criteria>

- A behind-base branch ends rebased onto `origin/<base>` with its own commits preserved, or stopped at an active rebase conflict with structured conflict details and operator options.
- A behind-base branch with uncommitted tracked changes ends reported as `dirty_tree` with the working tree untouched and no conflict details, leaving the caller to commit and re-run.
- A `dirty_tree` from Claude's own session changes ends committed to the correct branch — objective work to the change branch, an unrelated coordination note to its own branch pending `/merge` — and re-synced, never stashed and never surfaced to the operator.
- No `git reset` synchronizes a branch, no commit or stash clears a dirty tree from inside sync-base, and no automatic `git rebase --abort` erases conflict evidence at operator handoff.
- A clean rebase completes with no operator prompt.
- A clean outcome carries a `preservation` proof of git facts only — full OIDs, base delta, branch paths, overlap, patch identity — naming no lane and never satisfying a merge gate.

</success_criteria>
