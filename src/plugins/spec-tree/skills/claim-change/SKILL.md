---
name: claim-change
description: >-
  ALWAYS invoke this skill when claiming an Available Change from the declared
  Change store to hold it for refinement or execution. NEVER assign a Change or
  post its claim by hand without this skill.
argument-hint: "[#N | owner/repo#N | issue-url] [worktree-root]"
allowed-tools: Read, Write, Bash(spx worktree status:*), Bash(git fetch:*), Bash(git switch:*), Bash(gh issue list:*), Bash(gh issue view:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh api graphql:*), Bash(gh api user --jq .login), Bash(printenv USER), Bash(hostname -s), Bash(git log -1:*),{!% if target == 'claude' %!} Bash(printenv CLAUDE_CODE_SESSION_ID),{!% else %!} Bash(printenv CODEX_THREAD_ID),{!% endif %!} Bash(git rev-parse --show-toplevel), Bash(git worktree list --porcelain), Bash(git ls-remote --heads origin:*), {{! tool('ask_user') !}}, {{! tool('use_skill') !}}
---

<objective>
One `Available` Change held by this session in the declared store: its assignee added, one claim block posted naming this session and its worktree, the winning claim read back, and Lifecycle, Maturity, and the body untouched — or a report naming why the Change is not claimable with nothing written.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; it loads the common record contract and the Lifecycle rules, which govern every store read and write below by their `id`.

</required_reading>

<workflow>

1. **Resolve the target.** Resolve the store and Product under `store-binding`. Read the first token of `$ARGUMENTS` as the target and an optional second token as the worktree root to claim for. An issue reference — `#N`, `owner/repo#N`, or an issue URL — names the Change; a first token matching none of those forms is refused, naming the three forms, before anything is read or written; an `owner/repo` that differs from the overlay store is a blocked operation. When the argument is empty, list candidates with `gh issue list --repo <store> --state open --json number,title,assignees,url --limit 50`; a list of 50 entries is a blocked listing naming `50 issues`, which offers no candidate and claims nothing. Read each candidate's Product, Maturity, and Lifecycle under `canonical-state`, and offer up to three through the structured-question tool: Changes whose Product equals the overlay Product or is empty for a root, Lifecycle is `Available`, and assignee list is empty — Executable first, then any Maturity — each labelled with number, title, and Maturity. No candidate is a report, not a claim.
2. **Resolve identities.** Resolve the current account once with `gh api user --jq .login`, require one non-empty login, and record it as `<current-login>`. Resolve the agent session id verbatim from `{!% if target == 'claude' %!}printenv CLAUDE_CODE_SESSION_ID{!% else %!}printenv CODEX_THREAD_ID{!% endif %!}`, the machine from `printenv USER` and `hostname -s` joined as `<user>@<host>` under `transition-comment`, and this session's assigned worktree root from `git rev-parse --show-toplevel`. The claim root is the worktree root step 1 read, which must be an absolute path with no `.` or `..` segment, or this session's assigned root when step 1 read none. An empty value or a malformed claim root stops before any write.
3. **Verify the precondition under `claim-record`.** Read the issue and its fields under `canonical-state`, the unassign events of the issue, and the comments of the issue for the claim exception alone. A claim starts only when the issue is `OPEN`, Product equals the overlay Product or is empty for a root, Maturity is one declared value, Lifecycle is `Available`, and the winning claim, if any, is not live. A live winning claim of another session is reported as `owned_elsewhere`, naming its session and worktree. A Change at Lifecycle `Submitted` is reported as waiting for the Product's Maintainer, and any other state, field mismatch, or assignee list of more than one account is reported verbatim; each stops without mutation.
4. **Claim in order**, recording each successful write under `ordered-write`:
   1. When the assignee list is empty, add the holder with `gh issue edit <N> --repo <store> --add-assignee @me`. When it holds `<current-login>` alone, keep it. When it holds another account whose winning claim is not live, remove that account by its exact login with `gh issue edit <N> --repo <store> --remove-assignee '<login>'`, then add `@me`.
   2. Post the claim block with `gh issue comment <N> --repo <store> --body-file <claim-file>`: the one fenced YAML block `transition-comment` defines, with `transition: claim`, `maturity` the Maturity read in step 3, `harness` `{!% if target == 'claude' %!}claude{!% else %!}codex{!% endif %!}`, the `session` and `machine` of step 2, and `worktree` the claim root. Add `position` only when the conversation names this session's position. Write the text with the file-write tool to a file in the scratch directory the harness names for this session, under a file name unique to the agent and the Change, per `inert-stdin`, after inspecting it under `write-inspection`; never remove the file. Where the harness names no scratch directory, use the one the environment designates, such as `$RUNNER_TEMP` on a hosted runner.
   3. Re-read the unassign events and the comments and select the winning claim under `claim-record`. When another claim wins, this session lost: report `owned_elsewhere` naming the winning session and stop after one of two assignee repairs. When the winner's author equals `<current-login>`, leave the shared assignee, because it represents the winning session. When it differs, remove only `<current-login>` with `gh issue edit <N> --repo <store> --remove-assignee '<current-login>'` and re-read, requiring `<current-login>` absent.
   4. When this session wins, require the assignee list to be exactly `<current-login>`. An extra assignee is unexplained partial state: stop under `ordered-write`.
5. **Read back** under `complete-readback`: Product is unchanged (the overlay Product, or empty for a root), Maturity is unchanged, Lifecycle is `Available`, the assignee list is exactly `<current-login>`, and the winning claim under `claim-record` is the block just posted.
6. **Emit the claim marker** so later skills read the held Change without a second store lookup:

   ```text
   <CLAIMED_CHANGE url="<issue-url>" number="<N>" store="<store>" maturity="<Maturity>">
   claimed by <agent session id> for <claim root>
   </CLAIMED_CHANGE>
   ```

   A later claim in the same conversation emits its own marker.
7. **Bring the Change's branch into the assigned worktree.** When the claim root differs from this session's assigned root, leave every checkout as it is and report the checkout as pending for the claim root. Otherwise run `git ls-remote --heads origin 'change/<N>'`. When it prints nothing, leave the checkout as it is: execution creates the branch, and the first block of the record is the point to continue from. Otherwise run `spx worktree status` from the assigned root as a read-only check that records no worktree claim; when the running session's worktree occupancy claim is absent, stop before any checkout transition and report the diagnostic. Otherwise read `spx/local/merging.md` when it exists and run every check `store-binding` requires before a checkout transition, then `git fetch origin 'change/<N>'`. Run `git worktree list --porcelain`: a worktree other than this one whose `branch` line is `refs/heads/change/<N>` holds the branch, which is then unavailable here, so leave the checkout as it is and report the holder. Otherwise run `git switch 'change/<N>'` in this worktree, creating the local tracking branch when none exists. A failed fetch or a switch refused for any other reason ends this step with the claim standing: report the git output verbatim and leave the checkout as it is. Read the newest Handoff with `git log -1 --grep='^Handoff:' --format=%B origin/change/<N>`; a branch that carries no Handoff commit leaves the first block of the record as the point to continue from. Use skill `spec-tree:sync-base` afterwards, before any Change detail is presented as current.

</workflow>

<result>

Return the issue URL, the readback values verbatim, the Maturity, the newest Handoff's `Branch or PR` line when one exists, and the branch now checked out in the assigned worktree. A Change below Executable continues as refinement; execution at Executable continues from the Handoff's `Next block` line, or from the first block of the record when no Handoff exists.

</result>

<failure_modes>

**The assignee stood in for the claim.** Claude treated an added assignee as a won claim and started executing while a second session of the same account held the earlier claim. One account runs several sessions, so the assignee cannot distinguish them; the winning claim under `claim-record` decides — the earliest live claim block posted after the newest unassign event — and the loser withdraws only its own record.

**A partial claim was repaired by guessing.** Claude's claim block failed to post after the assignee landed, and Claude re-ran a later step to make the state look complete. Stop at the failed write, report the completed prefix and the observed state, and leave the partial state visible for recovery.

</failure_modes>

<success_criteria>

- The Change was claimable from current store state before the first write, and any other state produced a report with no mutation; a `Submitted` Change was reported as waiting for the Product's Maintainer.
- The claimed state reads back complete: Lifecycle `Available`, exactly the winning account as assignee, this session's claim block as the winning claim under `claim-record`, and Product and Maturity unchanged, a root's empty Product included.
- The only comment posted is one claim block, one fenced YAML block and nothing else, carrying `transition`, `maturity`, `harness`, `session`, `machine`, and `worktree`, and `position` only when known.
- No Lifecycle, Maturity, or body section was written.
- A losing concurrent claim removed only its own holder record, verified the winner unchanged, reported `owned_elsewhere`, and executed nothing.
- Every failed transition stopped before later mutation and reported the ordered successful writes, the failed operation, and the complete observed state.
- A root carrying no Product was claimable beside the configured Product's Changes and read back with its Product still empty.
- A candidate listing of 50 entries produced a blocked result naming `50 issues`, with no offer and no claim.
- A branch `change/<N>` that origin carries is checked out in the assigned worktree after a read-only occupancy check when the claim root is this session's assigned root; an absent branch, a failed fetch, a failed switch, and a branch held by another worktree each left the claim standing and the checkout unchanged.
- The winning claim names the claim root: the worktree root the argument supplied, or this session's assigned root.
- The result names the Handoff's `Next block` line, or the first block of the record when no Handoff exists, as the point execution continues from.

</success_criteria>
