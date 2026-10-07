---
name: confirm-change
description: >-
  ALWAYS invoke this skill when the Product's Maintainer confirms or rejects a
  Submitted Change — it posts the confirmation or rejection comment and moves
  the Change from Submitted to Available. NEVER move a Submitted Change by hand.
argument-hint: "<#N | owner/repo#N | issue-url> <confirm | reject <reason>>"
allowed-tools: Read, Bash(gh issue view:*), Bash(gh issue comment:*), Bash(gh api graphql:*), Bash(printf:*), Bash(printenv CLAUDE_CODE_SESSION_ID), AskUserQuestion, Skill
---

<objective>
One `Submitted` Change moved to `Available` in the declared store, with one `Confirmation:` or `Rejection:` comment naming the delegate, the operator it acts for, the harness, and the session as the deciding comment of that move, and the complete state read back; or a report naming why the Change cannot be confirmed or rejected, listing each write that landed before the step that stopped it.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; it loads the common record contract and the Lifecycle rules, which govern every store read and write below by their `id`.

</required_reading>

<workflow>

1. **Resolve the target.** Resolve the store and Product under `store-binding`. Read the first token of `$ARGUMENTS` as the issue reference — `#N`, `owner/repo#N`, or an issue URL; a first token matching none of those forms refuses the invocation, naming the three forms, with nothing written; a reference whose repository differs from the overlay store, in the `owner/repo#N` form or in an issue URL, is a blocked operation, and an absent reference stops the invocation naming the missing reference. Read the rest of `$ARGUMENTS` as the decision: `confirm`, or `reject` followed by the reason. The argument alone decides, and the conversation never does. An absent decision, any text after `confirm`, any other word, and a `reject` with no reason refuse the invocation, naming the two accepted forms, with nothing written.
2. **Verify the precondition.** Read the issue and its fields under `canonical-state`. A confirmation or rejection starts only when the issue is `OPEN`, Product equals the overlay Product, Lifecycle is `Submitted`, the assignee list is empty, and Maturity is `Proposed`, `Framed`, or `Sliced`. Any other state is reported verbatim and stops without mutation.
3. **Resolve identities.** Resolve the session id from `printenv CLAUDE_CODE_SESSION_ID`. The harness is `Claude Code`. Take the delegate — the name this session acts under — and the operator it acts for from the name each has been given in this conversation, copied verbatim; when either is absent, ask for it through the structured-question tool, and never infer a name. An empty value stops before any write.
4. **Compose the comment** under `confirmation-record`: `Confirmation: <Maturity>` with the Maturity read in step 2 for `confirm`, or `Rejection: <Maturity>` for `reject`, then the lines `Delegate`, `For`, `Harness`, and `Session` in that order, and for a rejection the `Reason` line last. Inspect the text under `write-inspection`.
5. **Write in order**, recording each successful write under `ordered-write`:
   1. Post the comment with `gh issue comment <N> --repo <store> --body-file -`, the text on stdin under `inert-stdin`.
   2. Write Lifecycle `Available` through the single-select write under `canonical-state`, with the issue id, the `Lifecycle` field id, and the `Available` option id it resolves.
6. **Read back** under `complete-readback`: Product equals the overlay Product, Maturity is unchanged, Lifecycle is `Available`, the assignee list is empty, and the deciding comment under `authority-read` is the exact comment just posted.

</workflow>

<result>

Return the issue URL, the readback values verbatim, whether the comment is a confirmation or a rejection with its Maturity, and the next step: `claim-change` claims the Change, and the next Maturity write after a rejection follows `maturity-and-authority`.

</result>

<success_criteria>

- The Change was `Submitted` and at `Proposed`, `Framed`, or `Sliced` from current store state before the first write, and any other state produced a report with no mutation.
- The comment records the decision the argument stated and nothing else decided it, carries exactly the lines `confirmation-record` states for its kind, names the delegate and the operator without inference, and passed `write-inspection` before posting.
- The comment was posted before Lifecycle moved, and the move wrote neither Maturity nor any body section.
- The readback shows Lifecycle `Available`, an empty assignee list, Product and Maturity unchanged, and the exact posted comment as the deciding comment.
- Every failed transition stopped before later mutation and reported the ordered successful writes, the failed operation, and the complete observed state.

</success_criteria>
