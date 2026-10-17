---
name: confirm-change
description: >-
  ALWAYS invoke this skill when the Product's Maintainer confirms a Submitted
  Change — it moves the Change from Submitted to Available and posts no
  comment. NEVER move a Submitted Change by hand.
argument-hint: "<#N | owner/repo#N | issue-url>"
allowed-tools: Read, Bash(gh issue view:*), Bash(gh api graphql:*), Skill
---

<objective>
One `Submitted` Change moved to `Available` in the declared store with the complete state read back, or a report naming why the Change cannot be confirmed and listing each write that landed before the step that stopped it.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; it loads the common record contract and the Lifecycle rules, which govern every store read and write below by their `id`.

</required_reading>

<workflow>

1. **Resolve the target.** Resolve the store and Product under `store-binding`. Read `$ARGUMENTS` as the issue reference alone — `#N`, `owner/repo#N`, or an issue URL; an argument matching none of those forms, and any text after the reference, refuse the invocation, naming the three forms, with nothing written; a reference whose repository differs from the overlay store, in the `owner/repo#N` form or in an issue URL, is a blocked operation, and an absent reference stops the invocation naming the missing reference.
2. **Verify the precondition.** Read the issue and its fields under `canonical-state`. A confirmation starts only when the issue is `OPEN`, Product equals the overlay Product, Lifecycle is `Submitted`, the assignee list is empty, and Maturity is `Proposed`, `Framed`, or `Sliced`. Any other state is reported verbatim and stops without mutation.
3. **Write Lifecycle `Available`** through the single-select write under `canonical-state`, with the issue id, the `Lifecycle` field id, and the `Available` option id it resolves, recording the write under `ordered-write`. Post no comment and write neither Maturity nor any body section.
4. **Read back** under `complete-readback`: Product equals the overlay Product, Maturity is unchanged, Lifecycle is `Available`, the assignee list is empty, and the newest field-change event under `authority-read` is the Lifecycle move out of `Submitted` just written.

</workflow>

<result>

Return the issue URL, the readback values verbatim, the move's actor and time from its field-change event, and the next step: `claim-change` claims the Change.

</result>

<success_criteria>

- The Change was `Submitted` and at `Proposed`, `Framed`, or `Sliced` from current store state before the write, and any other state produced a report with no mutation.
- The only write is Lifecycle `Available`: no comment was posted, and neither Maturity nor any body section changed.
- The readback shows Lifecycle `Available`, an empty assignee list, Product and Maturity unchanged, and the Lifecycle move out of `Submitted` as the newest field-change event.
- Every failed transition stopped before later mutation and reported the ordered successful writes, the failed operation, and the complete observed state.

</success_criteria>
