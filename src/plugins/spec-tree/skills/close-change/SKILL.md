---
name: close-change
description: >-
  ALWAYS invoke this skill when a held Change reaches a terminal Lifecycle —
  Applied or Abandoned — to write the terminal record, remove the holder, and
  close it in the declared store. NEVER close a Change issue by hand
  or before its terminal precondition holds.
argument-hint: "<Applied|Abandoned> [#N | owner/repo#N | issue-url]"
arguments: terminal reference
allowed-tools: Read, Write, Bash(git fetch:*), Bash(git merge-base --is-ancestor:*), Bash(spx spec status:*), Bash(gh issue view:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh issue close:*), Bash(gh api graphql:*), Bash(gh api user --jq .login), Bash(git rev-parse --show-toplevel), Bash(git rev-parse --abbrev-ref origin/HEAD), {{! tool('ask_user') !}}, {{! tool('use_skill') !}}
---

<objective>
One held Change moved from `Claimed` to the terminal Lifecycle its argument names — `Applied` or `Abandoned` — with the terminal record as its newest comment, its holder removed, the issue closed with the matching reason, and the complete terminal state read back; an `Applied` close whose Parent has a Parent and no open child continues upward.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; it loads the common record contract and the Lifecycle rules, which govern every store read and write below by their `id`.

</required_reading>

<workflow>

1. **Validate the argument.** Require `$terminal` to equal `Applied` or `Abandoned` exactly. Any other value, including `Refined` and an empty one, is a refused invocation naming the two accepted values; nothing is read or written.
2. **Resolve the held Change.** Resolve the store and Product under `store-binding`. Take `$reference` when present — `#N`, `owner/repo#N`, or an issue URL; a value matching none of those forms is a blocked operation naming the three forms; an `owner/repo` that differs from the overlay store is a blocked operation — otherwise the newest `<CLAIMED_CHANGE>` marker in the conversation; neither present is a blocked operation naming the missing reference. A close that runs after a compaction supplies the reference, because the marker does not survive it. Read the issue, including its `body`, and its fields under `canonical-state`. Resolve `<current-login>` with `gh api user --jq .login` and this session's assigned worktree root with `git rev-parse --show-toplevel`. Derive the Change's type — Leaf, Parent, or root — from its body and the store's `Parent` values under `canonical-state`. Require the issue `OPEN`, Product equal to the overlay Product or empty for a root, Lifecycle `Claimed`, the assignee list exactly `<current-login>`, and the worktree root the winning Claim names under `claim-record` to equal this session's assigned root. A Change at Lifecycle `Submitted` is reported as waiting for the Product's Maintainer's confirmation or rejection and is never closed from that state; any other state is reported verbatim; each stops without mutation.
3. **Verify the terminal precondition from current state**, never from this conversation's account of it. The type from step 2 selects the precondition for `Applied`; a merged pull request alone is not `Applied`:
   - A **Leaf** requires all four of these:
     - **Linked.** Each Node in the body's `## Nodes` section that the Change adds, modifies, or implements, per the transition of its `## Mutations` row, has a link in `## Artifacts`. A Node with no link refuses the close, naming it.
     - **Integrated.** Resolve the default branch from `git rev-parse --abbrev-ref origin/HEAD` with its leading `origin/` removed and run `git fetch origin <default>`. Each `## Artifacts` link pins the merge commit that carries its content; require `git merge-base --is-ancestor <merge-commit> origin/<default>` to exit zero for every link. A body with no `## Artifacts` section or a link that pins no merge commit refuses the close, naming it.
     - **Evidence satisfied.** `spx spec status --format json` reports each Node the body's `## Nodes` section lists in the `state` its Required state names and none of them `failing`. The evidence obligations of the `## Mutations` rows are judged from that current state, never from a verdict or command result the record or a Handoff would have to carry.
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

**A merge stood in for Applied.** Claude closed a Leaf `Applied` on the strength of a merged pull request while one Node had no Artifacts link, one link was not on the default branch, and one Node was off its Required state. `Applied` for a Leaf requires a link for every Node the Change adds, modifies, or implements, every Artifacts link integrated, every Node at its Required state, and the Intent's Evidence met, verified from current state.

</failure_modes>

<success_criteria>

- A terminal argument outside `Applied` and `Abandoned`, `Refined` included, was refused with the accepted values and no read or write; the held Change resolved from the explicit reference when given, else from the newest marker.
- This session's worktree held the Change, a `Submitted` Change was reported as waiting without mutation, and the precondition for the Change's type held from current state before the first write; a root closed only on the operator's direction, and a Parent stayed open while a child was open or its last child closed `Abandoned`.
- An `Applied` close whose Parent has a Parent and no open child claimed that Parent and closed it `Applied`, repeating upward, and closed no root.
- The terminal state reads back complete: the exact terminal comment newest, an empty assignee list, Lifecycle equal to the argument, the issue `CLOSED` with the matching reason, and Product (empty for a root) and Maturity unchanged.
- Every failed transition stopped before later mutation and reported the ordered successful writes, the failed operation, and the complete observed state.

</success_criteria>
