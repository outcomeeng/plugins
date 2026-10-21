---
name: confirm-change
description: >-
  ALWAYS invoke this skill when the Product's Maintainer confirms or rejects a
  Submitted Change — it posts one transition block and moves the Change from
  Submitted to Available, lowering Maturity first on a rejection. NEVER move a
  Submitted Change by hand.
argument-hint: "<#N | owner/repo#N | issue-url> [reject <reason>]"
allowed-tools: Read, Write, Bash(gh issue view:*), Bash(gh issue comment:*), Bash(gh api graphql:*), Bash(printenv USER), Bash(hostname -s), Bash(git rev-parse --show-toplevel),{!% if target == 'claude' %!} Bash(printenv CLAUDE_CODE_SESSION_ID),{!% else %!} Bash(printenv CODEX_THREAD_ID),{!% endif %!} {{! tool('use_skill') !}}
---

<objective>
One `Submitted` Change moved to `Available` in the declared store under the same holder, with one transition block posted — `confirm` with Maturity unchanged, or `reject` with the Maturity one level lower and the instruction naming what to fix — and the complete state read back, or a report naming why the Change cannot be confirmed or rejected and listing each write that landed before the step that stopped it.
</objective>

<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Lifecycle`; it loads the common record contract and the Lifecycle rules, which govern every store read and write below by their `id`.

</required_reading>

<workflow>

1. **Resolve the target.** Resolve the store and Product under `store-binding`. Read `$ARGUMENTS` as the issue reference — `#N`, `owner/repo#N`, or an issue URL — alone for a confirmation, or followed by the token `reject` exactly and then the rest of the argument as the reason for a rejection. An argument matching none of those forms, a second token other than `reject`, a `reject` with an empty reason, and any text after a confirmation's reference refuse the invocation, naming the accepted forms, with nothing written; a reference whose repository differs from the overlay store, in the `owner/repo#N` form or in an issue URL, is a blocked operation, and an absent reference stops the invocation naming the missing reference.
2. **Verify the precondition.** Read the issue and its fields under `canonical-state`, and keep the assignee list as read. A transition starts only when the issue is `OPEN`, Product equals the overlay Product, Lifecycle is `Submitted`, and Maturity is `Proposed`, `Framed`, or `Sliced`. A rejection at `Proposed` is refused, because a Proposed Change takes no reject. Any other state is reported verbatim and stops without mutation.
3. **Resolve identities.** Resolve the agent session id from `{!% if target == 'claude' %!}printenv CLAUDE_CODE_SESSION_ID{!% else %!}printenv CODEX_THREAD_ID{!% endif %!}`, the machine from `printenv USER` and `hostname -s` joined as `<user>@<host>`, and this session's assigned worktree root from `git rev-parse --show-toplevel`. An empty value stops before any write.
4. **Write in order**, recording each successful write under `ordered-write`:
   1. Post the transition block under `transition-comment` with `gh issue comment <N> --repo <store> --body-file <block-file>`: the one fenced YAML block with `transition: confirm` or `transition: reject`, `maturity` the Maturity at the Lifecycle move — the value read in step 2 for a confirmation, the lowered value for a rejection — `harness` `{!% if target == 'claude' %!}claude{!% else %!}codex{!% endif %!}`, the `session`, `machine`, and `worktree` of step 3, and `position` only when the conversation names this session's position. A rejection adds `reason`, the reason of step 1 as one double-quoted YAML string. Write the text with the file-write tool to a file in the scratch directory the harness names for this session, under a file name unique to the agent and the Change, per `inert-stdin`, after inspecting it under `write-inspection`; never remove the file. Where the harness names no scratch directory, use the one the environment designates, such as `$RUNNER_TEMP` on a hosted runner.
   2. For a rejection, write the Maturity one level lower — `Framed` to `Proposed`, `Sliced` to `Framed` — through the single-select write under `canonical-state`, with the issue id, the `Maturity` field id, and the option id it resolves, before the Lifecycle write.
   3. Write Lifecycle `Available` through the single-select write under `canonical-state`, with the issue id, the `Lifecycle` field id, and the `Available` option id it resolves. Release no assignee, and write no body section.
5. **Read back** under `complete-readback`: Product equals the overlay Product, Maturity is unchanged for a confirmation and one level lower for a rejection, Lifecycle is `Available`, the assignee list equals the list step 2 read, and the newest `Lifecycle` field-change event under `authority-read` is the move out of `Submitted` just written, preceded for a rejection by the `Maturity` event that lowered it.

</workflow>

<result>

Return the issue URL, the readback values verbatim, the move's actor and time from its field-change event, and the next step. After a confirmation, the holder advances the Change under `maturity-and-authority`, or any session claims it through `claim-change` once the holder releases it. After a rejection, the holder keeps the assignee, repairs the record named by the reason, and submits it again with no release and no new claim.

</result>

<success_criteria>

- The Change was `Submitted` and at `Proposed`, `Framed`, or `Sliced` from current store state before the first write, a rejection at `Proposed` was refused, and any other state produced a report with no mutation.
- The only comment posted is one `confirm` or `reject` block, one fenced YAML block and nothing else, as `transition-comment` defines, with `reason` on a reject only.
- A confirmation wrote Lifecycle `Available` alone; a rejection wrote the Maturity one level lower and then Lifecycle `Available`; neither released the assignee or wrote a body section.
- The readback shows Lifecycle `Available`, the assignee list unchanged, Product unchanged, Maturity unchanged or one level lower, and the Lifecycle move out of `Submitted` as the newest field-change event.
- Every failed transition stopped before later mutation and reported the ordered successful writes, the failed operation, and the complete observed state.

</success_criteria>
