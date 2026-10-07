---
name: close-change
description: >-
  ALWAYS invoke this skill when a held Change reaches a terminal Lifecycle —
  Applied, Refined, or Abandoned — to write the terminal record, remove the
  holder, and close it in the declared store. NEVER close a Change issue by hand
  or before its terminal precondition holds.
argument-hint: "<Applied|Refined|Abandoned> [#N | owner/repo#N | issue-url]"
arguments: terminal reference
allowed-tools: Read, Bash(git fetch:*), Bash(git merge-base --is-ancestor:*), Bash(spx spec status:*), Bash(gh issue view:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh issue close:*), Bash(gh api graphql:*), Bash(gh api user --jq .login), Bash(printf:*), Bash(git rev-parse --show-toplevel), Bash(git rev-parse --abbrev-ref origin/HEAD), request_user_input
---

<objective>
One held Change moved from `Claimed` to the terminal Lifecycle its argument names — `Applied`, `Refined`, or `Abandoned` — with the terminal record as its newest comment, its holder removed, the issue closed with the matching reason, and the complete terminal state read back.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; it loads the common record contract and the Lifecycle rules, which govern every store read and write below by their `id`.

</required_reading>

<workflow>

1. **Validate the argument.** Require `$terminal` to equal `Applied`, `Refined`, or `Abandoned` exactly. Any other value, including an empty one, is a refused invocation naming the three accepted values; nothing is read or written.
2. **Resolve the held Change.** Resolve the store and Product under `store-binding`. Take `$reference` when present — `#N`, `owner/repo#N`, or an issue URL; a value matching none of those forms is a blocked operation naming the three forms; an `owner/repo` that differs from the overlay store is a blocked operation — otherwise the newest `<CLAIMED_CHANGE>` marker in the conversation; neither present is a blocked operation naming the missing reference. A close that runs after a compaction supplies the reference, because the marker does not survive it. Read the issue, including its `body`, and its fields under `canonical-state`. Resolve `<current-login>` with `gh api user --jq .login` and this session's assigned worktree root with `git rev-parse --show-toplevel`. Require the issue `OPEN`, Lifecycle `Claimed`, the assignee list exactly `<current-login>`, and the worktree root the winning Claim names under `claim-record` to equal this session's assigned root. A Change at Lifecycle `Submitted` is reported as waiting for the Product's Maintainer's confirmation or rejection and is never closed from that state; any other state is reported verbatim; each stops without mutation.
3. **Verify the terminal precondition from current state**, never from this conversation's account of it:
   - `Applied` requires all three of these; a merged pull request alone is not `Applied`, and a Change with no changeset and no Nodes satisfies the first two by having nothing to integrate or verify, so the third decides:
     - **Integrated.** Resolve the default branch from `git rev-parse --abbrev-ref origin/HEAD` with its leading `origin/` removed, run `git fetch origin <default>`, and require `git merge-base --is-ancestor <merge-commit> origin/<default>` to exit zero for the merge commit the record or conversation names. A Change with a changeset whose merge commit neither names refuses the close, naming the missing merge commit.
     - **Evidence satisfied.** `spx spec status --format json` reports each Node the body's `## Nodes` section lists in the `state` its row requires and none of them `failing`. The evidence obligations that section and `## Activities` state are judged from that current state, never from a verdict or command result the record or a Handoff would have to carry.
     - **Output delivered.** Every Activity in the body is checked.
   - `Refined`: at least one successor exists in the store. Read this Change's successors under `canonical-state`. A blocked read, whichever bound `canonical-state` names, refuses the close naming that bound, and derives no successor from it. Zero such records refuses the close, because a Change whose Output continues nowhere is not refined; a successor the conversation names that the store does not hold, or whose `Predecessors` does not name this Change, refuses the close and names it.
   - `Abandoned`: the operator's explicit direction and stated reason are present in the conversation. When the reason is absent, ask for it through the structured-question tool; never infer it.
4. **Close in order**, recording each successful write under `ordered-write`:
   1. Post the terminal record under `terminal-record` with `gh issue comment <N> --repo <store> --body-file -`, the text on stdin under `inert-stdin`, after inspecting it under `write-inspection`.
   2. Remove the holder with `gh issue edit <N> --repo <store> --remove-assignee @me`.
   3. Write Lifecycle `$terminal` through the single-select write under `canonical-state`, with the issue id, the `Lifecycle` field id, and the `$terminal` option id it resolves.
   4. Close the issue with `gh issue close <N> --repo <store> --reason 'completed'` for `Applied` or `Refined`, or `gh issue close <N> --repo <store> --reason 'not planned'` for `Abandoned`.
5. **Read back** under `complete-readback`: Product equals the overlay Product, Maturity is unchanged, Lifecycle equals `$terminal`, the assignee list is empty, the issue state is `CLOSED`, `stateReason` is `COMPLETED` for `Applied` or `Refined` and `NOT_PLANNED` for `Abandoned`, and the newest terminal comment is the exact comment just posted.

</workflow>

<result>

Return the issue URL and the readback values verbatim. A terminal Change receives no Handoff and never returns to `Available`; a follow-up is a Proposed Change created through `author-change`.

</result>

<failure_modes>

**A terminal Change was closed from an incomplete transition.** Claude closed the issue before the terminal record, the holder removal, and the terminal Lifecycle write had all succeeded, and reported completion without reading the complete state back. Each write lands in its declared order, and the close completes only when the readback shows every value.

**Zero successors read as every successor present.** Claude closed a Change `Refined` because the empty set of known successors was vacuously complete. A Refined Change's Output continues in its successors, so `Refined` requires at least one successor in the store naming this Change; zero successors refuses the close.

**A merge stood in for Applied.** Claude closed a Change `Applied` on the strength of a merged pull request while a deploy phase and the evidence for one Node were outstanding. `Applied` requires the changeset integrated, the evidence satisfied, and the Output delivered, verified from current state.

</failure_modes>

<success_criteria>

- A terminal argument outside `Applied`, `Refined`, and `Abandoned` was refused with the accepted values and no read or write; the held Change resolved from the explicit reference when given, else from the newest marker.
- This session's worktree held the Change, a `Submitted` Change was reported as waiting without mutation, and the named terminal precondition held from current state before the first write; `Refined` was refused while the store held no successor, any known successor was absent, a known successor's `Predecessors` did not name this Change, or the successor read was blocked, which the refusal named by the bound `canonical-state` states.
- The terminal state reads back complete: the exact terminal comment newest, an empty assignee list, Lifecycle equal to the argument, the issue `CLOSED` with the matching reason, and Product and Maturity unchanged.
- Every failed transition stopped before later mutation and reported the ordered successful writes, the failed operation, and the complete observed state.

</success_criteria>
