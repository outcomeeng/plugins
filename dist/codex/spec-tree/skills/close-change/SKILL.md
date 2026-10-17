---
name: close-change
description: >-
  ALWAYS invoke this skill when a held Change reaches a terminal Lifecycle —
  Applied or Abandoned — to write the terminal record, remove the holder, and
  close it in the declared store. NEVER close a Change issue by hand
  or before its terminal precondition holds.
argument-hint: "<Applied|Abandoned> [#N | owner/repo#N | issue-url]"
arguments: terminal reference
allowed-tools: Read, Write, Bash(git fetch:*), Bash(git merge-base --is-ancestor:*), Bash(spx spec status:*), Bash(gh issue view:*), Bash(gh pr view:*), Bash(gh pr checks:*), Bash(git cat-file -e:*), Bash(git rev-parse --verify:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh issue close:*), Bash(gh api graphql:*), Bash(gh api user --jq .login), Bash(git rev-parse --show-toplevel), Bash(git rev-parse --abbrev-ref origin/HEAD), request_user_input
---

<objective>
One held Change moved from `Claimed` to the terminal Lifecycle its argument names — `Applied` or `Abandoned` — with the terminal record as its newest comment, its holder removed, the issue closed with the matching reason, and the complete terminal state read back; an `Applied` close whose Parent has a Parent and no open child continues upward.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; it loads the common record contract and the Lifecycle rules, which govern every store read and write below by their `id`.

Use skill `spec-tree:change-standards`. Invoke it with `Executable`; its `merge_composition` selects the results a Leaf's Nodes must hold, because the record names none.

</required_reading>

<workflow>

1. **Validate the argument.** Require `$terminal` to equal `Applied` or `Abandoned` exactly. Any other value, including `Refined` and an empty one, is a refused invocation naming the two accepted values; nothing is read or written.
2. **Resolve the held Change.** Resolve the store and Product under `store-binding`. Take `$reference` when present — `#N`, `owner/repo#N`, or an issue URL; a value matching none of those forms is a blocked operation naming the three forms; an `owner/repo` that differs from the overlay store is a blocked operation — otherwise the newest `<CLAIMED_CHANGE>` marker in the conversation; neither present is a blocked operation naming the missing reference. A close that runs after a compaction supplies the reference, because the marker does not survive it. Read the issue, including its `body`, and its fields under `canonical-state`. Resolve `<current-login>` with `gh api user --jq .login` and this session's assigned worktree root with `git rev-parse --show-toplevel`. Derive the Change's type — Leaf, Parent, or root — from its body's mutations blocks and the store's `Parent` values under `canonical-state`. The winning Claim is the earliest `Claim:` comment posted after the newest `Handoff:` that a Lifecycle move to `Available` follows, or since issue creation when none exists, under the `claim-record` window; a Handoff the Executor posted without a release leaves the Claim before it in force. Require the issue `OPEN`, Product equal to the overlay Product or empty for a root, Lifecycle `Claimed`, the assignee list exactly `<current-login>`, and the worktree root the winning Claim names to equal this session's assigned root. A Change at Lifecycle `Submitted` is reported as waiting for the Product's Maintainer to move it out of `Submitted` and is never closed from that state; any other state is reported verbatim; each stops without mutation.
3. **Verify the terminal precondition from current state**, never from this conversation's account of it. The type from step 2 selects the precondition for `Applied`; a merged pull request alone is not `Applied`:
   - A **Leaf** requires all four of these:
     - **Integrated.** Resolve the default branch from `git rev-parse --abbrev-ref origin/HEAD` with its leading `origin/` removed and run `git fetch origin <default>`. Read the newest Handoff, whether a release or an Executor progress Handoff, and its `Branch or PR` line under `handoff-record` and take the text before its `@` as the pushed branch or the pull request; the full head commit SHA after `@` is the state the Handoff describes and is never the commit this check takes. For a pull request, take the merge commit from `gh pr view <pr> --repo <repository> --json state,mergeCommit`; for a pushed branch, take its tip on origin from `git rev-parse --verify origin/<branch>`. Require `git merge-base --is-ancestor <merge-commit> origin/<default>` to exit zero. No Handoff, a Handoff naming `none`, or a pull request with no merge commit refuses the close, naming it; the record's body carries no link to produced content and is never read for one.
     - **Results held.** Judge each Node the body's `## Spec mutations` blocks list against the `merge_composition` loaded under `<required_reading>`: the results it selects for the malleability after the block opening names, given the tags of the Node's assertions. Run `git cat-file -e origin/<default>:<node-path>/spx.status.json`, where `<node-path>` is the path the block opening names.
       - When it exits zero, the Node's directory on the default branch holds its status claim, and `spx spec status --format json` reports whether the Node holds every one of those results.
       - When it exits nonzero, the Node carries no status claim. The Node holds every result its merge composition selects only when two conditions hold. First, the newest Handoff's `Completed blocks` line lists the Node's block under `handoff-record`. Second, the text before `@` on that Handoff's `Branch or PR` line names a pull request, and every check `gh pr checks <pr> --repo <repository> --json name,state` reports for its merged head has `state` `SUCCESS`. A failed or empty read refuses the close, and so do a check in any other state and a Handoff that names a pushed branch rather than a pull request. A check that concluded skipped reports `state` `SKIPPED`, a review check skipped because the pull request modifies that check's own workflow file included, so a Node without a claim on such a pull request holds its results only once its `spx.status.json` reaches the default branch and `spx spec status` judges it.
       - A Node short of a result refuses the close, naming the Node and the result. The judgment reads the status claim, the Handoff's lines, and the checks as they stand, never a verdict or command result the record or a Handoff would have to carry.
     - **Decisions audited.** Each record the body's `## Governance mutations` blocks amend or create counts as audited when the newest Handoff's `Completed blocks` line lists its block under `handoff-record`; the decision-record audit seals no verification run, so the line carries no token and the check runs no verification command. A record whose block that line does not list refuses the close, naming each such record.
     - **Intent met.** The result the Intent's Evidence names holds when observed from current state.
   - A **Parent** requires every child, read under `canonical-state`, `CLOSED`, and the child that closed last, read with `gh issue view <child> --repo <store> --json state,stateReason,closedAt`, closed `Applied`. An open child, or a last child closed `Abandoned`, refuses the close and leaves the Parent open for refinement.
   - A **root** closes only on the operator's explicit direction in the conversation. `Applied` additionally requires the operator's judgment that the Intent is met; without both, ask through the structured-question tool and write nothing.
   - `Abandoned` requires the operator's explicit direction and stated reason in the conversation. When the reason is absent, ask for it through the structured-question tool; never infer it.
4. **Close in order**, recording each successful write under `ordered-write`:
   1. Post the terminal record under `terminal-record` with `gh issue comment <N> --repo <store> --body-file <terminal-file>`, the text written with the file-write tool to a file in the scratch directory the harness names for this session, under a file name unique to the agent and the Change, per `inert-stdin`, after inspecting it under `write-inspection`; never remove the file. Where the harness names no scratch directory, use the one the environment designates, such as `$RUNNER_TEMP` on a hosted runner.
   2. Remove the holder with `gh issue edit <N> --repo <store> --remove-assignee @me`.
   3. Write Lifecycle `$terminal` through the single-select write under `canonical-state`, with the issue id, the `Lifecycle` field id, and the `$terminal` option id it resolves.
   4. Close the issue with `gh issue close <N> --repo <store> --reason 'completed'` for `Applied`, or `gh issue close <N> --repo <store> --reason 'not planned'` for `Abandoned`.
5. **Read back** under `complete-readback`: Product equals the overlay Product, or is empty for a root, Maturity is unchanged, Lifecycle equals `$terminal`, the assignee list is empty, the issue state is `CLOSED`, `stateReason` is `COMPLETED` for `Applied` and `NOT_PLANNED` for `Abandoned`, and the newest terminal comment is the exact comment just posted.
6. **Continue upward.** After a close of `Applied`, read this Change's Parent under `canonical-state`. When it has none, or its Parent has none, stop: a root never closes this way. Otherwise, when it has no open child, invoke `spec-tree:claim-change` for it in this session, then repeat steps 2 to 5 for it with `Applied`, and repeat this step for its own Parent. When any child is open, stop; when the Parent is not claimable, report the `claim-change` result verbatim. After a close of `Abandoned`, stop.

</workflow>

<result>

Return the issue URL and the readback values verbatim for each Change closed, in closing order. A terminal Change receives no Handoff and never returns to `Available`; a follow-up is a new Proposed Change.

</result>

<failure_modes>

**A terminal Change was closed from an incomplete transition.** Claude closed the issue before the terminal record, the holder removal, and the terminal Lifecycle write had all succeeded, and reported completion without reading the complete state back. Each write lands in its declared order, and the close completes only when the readback shows every value.

**A Parent closed with its work unfinished.** Claude closed a Parent `Applied` because one child had closed `Applied`, while a sibling stayed open or the last child to close had closed `Abandoned`. A Parent closes `Applied` only when every child is closed and the last to close closed `Applied`.

**A merge stood in for Applied.** Claude closed a Leaf `Applied` on the strength of a merged pull request while the merge commit of the pull request, or the tip of the pushed branch, that the newest Handoff names was not on the default branch, one Node lacked a result its merge composition selects, and one amended record's Governance mutations block was missing from the newest Handoff's completed-blocks line. `Applied` for a Leaf requires the merge commit of the pull request, or the tip of the pushed branch, that the newest Handoff names to be an ancestor of the default branch, every Node holding every result the composition selects for its malleability after, every amended or new record's block listed in that Handoff's completed-blocks line, and the Intent's Evidence met, verified from current state.

**A Node without a status claim was judged from an empty report.** Claude ran `spx spec status` for a Node whose directory on the default branch held no `spx.status.json`, found no result for it, and either refused every such close or read the silence as passing. A Node without a claim holds its results only when the newest Handoff lists its block and names a pull request whose every check on the merged head reported `SUCCESS`.

</failure_modes>

<success_criteria>

- A terminal argument outside `Applied` and `Abandoned`, `Refined` included, was refused with the accepted values and no read or write; the held Change resolved from the explicit reference when given, else from the newest marker.
- This session's worktree held the Change, a `Submitted` Change was reported as waiting without mutation, and the precondition for the Change's type held from current state before the first write; a root closed only on the operator's direction, and a Parent stayed open while a child was open or its last child closed `Abandoned`.
- A Node whose directory on the default branch holds no status claim held its results only when the newest Handoff listed its block and named a pull request whose every check on the merged head reported `SUCCESS`; a Handoff naming a pushed branch, or a check that reported `SKIPPED`, refused `Applied` for that Node.
- An `Applied` close whose Parent has a Parent and no open child claimed that Parent and closed it `Applied`, repeating upward, and closed no root.
- The terminal state reads back complete: the exact terminal comment newest, an empty assignee list, Lifecycle equal to the argument, the issue `CLOSED` with the matching reason, and Product (empty for a root) and Maturity unchanged.
- Every failed transition stopped before later mutation and reported the ordered successful writes, the failed operation, and the complete observed state.

</success_criteria>
