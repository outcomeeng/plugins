---
name: claim-change
description: >-
  ALWAYS invoke this skill when claiming an Available Change from the declared
  Change store to hold it for refinement or execution. NEVER assign a Change or
  write its Status by hand without this skill.
argument-hint: "[#N | owner/repo#N | issue-url]"
allowed-tools: Read, Bash(spx worktree status:*), Bash(git fetch:*), Bash(git switch:*), Bash(gh pr view:*), Bash(gh issue list:*), Bash(gh issue view:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh project view:*), Bash(gh project field-list:*), Bash(gh project item-list:*), Bash(gh project item-edit:*), Bash(gh api user --jq .login), Bash(printf:*), Bash(printenv CLAUDE_CODE_SESSION_ID), Bash(git rev-parse --show-toplevel), AskUserQuestion, Skill
---

<objective>
One Change moved from `Available` to `Claimed` in the declared store — this agent session recorded as its holder — with the complete claimed state read back, or a report naming why the Change is not claimable with nothing written.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; it loads the common record contract and the Lifecycle rules, which govern every store read and write below by their `id`.

</required_reading>

<workflow>

1. **Resolve the target.** Read `$ARGUMENTS`. An issue reference — `#N`, `owner/repo#N`, or an issue URL — names the Change; an `owner/repo` that differs from the overlay store is a blocked operation. When the argument is empty, list candidates with `gh issue list --repo <store> --state open --json number,title,assignees,url --limit 50`, read each candidate's Product, Maturity, and Status under `canonical-state`, and offer up to three through the structured-question tool: Changes whose Product equals the overlay Product, Status is `Available`, and assignee list is empty — Executable first, then any Maturity — each labelled with number, title, and Maturity. No candidate is a report, not a claim.
2. **Verify the precondition.** Read the issue and its single project item under `canonical-state`. A claim starts only when the issue is `OPEN`, Product equals the overlay Product, Maturity is one declared value, Status is `Available`, and the assignee list is empty. Any other state reports the terminal state, field mismatch, or holder verbatim and stops without mutation.
3. **Resolve identities.** Resolve the current account once with `gh api user --jq .login`, require one non-empty login, and record it as `<current-login>`. Resolve the agent session id verbatim from `printenv CLAUDE_CODE_SESSION_ID` and the assigned worktree root from `git rev-parse --show-toplevel`; an empty value stops before any write.
4. **Claim in order**, recording each successful write under `ordered-write`:
   1. `gh issue edit <N> --repo <store> --add-assignee @me`.
   2. Post the Claim under `claim-record` with `gh issue comment <N> --repo <store> --body-file -`, the text on stdin under `inert-stdin`.
   3. Re-read the comments and select the winning Claim under `claim-record`. When another Claim wins, this session lost: report `owned_elsewhere` naming the winning session and stop after one of two assignee repairs. When the winner's author equals `<current-login>`, leave the shared assignee, because it represents the winning session. When it differs, remove only `<current-login>` with `gh issue edit <N> --repo <store> --remove-assignee '<current-login>'`, re-read, and require `<current-login>` absent while the same earliest Claim still wins.
   4. When this session wins, reconcile the assignee list before writing Status: keep `<current-login>`; remove another assignee only when that account authored a later losing Claim since the newest `Handoff:` — the window `claim-record` defines — by its exact login, and re-read after the removals. An extra assignee without that evidence is unexplained partial state — stop under `ordered-write` and write no Status.
   5. Write Status `Claimed` with `gh project item-edit --project-id <project-id> --id <item-id> --field-id <status-field-id> --single-select-option-id <claimed-option-id>`, ids resolved under `canonical-state`.
5. **Read back** under `complete-readback`: Product equals the overlay Product, Maturity is unchanged, Status is `Claimed`, the assignee list is exactly `<current-login>`, and the earliest Claim after the latest Handoff is this session's exact comment.
6. **Emit the claim marker** so later skills read the held Change without a second store lookup:

   ```text
   <CLAIMED_CHANGE url="<issue-url>" number="<N>" store="<store>" maturity="<Maturity>">
   claimed by <agent session id> in <assigned worktree root>
   </CLAIMED_CHANGE>
   ```

   A later claim in the same conversation emits its own marker; the newest marker names the Change the release and close skills act on unless they receive an explicit reference.
7. **Bring the Handoff's branch into the assigned worktree.** Read only the newest `Handoff:` comment's `Branch or PR` line. When it names a branch on origin, run `spx worktree status` from the assigned root as a read-only check that records no worktree claim; when the running session's claim is absent, stop before any checkout transition and report the diagnostic. Otherwise `git fetch origin <branch>` and `git switch <branch>` in this worktree, creating the local tracking branch when none exists; a branch another worktree holds is unavailable here, so branch from `origin/<branch>` under a fresh name in this worktree and continue. When the line names a pull request, resolve its head branch with `gh pr view <url> --json headRefName` and treat it the same way. When it is `none` or no Handoff exists, leave the checkout as it is. Use skill `spec-tree:sync-base` afterwards, before any Change detail is presented as current.

</workflow>

<result>

Return the issue URL, the readback values verbatim, the Maturity, the newest `Handoff:` comment's `Branch or PR` line when one exists, and the branch now checked out in the assigned worktree. Refinement below Executable continues through `author-change`; execution at Executable continues from the Handoff's Next Activity or the first unchecked Activity.

</result>

<failure_modes>

**The assignee stood in for the Claim.** Claude treated an added assignee as a won claim and started executing while a second session of the same account held the earlier Claim. One account runs several sessions, so the assignee cannot distinguish them; the earliest `Claim:` after the latest `Handoff:` decides, and the loser withdraws only its own record.

**A partial claim was repaired by guessing.** Claude's Status write failed after the assignee and Claim landed, and Claude re-ran a later step to make the state look complete. Stop at the failed write, report the completed prefix and the observed state, and leave the partial state visible for recovery.

</failure_modes>

<success_criteria>

- The Change was claimable from current store state before the first write, and any other state produced a report with no mutation.
- The claimed state reads back complete: Status `Claimed`, exactly the winning account as assignee, this session's Claim as the earliest since the last Handoff, and Product and Maturity unchanged.
- A losing concurrent claim removed only its own holder record, verified the winner unchanged, reported `owned_elsewhere`, and executed nothing.
- Every failed transition stopped before later mutation and reported the ordered successful writes, the failed operation, and the complete observed state.
- Maturity and every body section are untouched.
- When the newest Handoff names a branch or pull request, that work is checked out in the assigned worktree after a read-only occupancy check, and the checkout is current with its base.

</success_criteria>
