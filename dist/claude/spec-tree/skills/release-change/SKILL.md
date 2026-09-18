---
name: release-change
description: >-
  ALWAYS invoke this skill when stopping work on a held Change so another agent
  can continue it — it writes the Handoff, removes the holder, and returns the
  Change to Available. NEVER leave a Change Claimed by a conversation that has
  ended, and NEVER close a Change with this skill.
argument-hint: "[#N | owner/repo#N | issue-url]"
allowed-tools: Read, Bash(git status:*), Bash(git branch --show-current), Bash(git rev-parse:*), Bash(git push -u origin HEAD:*), Bash(git switch --detach), Bash(spx worktree status:*), Bash(spx diagnose:*), Bash(gh issue view:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh pr view:*), Bash(gh project view:*), Bash(gh project field-list:*), Bash(gh project item-list:*), Bash(gh project item-edit:*), Bash(gh api user --jq .login), Bash(gh api repos/*/issues/*/dependencies/blocked_by), Bash(printf:*), Bash(printenv CLAUDE_CODE_SESSION_ID), AskUserQuestion, Skill
---

<objective>
One held Change returned from `Claimed` to `Available` in the declared store with its Handoff as the newest comment, its work committed and pushed, its holder removed, its Maturity unchanged, and the complete released state read back.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; it loads the common record contract and the Lifecycle rules, which govern every store read and write below by their `id`.

</required_reading>

<workflow>

1. **Resolve the held Change.** Read `$ARGUMENTS` as an issue reference — `#N`, `owner/repo#N`, or an issue URL — or, when empty, the newest `<CLAIMED_CHANGE>` marker in the conversation. When neither an argument nor a marker exists, stop and report the missing issue reference. Read the issue and its single project item under `canonical-state`. Resolve `<current-login>` with `gh api user --jq .login` and the agent session id from `printenv CLAUDE_CODE_SESSION_ID`. Require the issue `OPEN`, Status `Claimed`, `<current-login>` in the assignee list, and the winning Claim under `claim-record` to be this session's. Any other state — a terminal Status, another holder, a different winning session — is reported verbatim and stops without mutation.
2. **Refine the body first.** What this conversation learned about the Output — Nodes, Assertions, Decisions, completed and discovered Activities, a Maturity that current facts made false — belongs in the record, not in the Handoff. Use skill `spec-tree:author-change` for that revision before continuing; this skill writes no body section and no Maturity.
3. **Make the work recoverable.** Run `git status --short --branch`. When the worktree carries uncommitted session-owned changes, use skill `spec-tree:commit-changes` to checkpoint them, recording `passing`, `failing`, or `not-run`. When `git branch --show-current` names a work branch, push it with `git push -u origin HEAD:refs/heads/<branch>` and require `git rev-parse <branch>` to equal `git rev-parse origin/<branch>`; a chat-only or local-only Handoff is never valid, because unpushed work is invisible to the next holder. Then run `spx worktree status` from the assigned root and require the running claim for this worktree and session. Read `spx/local/merging.md` when it exists and run every preflight check it declares immediately before the detach (the timing the merge policy's overlay-safety-checks section fixes for every detach) — in a repository whose overlay declares the `spx diagnose --format json` `worktree-pool` check, that check proves this worktree is not the designated main checkout; a failed check stops before the detach with its output preserved. Step the worktree off the branch with `git switch --detach` at the same commit, so another worktree can check the branch out, then run every post-cleanup check the overlay declares; a failed post-cleanup check stops before the store writes and preserves the detached checkout for inspection. A detached worktree on the default branch tip needs no push and no switch. The checkpoint commit, the push, and the detach are durable; a later failure reports them alongside the ordered store writes under `ordered-write`, so the next holder learns the branch is on origin and the worktree is detached.
4. **Compose the Handoff** under `handoff-record`: `Branch or PR` from the pushed branch or the open PR `gh pr view --json url` reports; `Completed Activities` and `Next Activity` from the body's `# Activities` checklist; `Blockers` from `gh api repos/<store>/issues/<N>/dependencies/blocked_by` — a mirror of the dependency graph, never its source; `Hazards` from what the next holder cannot derive quickly, each with its read-only re-confirmation command. Inspect the text under `write-inspection`.
5. **Release in order**, recording each successful write under `ordered-write`:
   1. Post the Handoff with `gh issue comment <N> --repo <store> --body-file -`, the text on stdin under `inert-stdin`.
   2. Remove the holder with `gh issue edit <N> --repo <store> --remove-assignee @me`.
   3. Write Status `Available` with `gh project item-edit --project-id <project-id> --id <item-id> --field-id <status-field-id> --single-select-option-id <available-option-id>`, ids resolved under `canonical-state`. Write it even when the field already reads `Available`.
6. **Read back** under `complete-readback`: Product equals the overlay Product, Maturity is unchanged, Status is `Available`, the assignee list is empty, and the newest `Handoff:` is the exact comment just posted.

</workflow>

<result>

Return the issue URL, the readback values verbatim, the pushed branch or PR, and the Handoff's Next Activity. The Change is claimable by any agent through `claim-change`.

</result>

<failure_modes>

**Status remained implicit after a release.** Claude posted the Handoff and removed the assignee, then treated the open issue as Available while its project Status still read `Claimed`. Every release writes Status `Available` and reads Product, Maturity, Status, assignees, and the newest Handoff back before it completes.

**A Handoff carried the body.** Claude wrote insight, status narrative, and a restated plan into the Handoff comment while the record's Activities stayed stale. The Handoff carries the five continuation lines; what was learned about the Output is refined into the body through `author-change` first.

**A branch was left occupied.** Claude pushed the work branch and released the Change while the worktree still had that branch checked out, so the next holder's `git switch` failed. Step the worktree off the branch after the push; the runtime worktree claim stays with the live process.

</failure_modes>

<success_criteria>

- This session held the Change from current store state before the first write, and any other state produced a report with no mutation.
- Every session-owned change is committed, the work branch is on origin at the local tip, the overlay-declared preflight and post-cleanup checks passed around the detach, and the worktree no longer has the branch checked out.
- The Handoff carries exactly the five continuation lines, refinement landed in the body before it, and it passed `write-inspection` before posting.
- The released state reads back complete: Status `Available`, an empty assignee list, the exact new Handoff as the newest `Handoff:`, and Product and Maturity unchanged.
- Every failed transition stopped before later mutation and reported the ordered successful writes, the failed operation, and the complete observed state.

</success_criteria>
