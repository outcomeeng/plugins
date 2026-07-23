---
name: sync-base
description: >-
  ALWAYS invoke this skill to bring a branch behind its base current — before reading product truth, before verifying, and before every merge push. NEVER rebase a behind-base branch by hand or bring it current with git reset.
allowed-tools: Read, Edit, Skill, AskUserQuestion, Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/sync_base.py":*), Bash(git status:*), Bash(git rev-parse:*), Bash(git symbolic-ref:*), Bash(git branch:*), Bash(git switch -c:*), Bash(git merge-base:*), Bash(git rev-list:*), Bash(git diff:*), Bash(git ls-files:*), Bash(git show:*), Bash(git add:*), Bash(git rebase --continue:*)
---

<objective>
The current checkout brought current with its fetched base, with authorized dirty work checkpointed on its owning branch and detached-head safety preserved.
</objective>

<workflow>

Run the synchronizer against the repository working tree (default: the current directory):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/sync_base.py" [repo] [--base <branch>]
```

It resolves the base ref and `origin/<base>` through the shared changeset-scope primitives and fetches the base. When an attached branch is behind, it rebases the branch onto the fetched base. When a clean detached HEAD is an ancestor of the fetched base, it advances the worktree with `git switch --detach origin/<base>`; a detached HEAD carrying commits absent from the base fails without moving. The base defaults to `origin/HEAD`; pass `--base <branch>` when the changeset tracks a non-default base (a stacked pull request whose base is another feature branch). It prints a JSON result (`status`, `base_ref`, `remote_ref`, `branch`, `detail`, `preservation` on a clean outcome, and `conflict` on an active rebase conflict) and exits:

| `status`          | exit | meaning                                                                                                                                              | how Claude acts                                                                                                                                            |
| ----------------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `already_current` | 0    | the branch is not behind the base                                                                                                                    | proceed                                                                                                                                                    |
| `rebased`         | 0    | the branch was rebased onto `origin/<base>`                                                                                                          | proceed; use `<readiness_preservation>` to identify which verification and review evidence the base movement invalidated                                   |
| `conflict`        | 3    | the rebase stopped with active conflict state; the result's `conflict` object names the conflicted paths, git facts, git conflict text, and options  | reconcile per `<conflict_reconciliation>`; stop for the operator only after deterministic evidence cannot decide product intent, leaving the rebase active |
| `dirty_tree`      | 4    | the branch is behind, but uncommitted changes to tracked files block the rebase; no rebase is attempted and the tree is left untouched               | classify ownership per `<dirty_tree_resolution>`; commit authorized changes to the right branch, leave operator-owned work untouched, and re-run           |
| `git_failure`     | 1    | a diverged detached HEAD carrying its own commits, an unresolved base, or a failed fetch — a clean behind-base detached HEAD is advanced, not failed | report `detail`; do not rebase                                                                                                                             |

A `dirty_tree` from changes Claude owns is resolved end to end by this workflow: `<dirty_tree_resolution>` checkpoints the work through `/commit-changes`, then reruns the deterministic synchronizer. Operator-owned work remains untouched unless the active instruction already authorizes committing it. The bundled synchronizer never commits or stashes; the surrounding skill composes checkpoint policy through `/commit-changes`.

Pass `--no-fetch` only when the remote-tracking ref is already current and a fetch would be redundant.

</workflow>

<dirty_tree_resolution>

A `dirty_tree` outcome means uncommitted tracked changes block the rebase, not that a content conflict exists. Stash remains forbidden. Inspect the exact tracked paths and establish who owns the changes before mutating them:

1. **Session-owned changes.** Classify changes Claude made during the active objective, then clear the precondition within the same invocation:
   - **Related to the objective** → when the worktree is detached or sitting on the default branch, create a neutral `work/<objective-slug>` branch from the current commit; invoke `/commit-changes` immediately on that branch, regardless of whether verification is passing, failing, or not run.
   - **An unrelated coordination note** — a `PLAN.md` / `ISSUES.md` recording future work that is not part of the objective → commit it onto its own local branch, and record in the imperfection ledger that the branch is pending `/merge`. At session end `/merge` routes a coordination-note-only changeset to the default branch on origin through its direct-push transport, exactly as the merge guidance prescribes for such a changeset.
2. **Operator-owned work-in-progress.** Leave every file and the index untouched. When the current instruction already authorizes committing those paths, invoke `/commit-changes` on their owning branch and continue. Otherwise use the structured-question surface with two choices: commit the files through `/commit-changes` on their owning branch (recommended), or pause base sync for inspection. Never describe this authority boundary as a rebase conflict.
3. **Re-run the synchronizer.** After every successful checkpoint, run `sync_base.py` again in the same invocation. Continue until it returns `already_current`, `rebased`, `conflict`, or `git_failure`; never return an intermediate session-owned `dirty_tree` to a composing workflow.

The branch routing above is the merge lifecycle's routing applied early — the same destinations `/merge` selects at session end.

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
   - Version or manifest bumps choose the monotonic/latest valid value, then include the exact project-declared version or manifest validation command in the result.
   - Generated artifacts are resolved by resolving their source of truth first. Never hand-merge generated output when regeneration is available. Include the exact project-declared regeneration command in the result and require re-entry after regeneration; this is a mechanical continuation, not an operator decision.
   - Redundant edits keep the change that supersedes the other by product truth, branch chronology, or source contract; remove the redundant text rather than preserving both.
   - Nearby independent edits are combined when both are compatible with the loaded specs, decisions, and tests.
   - Coordination notes are reconciled to still-true facts; stale, duplicate, or superseded notes are removed or archived through the relevant session/note workflow.
4. After resolving a file, run `git add <resolved-paths>`.
5. Continue with `git rebase --continue`.
6. Return the resolved-path scope and the narrowest deterministic verification command the project overlay declares. Run that command through its governing workflow after the rebase completes; when the overlay cannot classify the paths, return the full deterministic gate command.

Stop for the operator only when the remaining conflict is a product-intent conflict: specs, decisions, tests, newer session state, and git facts do not choose which behavior should survive. The human-facing report must say `Base sync stopped: rebase conflict requires reconciliation`, list conflicted paths, summarize every attempted reconciliation class, explain why evidence did not decide, and present the exact manual options from the `conflict.operator_options` list. Leave the rebase active. The operator can inspect, resolve and continue, or run `git rebase --abort`.

</conflict_reconciliation>

<git_command_policy>

Allowed direct commands:

- Read state: `git status`, `git rev-parse`, `git symbolic-ref --short HEAD`, `git merge-base`, `git rev-list`, `git diff --name-only`, `git diff`, `git ls-files -u`, `git show :1:<path>`, `git show :2:<path>`, `git show :3:<path>`.
- Resolve: edit files, `git add <resolved-paths>`, `git rebase --continue`.

The synchronizer script owns base movement. It runs `git fetch origin <base>` and either `git rebase origin/<base>` for an attached branch or `git switch --detach origin/<base>` for a clean detached HEAD that is an ancestor of the fetched base. Do not substitute direct sync commands for the script.

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

On `rebased` or `already_current`, the result carries a `preservation` object that identifies pre-push readiness work the base movement did not invalidate:

- `old_base_oid`, `new_base_oid`, `old_head_oid`, `new_head_oid` — full OIDs before and after the sync.
- `base_delta_paths` — the files the base advanced over.
- `branch_paths_before`, `branch_paths_after` — the branch's own changed paths against the old and new base.
- `path_overlap` — base-delta paths the branch also changed.
- `branch_patch_changed` — whether the branch's patch identity differs across the sync.
- `branch_diff_unchanged` — the git-only reuse signal: the branch patch is unchanged and the base delta does not overlap the branch.

Read `branch_diff_unchanged` to consider a prior local review reusable — and **also** confirm, against the project's overlay, that no `base_delta_paths` entry is a governance surface the reviewer judges against. Run the project overlay's narrowest deterministic lane covering `base_delta_paths`, falling back to the full gate when any path is unclassified or `path_overlap` is non-empty. The proof carries no lane name — lane mapping is the project overlay's.

The proof scopes pre-push local work only. It never satisfies a merge gate: current-head pull-request checks and the current-head CI review still decide `MERGE_READINESS` after the push.

</readiness_preservation>

<invariants>

- Rebase, never reset — a behind-base branch is brought current only by replaying its own commits onto `origin/<base>`.
- No operator decision for a clean rebase — the only operator touch-point is a product-intent conflict that deterministic evidence cannot resolve, or a hard git failure.
- A dirty tree is a precondition, never a conflict — uncommitted tracked changes yield `dirty_tree`, cleared by committing, never by stashing and never surfaced as a conflict.
- A dirty tree from Claude's own session changes is Claude's to clear per `<dirty_tree_resolution>` — committed to the right branch and re-synced, never stashed and never escalated to the operator.
- The bundled synchronizer fetches and advances the current checkout through exactly one topology-appropriate operation: rebase for an attached branch, or `git switch --detach` for an ancestor detached HEAD. It never commits or stashes the working tree; the skill may create an owning branch and invoke `/commit-changes` before rerunning it.
- A conflicted rebase remains active at operator handoff — Claude offers `git rebase --abort` as an option and does not run it automatically.
- One base derivation — the base ref and `origin/<base>` come from the changeset-scope primitives, never re-derived here.

</invariants>

<invalid_operator_escalations>

A base-sync stop reaches the operator for a product-intent conflict the rebase cannot resolve autonomously or a hard git failure that leaves no autonomous path (a diverged detached HEAD carrying its own commits, an unresolved base, a failed fetch). Resolve operator-owned work-in-progress through the authority branch in `<dirty_tree_resolution>` and never surface it as a base-sync conflict. None of the following is a valid reason to ask the operator:

- A dirty tree from a file Claude created this session — commit it per `<dirty_tree_resolution>` and re-run.
- A coordination note (`PLAN.md` / `ISSUES.md`) Claude wrote that now makes the tree dirty — commit it to its own branch, record the pending `/merge` in the imperfection ledger, and re-run.
- A conflict in a coordination note where one side is stale or superseded — reconcile the note to still-true facts and continue the rebase.
- A conflict in a generated artifact whose source of truth can be resolved — resolve the source, return the exact project-declared regeneration command, and continue after re-entry with regenerated output.
- A version bump conflict with an objectively monotonic/latest valid value — choose it, return the exact validation command, and run validation after the rebase completes.
- "Stash is forbidden, so the tree cannot be cleared" — committing clears it; the forbidden tool is not a blocker.
- A detached worktree with no branch to commit onto — create a local branch from the current commit and commit there.
- Uncertainty about which branch a change belongs on — objective work goes on the change branch, an unrelated coordination note on its own branch routed by `/merge`.
- A clean behind-base detached HEAD — sync-base advances it to the base tip; it returns `rebased` / `already_current`, not a stop.

A product-intent conflict is the only thing on the other side. Name it precisely; resolve everything else.

</invalid_operator_escalations>

<testing>

The bundled synchronizer is covered before release by this real-git test matrix:

| Input                                                | Expected result                                                                     |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------- |
| attached branch at the fetched base tip              | exit 0; `status=already_current`; non-null `preservation`                           |
| attached branch behind the fetched base              | exit 0; `status=rebased`; branch commit preserved; non-null `preservation`          |
| attached branch with a tracked edit                  | exit 4; `status=dirty_tree`; HEAD and working tree unchanged; no `conflict`         |
| attached branch with conflicting commits             | exit 3; `status=conflict`; active rebase state and structured `conflict`            |
| clean detached HEAD behind the fetched base          | exit 0; `status=rebased`; HEAD advanced to `origin/<base>`; non-null `preservation` |
| detached HEAD carrying a commit absent from the base | exit 1; `status=git_failure`; HEAD unchanged                                        |
| missing `origin` during fetch                        | exit 1; `status=git_failure`; actionable `detail`                                   |

Every fixture uses an invocation-unique temporary directory owned and removed by pytest's `tmp_path` fixture.

</testing>

<failure_modes>

**Failure 1: Bare Bash bypassed command containment.**

What happened: Claude granted `Bash, Read` even though sync-base invokes one bundled script and a finite set of git inspection and conflict-reconciliation commands.

Why it failed: the broad grant admitted unrelated destructive and network commands without approval, defeating `allowed-tools` as a security boundary.

How to avoid: grant the bundled script invocation and each required git verb explicitly; leave every unrelated command behind normal approval.

**Failure 2: The detached-head advance disappeared from the written contract.**

What happened: Claude described sync-base as fetch-and-rebase only while the synchronizer advanced a clean ancestor detached HEAD with `git switch --detach origin/<base>`.

Why it failed: callers could not reconcile the documented invariant with the script's valid detached-worktree behavior.

How to avoid: state the attached-branch rebase and detached-head advance as separate topology paths everywhere the skill describes base movement.

**Failure 3: Dirty-tree recovery stopped at an intermediate result.**

What happened: Claude returned session-owned `dirty_tree` before branch creation, commit authorization, and retry completed.

Why it failed: The public sync capability exposed an internal precondition instead of completing authorized recovery itself.

How to avoid: Keep `dirty_tree` as the bundled script's deterministic result, resolve authorized work through `/commit-changes` inside this workflow, and return only after rerunning the synchronizer.

</failure_modes>

<success_criteria>

- Exit 0 carries `status=already_current` or `status=rebased`, `conflict=null`, and a non-null `preservation` object.
- After an attached-branch `rebased` outcome, `git merge-base --is-ancestor origin/<base> HEAD` succeeds and the branch's commits remain reachable from HEAD.
- After a detached-head `rebased` outcome, HEAD equals the full OID of the fetched `origin/<base>` tip.
- Exit 4 carries `status=dirty_tree` and `conflict=null`; HEAD, index, and tracked working-tree content match their pre-invocation state.
- Exit 3 carries `status=conflict`, a non-null `conflict` object with paths, git facts, conflict text, and operator options, and an active rebase state remains available for inspection.
- Exit 1 carries `status=git_failure` and a non-empty `detail`; a diverged detached HEAD remains at its original full OID.
- Every clean outcome's `preservation` object carries `schema_version`, full old/new base and head OIDs, base and branch path sets, overlap, and patch-identity booleans; it carries no project lane name.
- Git state and command output show no synchronization through `git reset`, no commit or stash created by the bundled synchronizer, and no automatic `git rebase --abort` at conflict handoff.
- Session-owned `dirty_tree` state produces an owning branch when needed, an atomic checkpoint with verification state recorded, and a same-invocation synchronizer retry; the final result is never that intermediate `dirty_tree`.

</success_criteria>
