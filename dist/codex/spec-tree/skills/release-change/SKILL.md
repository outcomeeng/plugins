---
name: release-change
description: >-
  ALWAYS invoke this skill when stopping work on a held Change so another agent
  can continue it — it writes the Handoff, removes the holder, and returns the
  Change to Available. NEVER leave a Change Claimed by a conversation that has
  ended, and NEVER close a Change with this skill.
argument-hint: "[#N | owner/repo#N | issue-url]"
allowed-tools: Read, Bash(git status:*), Bash(git branch --show-current), Bash(git rev-parse:*), Bash(git push -u origin HEAD:*), Bash(git switch --detach), Bash(git switch -c work/change-:*), Bash(git merge-base --is-ancestor:*), Bash(spx worktree status:*), Bash(spx diagnose:*), Bash(gh issue view:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh pr view:*), Bash(gh api graphql:*), Bash(gh api user --jq .login), Bash(gh api repos/*/issues/*/dependencies/blocked_by), Bash(printf:*), Bash(printenv CODEX_THREAD_ID), request_user_input
---

<objective>
One held Change returned from `Claimed` to `Available` in the declared store with its Handoff as the newest comment, any local work committed and pushed, its holder removed, its Maturity as the refinement in step 2 left it, and the complete released state read back.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; it loads the common record contract and the Lifecycle rules, which govern every store read and write below by their `id`.

</required_reading>

<workflow>

1. **Resolve the held Change.** Read `$ARGUMENTS` as an issue reference — `#N`, `owner/repo#N`, or an issue URL — or, when empty, the newest `<CLAIMED_CHANGE>` marker in the conversation; an `owner/repo` that differs from the overlay store under `store-binding` is a blocked operation. When neither an argument nor a marker exists, stop and report the missing issue reference; a release that runs after a compaction supplies the reference, because the marker does not survive it. Read the issue and its fields under `canonical-state`. Resolve `<current-login>` with `gh api user --jq .login`, this session's assigned worktree root with `git rev-parse --show-toplevel`, and the agent session id from `printenv CODEX_THREAD_ID`. Require the issue `OPEN`, Lifecycle `Claimed`, the assignee list exactly `<current-login>`, and the worktree root the winning Claim names under `claim-record` to equal this session's assigned root. Any other state — a terminal Lifecycle, another holder, a winning Claim naming a different worktree — is reported verbatim and stops without mutation.
2. **Refine the body first.** What this conversation learned about the Output — Nodes, Assertions, Decisions, completed and discovered Activities, a Maturity that current facts made false — belongs in the record, not in the Handoff. Use skill `spec-tree:author-change` for that revision before continuing; this skill writes no body section and no Maturity.
3. **Make the work recoverable.**
   1. Run `git status --short --branch`, resolve the default branch from `git rev-parse --abbrev-ref origin/HEAD` with its leading `origin/` removed, and classify the checkout before any commit. A checkout attached to the default branch stops before any commit and any store write with result `default-branch-checkout`, because default-branch work reaches origin only through `/merge`. A checkout attached to another branch has that branch as its work branch. A detached checkout that carries uncommitted session-owned changes, or for which `git merge-base --is-ancestor HEAD origin/<default>` exits nonzero, gets the work branch `work/change-<N>` through `git switch -c work/change-<N>`. A clean detached checkout for which that command exits zero carries no local work: it needs no commit, push, or switch, and its Handoff names `none` as `Branch or PR`; continue at step 4.
   2. When the worktree carries uncommitted session-owned changes, use skill `spec-tree:commit-changes` to checkpoint them on the work branch, recording `passing`, `failing`, or `not-run`.
   3. Push the work branch with `git push -u origin HEAD:refs/heads/<branch>` and require `git rev-parse <branch>` to equal `git rev-parse origin/<branch>`; a chat-only or local-only Handoff is never valid, because unpushed work is invisible to the next holder.
   4. Run `spx worktree status` from the assigned root and require the running worktree occupancy claim for this worktree and session. Read `spx/local/merging.md` when it exists and run every preflight check it declares immediately before the detach — in a repository whose overlay declares the `spx diagnose --format json` `worktree-pool` check, that check proves this worktree is not the designated main checkout; a failed check stops before the detach with its output preserved. A declared check outside this skill's granted commands goes through the ordinary permission prompt.
   5. Step the worktree off the branch with `git switch --detach` at the same commit, so another worktree can check the branch out, then run every post-cleanup check the overlay declares; a failed post-cleanup check stops before the store writes and preserves the detached checkout for inspection.
   6. The checkpoint commit, the push, and the detach are durable; a later failure reports them alongside the ordered store writes under `ordered-write`, so the next holder learns the branch is on origin and the worktree is detached.
4. **Compose the Handoff** under `handoff-record`: `Branch or PR` from the open PR `gh pr view <branch> --json url,state` reports with `state` `OPEN`, or else the pushed branch, or `none` for a checkout step 3.1 found without local work; `Completed Activities` and `Next Activity` from the body's `# Activities` checklist; `Blockers` from `gh api repos/<store>/issues/<N>/dependencies/blocked_by` — a mirror of the dependency graph, never its source — followed by each question the stopped work leaves for the operator, verbatim; `Hazards` from why the work stopped and what the next holder cannot derive quickly, each with its read-only re-confirmation command. Inspect the text under `write-inspection`.
5. **Release in order**, recording each successful write under `ordered-write`:
   1. Post the Handoff with `gh issue comment <N> --repo <store> --body-file -`, the text on stdin under `inert-stdin`.
   2. Remove the holder with `gh issue edit <N> --repo <store> --remove-assignee @me`.
   3. Write Lifecycle `Available` through the single-select write under `canonical-state`, with the issue id, the `Lifecycle` field id, and the `Available` option id it resolves. Write it even when the field already reads `Available`.
6. **Read back** under `complete-readback`: Product equals the overlay Product, Maturity equals the value read after step 2 completes, Lifecycle is `Available`, the assignee list is empty, and the newest `Handoff:` is the exact comment just posted.

</workflow>

<result>

Return the issue URL, the readback values verbatim, the pushed branch or PR, and the Handoff's Next Activity. The Change is claimable by any agent through `claim-change`.

</result>

<failure_modes>

**Lifecycle remained implicit after a release.** Claude posted the Handoff and removed the assignee, then treated the open issue as Available while its `Lifecycle` field still read `Claimed`. Every release writes Lifecycle `Available` and reads Product, Maturity, Lifecycle, assignees, and the newest Handoff back before it completes.

**A Handoff carried the body.** Claude wrote insight, status narrative, and a restated plan into the Handoff comment while the record's Activities stayed stale. The Handoff carries the five continuation lines; what was learned about the Output is refined into the body through `author-change` first.

**A branch was left occupied.** Claude pushed the work branch and released the Change while the worktree still had that branch checked out, so the next holder's `git switch` failed. Step the worktree off the branch after the push; the runtime worktree claim stays with the live process.

</failure_modes>

<success_criteria>

- This session's worktree held the Change from current store state before the first write, and any other state produced a report with no mutation.
- Every session-owned change is committed; a checkout carrying local work has its work branch on origin at the local tip, the overlay-declared preflight and post-cleanup checks passed around the detach, and no longer has the branch checked out; a clean checkout without local work names `none` as `Branch or PR`.
- The Handoff carries exactly the five continuation lines, refinement landed in the body before it, and it passed `write-inspection` before posting.
- The released state reads back complete: Lifecycle `Available`, an empty assignee list, the exact new Handoff as the newest `Handoff:`, Product equal to the overlay Product, and Maturity equal to the value read after step 2 completes.
- Every failed transition stopped before later mutation and reported the ordered successful writes, the failed operation, and the complete observed state.

</success_criteria>
