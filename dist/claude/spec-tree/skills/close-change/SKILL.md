---
name: close-change
description: >-
  ALWAYS invoke this skill when a held Change reaches a terminal Lifecycle —
  Applied, Refined, or Abandoned — to write the terminal record, remove the
  holder, and close it in the declared store. NEVER close a Change issue by hand
  or before its terminal precondition holds.
argument-hint: "<Applied|Refined|Abandoned> [#N | owner/repo#N | issue-url]"
arguments: terminal reference
allowed-tools: Read, Bash(git fetch:*), Bash(git merge-base --is-ancestor:*), Bash(spx spec status:*), Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh issue close:*), Bash(gh project view:*), Bash(gh project field-list:*), Bash(gh project item-list:*), Bash(gh project item-edit:*), Bash(gh api user --jq .login), Bash(printf:*), Bash(printenv CLAUDE_CODE_SESSION_ID), AskUserQuestion, Skill
---

<objective>
One held Change moved from `Claimed` to the terminal Lifecycle its argument names — `Applied`, `Refined`, or `Abandoned` — with the terminal record as its newest comment, its holder removed, the issue closed with the matching reason, and the complete terminal state read back.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; it loads the common record contract and the Lifecycle rules, which govern every store read and write below by their `id`.

</required_reading>

<workflow>

1. **Validate the argument.** Require `$terminal` to equal `Applied`, `Refined`, or `Abandoned` exactly. Any other value, including an empty one, is a refused invocation naming the three accepted values; nothing is read or written.
2. **Resolve the held Change.** Take `$reference` when present — `#N`, `owner/repo#N`, or an issue URL; an `owner/repo` that differs from the overlay store is a blocked operation — otherwise the newest `<CLAIMED_CHANGE>` marker in the conversation; neither present is a blocked operation naming the missing reference. A close that runs after a compaction supplies the reference, because the marker does not survive it. Read the issue and its single project item under `canonical-state`. Resolve `<current-login>` with `gh api user --jq .login` and the agent session id from `printenv CLAUDE_CODE_SESSION_ID`. Require the issue `OPEN`, Status `Claimed`, `<current-login>` in the assignee list, and the winning Claim under `claim-record` to be this session's. Any other state is reported verbatim and stops without mutation.
3. **Verify the terminal precondition from current state**, never from this conversation's account of it:
   - `Applied`: the changeset has integrated into the authoritative branch — `git fetch origin <default>` then `git merge-base --is-ancestor <merge-commit> origin/<default>` exits zero for the merge commit the record or conversation names; the Assertions and evidence governing the Change's Nodes are satisfied — `spx spec status --format json` reports no `failing` node among the Frame's Nodes, and every evidence obligation the Frame states reads back as a passed result for its assertion in that same status output; and the Output is delivered — every Activity in the body is checked. A merged pull request alone is not `Applied`; a Change with no changeset and no Nodes satisfies the first two by having nothing to integrate or verify, and the third decides.
   - `Refined`: at least one successor exists in the store. The successors are the store records whose front-matter `refined_from` names this Change: find candidates with `gh issue list --repo <store> --state all --search '<issue-url>' --json number,state,body,url`, read each hit's front matter, and keep those naming this Change. Zero such records refuses the close, because a Change whose Output continues nowhere is not refined; a successor the conversation names that the store does not hold refuses the close and names it.
   - `Abandoned`: the operator's explicit direction and stated reason are present in the conversation. When the reason is absent, ask for it through the structured-question tool; never infer it.
4. **Close in order**, recording each successful write under `ordered-write`:
   1. Post the terminal record under `terminal-record` with `gh issue comment <N> --repo <store> --body-file -`, the text on stdin under `inert-stdin`, after inspecting it under `write-inspection`.
   2. Remove the holder with `gh issue edit <N> --repo <store> --remove-assignee @me`.
   3. Write Status `$terminal` with `gh project item-edit --project-id <project-id> --id <item-id> --field-id <status-field-id> --single-select-option-id <terminal-option-id>`, ids resolved under `canonical-state`.
   4. Close the issue with `gh issue close <N> --repo <store> --reason 'completed'` for `Applied` or `Refined`, or `gh issue close <N> --repo <store> --reason 'not planned'` for `Abandoned`.
5. **Read back** under `complete-readback`: Product equals the overlay Product, Maturity is unchanged, Status equals `$terminal`, the assignee list is empty, the issue state is `CLOSED`, `stateReason` is `COMPLETED` for `Applied` or `Refined` and `NOT_PLANNED` for `Abandoned`, and the newest terminal comment is the exact comment just posted.

</workflow>

<result>

Return the issue URL and the readback values verbatim. A terminal Change receives no Handoff and never returns to `Available`; a follow-up is a Proposed Change created through `author-change`.

</result>

<failure_modes>

**A terminal Change was closed from an incomplete transition.** Claude closed the issue before the terminal record, the holder removal, and the terminal Status write had all succeeded, and reported completion without reading the complete state back. Each write lands in its declared order, and the close completes only when the readback shows every value.

**Zero successors read as every successor present.** Claude closed a Change `Refined` because the empty set of known successors was vacuously complete. A Refined Change's Output continues in its successors, so `Refined` requires at least one successor in the store naming this Change; zero successors refuses the close.

**A merge stood in for Applied.** Claude closed a Change `Applied` on the strength of a merged pull request while a deploy phase and the evidence for one Node were outstanding. `Applied` requires the changeset integrated, the evidence satisfied, and the Output delivered, verified from current state.

</failure_modes>

<success_criteria>

- A terminal argument outside `Applied`, `Refined`, and `Abandoned` was refused with the accepted values and no read or write; the held Change resolved from the explicit reference when given, else from the newest marker.
- This session held the Change and the named terminal precondition held from current state before the first write; `Refined` was refused while the store held no successor or any known successor was absent.
- The terminal state reads back complete: the exact terminal comment newest, an empty assignee list, Status equal to the argument, the issue `CLOSED` with the matching reason, and Product and Maturity unchanged.
- Every failed transition stopped before later mutation and reported the ordered successful writes, the failed operation, and the complete observed state.

</success_criteria>
