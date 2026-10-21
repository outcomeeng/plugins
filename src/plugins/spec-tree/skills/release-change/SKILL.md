---
name: release-change
description: >-
  ALWAYS invoke this skill when stopping work on a held Change so another agent
  can continue it — it commits the Handoff to the Change's branch and removes
  the holder, or submits a refined record to the Product's Maintainer and keeps
  the holder. NEVER leave a Change held by a conversation that has ended, and
  NEVER close a Change with this skill.
argument-hint: "[#N | owner/repo#N | issue-url] [submit]"
allowed-tools: Read, Write, Bash(git status:*), Bash(git rev-parse:*), Bash(git push -u origin HEAD:*), Bash(git switch --detach), Bash(git switch -c change/:*), Bash(git commit --allow-empty -F:*), Bash(git fetch origin change/:*), Bash(git log -1:*), Bash(git ls-remote --heads origin:*), Bash(git merge-base --is-ancestor:*), Bash(spx worktree status:*), Bash(spx diagnose:*), Bash(gh issue view:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh pr view:*), Bash(gh api graphql:*), Bash(gh api user --jq .login), Bash(gh api repos/*/issues/*/dependencies/blocked_by --method GET -F per_page=100), Bash(printenv USER), Bash(hostname -s),{!% if target == 'claude' %!} Bash(printenv CLAUDE_CODE_SESSION_ID),{!% else %!} Bash(printenv CODEX_THREAD_ID),{!% endif %!} {{! tool('ask_user') !}}, {{! tool('use_skill') !}}
---

<objective>
One held Change released in the declared store: its Handoff an empty commit on the Change's branch on origin, any local work committed and pushed, one release block posted, and its holder removed — Lifecycle `Available` written only for a `Submitted` Change. For the `submit` result, the Handoff commit lands, one submit block posts, Lifecycle `Submitted` is written, and the holder stays.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; it loads the common record contract and the Lifecycle rules, which govern every store read and write below by their `id`.

</required_reading>

<workflow>

1. **Resolve the held Change.** Read `$ARGUMENTS` as an optional issue reference followed by the optional token `submit`. A first token equal to `submit` exactly is the `submit` token with the reference absent. Any other first token is the issue reference — `#N`, `owner/repo#N`, or an issue URL — and a first token matching none of those forms is refused, naming the three forms, before anything is read or written. An absent reference reads the newest `<CLAIMED_CHANGE>` marker in the conversation; an `owner/repo` that differs from the overlay store under `store-binding` is a blocked operation. Require the token after the reference, when present, to equal `submit` exactly; any other value, and any further token, is refused, naming `submit` as the one accepted value, before anything is read or written. When neither an argument nor a marker exists, stop and report the missing issue reference; a release that runs after a compaction supplies the reference, because the marker does not survive it. Read the issue and its fields under `canonical-state`. Resolve `<current-login>` with `gh api user --jq .login`, this session's assigned worktree root with `git rev-parse --show-toplevel`, the agent session id from `{!% if target == 'claude' %!}printenv CLAUDE_CODE_SESSION_ID{!% else %!}printenv CODEX_THREAD_ID{!% endif %!}`, and the machine from `printenv USER` and `hostname -s` joined as `<user>@<host>`. Read the unassign events and the comments and select the winning claim under `claim-record`. Require the issue `OPEN`, Lifecycle `Available` — or `Submitted` for a release without the `submit` token — the assignee list exactly `<current-login>`, and the session and worktree root the winning claim names to equal this session and its assigned root. Any other state — a terminal Lifecycle, another holder, a winning claim naming a different session or worktree — is reported verbatim and stops without mutation.
2. **Refine the body first.** What this conversation learned about the Output — governing records, Governance mutations and Spec mutations blocks, a Maturity that current facts made false — belongs in the record, not in the Handoff. Use skill `spec-tree:author-change` for that revision before continuing; this skill writes no body section and no Maturity. Read `Maturity` again under `canonical-state` after the revision and retain it as the value step 7 compares. For `submit`, require `Proposed`, `Framed`, or `Sliced`; an `Executable` Change is refused without further mutation, because a Change at `Executable` is never submitted.
3. **Make the work recoverable.**
   1. Run `git status --short --branch`, resolve the default branch from `git rev-parse --abbrev-ref origin/HEAD` with its leading `origin/` removed, and classify the checkout before any commit. A checkout attached to the default branch stops before any commit and before every store write after the step 2 body revision with result `default-branch-checkout`, because default-branch work reaches origin only through `/merge`. A checkout attached to another branch has that branch as its work branch, which keeps its name until it merges. A detached checkout that carries uncommitted session-owned changes, or for which `git merge-base --is-ancestor HEAD origin/<default>` exits nonzero, gets the work branch `change/<N>` through `git switch -c change/<N>`. A clean detached checkout for which that command exits zero carries no local work: when `git ls-remote --heads origin 'change/<N>'` prints a line, run `git fetch origin change/<N>` and `git switch -c change/<N> origin/change/<N>`; otherwise run `git switch -c change/<N>`. Its Handoff names `none` as `Branch or PR` unless origin carries the branch.
   2. When the worktree carries uncommitted session-owned changes, use skill `spec-tree:commit-changes` to checkpoint them on the work branch, recording `passing`, `failing`, or `not-run`.
   3. Record the work branch's tip with `git rev-parse HEAD`; it is the commit the Handoff describes.
4. **Compose the Handoff** under `handoff-record`: `Branch or PR` from the open PR `gh pr view <branch> --json url,state` reports with `state` `OPEN`, or else the work branch name, followed by `@` and the full 40-character tip step 3.3 recorded, or `none` for a checkout step 3.1 found without local work and without the branch on origin; `Completed blocks` and `Next block` from the body's `## Governance mutations` and `## Spec mutations` blocks, by path, a block counting as completed when the newest earlier Handoff commit lists it or this session's pushed work produced its results, and a Governance mutations block only when its decision-record audit approved, each block named by its path alone with no decision-record audit token — `none` for a Parent, which carries none, and the record is never read for progress — with `refinement: <Maturity> → <next level>` as the Next block below `Executable` and `confirmation: <Maturity>` for `submit`; `Blockers` from `gh api repos/<store>/issues/<N>/dependencies/blocked_by --method GET -F per_page=100` — a mirror of the dependency graph, never its source — followed by each question the stopped work leaves for the operator, verbatim; the read is one page of 100, and a page holding 100 entries is a blocked read that stops the release and names the bound `100 blockers, one page`; `Hazards` from why the work stopped and what the next holder cannot derive quickly, each with its read-only re-confirmation command; then the two context lines `Session:` with the agent session id and `Worktree:` with the assigned root, both resolved in step 1. Write the message with the file-write tool to a file in the scratch directory the harness names for this session, under a file name unique to the agent and the Change, per `inert-stdin`, after inspecting it under `write-inspection`; never remove the file. Where the harness names no scratch directory, use the one the environment designates, such as `$RUNNER_TEMP` on a hosted runner.
5. **Land the Handoff.**
   1. Commit it with `git commit --allow-empty -F <handoff-file>` on the work branch.
   2. Push the work branch with `git push -u origin HEAD:refs/heads/<branch>` and require `git rev-parse <branch>` to equal `git rev-parse origin/<branch>`; a chat-only or local-only Handoff is never valid, because an unpushed commit is invisible to the next holder.
   3. Run `spx worktree status` from the assigned root and require the running worktree occupancy claim for this worktree and session. Read `spx/local/merging.md` when it exists and run every preflight check it declares immediately before the detach — in a repository whose overlay declares the `spx diagnose --format json` `worktree-pool` check, that check proves this worktree is not the designated main checkout; a failed check stops before the detach with its output preserved. A declared check outside this skill's granted commands goes through the ordinary permission prompt.
   4. Step the worktree off the branch with `git switch --detach` at the same commit, so another worktree can check the branch out, then run every post-cleanup check the overlay declares; a failed post-cleanup check stops before the store writes and preserves the detached checkout for inspection.
   5. The checkpoint commit, the Handoff commit, the push, and the detach are durable; a later failure reports them alongside the ordered store writes under `ordered-write`, so the next holder learns the branch is on origin and the worktree is detached.
6. **Transition in order**, recording each successful write under `ordered-write`:
   1. Post the transition block under `transition-comment` with `gh issue comment <N> --repo <store> --body-file <block-file>`, written to a file like the Handoff file and inspected under `write-inspection`. A release carries `transition: release` and a `handoff` value, one double-quoted YAML string `<branch>@<tip>; next: <Next block line>` naming the branch, the tip step 3.3 recorded, and the Next block line; the `submit` result carries `transition: submit` and no `handoff`. Either carries `maturity` equal to the value step 2 retained, `harness` `{!% if target == 'claude' %!}claude{!% else %!}codex{!% endif %!}`, the `session` and `machine` of step 1, and `worktree` the assigned root, and `position` only when the conversation names this session's position. The comment carries no Handoff text.
   2. For a release, remove the holder with `gh issue edit <N> --repo <store> --remove-assignee @me`; that unassign event is the release, and it ends the claim window. A `submit` leaves the assignee.
   3. Write Lifecycle through the single-select write under `canonical-state`, with the issue id, the `Lifecycle` field id, and the option id it resolves: `Submitted` for `submit`, and `Available` for a release of a `Submitted` Change, whose pending confirmation then lapses. A release of an `Available` Change writes no Lifecycle.
7. **Read back** under `complete-readback`: Product is unchanged (the overlay Product, or empty for a root), Maturity equals the value step 2 retained, Lifecycle is `Submitted` after `submit` and `Available` after a release, the assignee list is empty after a release and unchanged after `submit`, and `git log -1 --grep='^Handoff:' --format=%H origin/<branch>` equals the Handoff commit just pushed.

</workflow>

<result>

Return the issue URL, the readback values verbatim, the pushed branch or PR with its tip, and the Handoff's Next block line. A Change released `Available` is claimable by any agent through `claim-change`. A Change submitted `Submitted` stays with its holder and waits for the Product's Maintainer, who confirms it, or rejects it through `confirm-change`, which lowers Maturity and returns the Change to `Available` under the same holder; a release of a `Submitted` Change lapses the pending confirmation.

</result>

<failure_modes>

**A release left the holder in place.** Claude posted the release block and the Handoff commit but left the assignee on the issue, so the Change stayed held by an ended conversation. The unassign event is the release: every release removes the assignee and reads the assignee list back empty before it completes.

**A Handoff carried the body.** Claude wrote insight, status narrative, and a restated plan into the Handoff while the record's mutations blocks stayed stale. The Handoff carries the five continuation lines; what was learned about the Output is refined into the body first.

**A branch was left occupied.** Claude pushed the work branch and released the Change while the worktree still had that branch checked out, so the next holder's `git switch` failed. Step the worktree off the branch after the push; the runtime worktree claim stays with the live process.

**The Handoff went into a comment.** Claude posted the Handoff text as the release comment. The comment is the one YAML block `transition-comment` defines; the Handoff is the pushed commit.

</failure_modes>

<success_criteria>

- This session held the Change from current store state before the first write, and any other state produced a report with no mutation.
- Every session-owned change is committed; the Handoff is an empty commit on the work branch, pushed to origin, with its message exactly the lines `handoff-record` defines; the overlay-declared preflight and post-cleanup checks passed around the detach, and the worktree no longer has the branch checked out.
- The Handoff's `Branch or PR` line names the branch or its open PR followed by `@` and the full tip the Handoff commit sits on; a clean checkout without local work and without the branch on origin names `none`.
- The only comment posted is one transition block, one fenced YAML block and nothing else, as `transition-comment` defines, with `handoff` on a release only.
- A `submit` ran only at `Proposed`, `Framed`, or `Sliced`, committed and pushed its Handoff before writing `Submitted`, named `confirmation: <Maturity>` as its Next block line, and kept the assignee; an `Executable` Change was refused without further mutation after the body revision, and any other token, a first token matching no reference form included, was refused before anything was read or written.
- A blocker read that returned a page of 100 entries stopped the release before the Handoff commit and named the bound `100 blockers, one page`.
- The resulting state reads back complete: an empty assignee list after a release, Lifecycle `Available` after a release of a `Submitted` Change and unwritten after a release of an `Available` Change, Product unchanged, and Maturity equal to the value step 2 retained.
- Every failed transition stopped before later mutation and reported the ordered successful writes, the failed operation, and the complete observed state.

</success_criteria>
