---
name: orchestrate-change
description: >-
  ALWAYS invoke this skill when starting the Executor session for a Change, or checking, restarting, or answering a running Executor. NEVER start an Executor session by hand without this skill.
argument-hint: "<#N | owner/repo#N | issue-url> <absolute-worktree-root> <principal-mail-name> | check <#N | owner/repo#N | issue-url> <pane-id> <principal-mail-name>"
allowed-tools: Read, {{! tool('use_skill') !}}, Bash(spx worktree status:*), Bash(gh issue view:*), Bash(gh api graphql:*)
---

<objective>
One Change held by the worktree of one Executor session this Orchestrator started with the spec-tree definition `change-executor` selected, checked until that session closes or releases the Change, with every pane blocker it reported acted on and every question it raised passed to its principal.
</objective>

<essential_principles>

- The Orchestrator is a position, never a Role of the Change: it produces no artifact of the Change and never acts as a Verifier.
- `change-executor` is the one definition this skill starts a session with; the session's own `/execute-change` launches every other session of the Change.
- Across the Changes this position orchestrates, blockers and questions are settled in the order of each Change's `Priority` issue field.
- The harness setting alone withholds the structured-question tool from the Executor session, on its start and on every relaunch; no skill detects whether its session is an Executor.
- Every pane operation runs through `coding-agents:operate-herdr`. Every message record is sent after this instruction: Use skill `coding-agents:message-agents`.

</essential_principles>

{!% if target == 'codex' %!}
<codex_surface>

Codex provides no native argument that starts a session with a configured subagent definition selected and the structured-question tool withheld. On this surface **Start** runs none of its steps: it returns result `unavailable` with the Change reference and this reason, and writes no store state. **Check** runs unchanged for an Executor another surface started.

</codex_surface>
{!% endif %!}

<workflow>

`$ARGUMENTS` selects one mode. Empty arguments, or arguments matching neither mode, return result `stopped` with reason `arguments-required` and the expected shapes from `argument-hint`. Resolve a `#N` reference against the Change store `spx/local/coordination.md` declares; an absent overlay, or an `owner/repo` other than that store, returns `stopped` with the observed value.

Every mode's last token is the principal: the agent-mail name of the position this Orchestrator reports to. Message records go to that name, and `coding-agents:message-agents` resolves this session's own registered sender.

**Start** — `$ARGUMENTS` names a Change, the absolute root of the worktree its Executor works in, and the principal.

1. Read the Change with `gh issue view <reference> --repo <store> --json number,url,state,assignees,comments`. An issue that is not `OPEN` returns `stopped` with its state. Run `spx worktree status`; a root absent from the pool returns `stopped` with the pool listing, and a root another live session holds returns `stopped` with that session's identity.
2. Use skill `coding-agents:operate-herdr` for an `inventory`; an agent whose `cwd` equals the worktree root returns `stopped` with that agent's identity.
3. Use skill `coding-agents:operate-herdr` for one `open-worktree` with `path` the worktree root and `"mutationAuthorized": true` under the operator's standing authorization for the worktrees this position starts Executors in; its root pane is the Executor's pane. A failed open returns `stopped` with the herdr status.
4. Use skill `spec-tree:claim-change` with the Change reference and the worktree root, so the winning Claim names the Executor's worktree. A claim that reports `owned_elsewhere` or any unclaimable state returns `stopped` with that report.
5. Use skill `coding-agents:operate-herdr` for one `start` in that pane, with `name` `change-<N>`, `kind` `claude`, a `timeout` of `120000`, `"mutationAuthorized": true` under the same standing authorization, and `agentArguments` `["--agent", "{{! subagent_name('spec-tree', 'change-executor', 'claude') !}}", "--disallowedTools", "{{! tool('ask_user', 'claude') !}}"]`.
6. When the harness's classifier refuses that `start`, submit the same `operate-herdr` request once more. A second refusal returns `stopped` with the refused request and the reason verbatim, and with the Claim step 4 wrote: its URL and the worktree root it names, reported as held with no Executor running. Before returning, use skill `coding-agents:message-agents` to send that fact to the principal, whose release of the Claim the stranded state needs, and include the message id in the result.
7. Use skill `coding-agents:operate-herdr` for one `prompt` whose `text` is the Change's issue reference, with `wait` until `working` and a `timeout` of `120000`; a prompt that does not reach `working` returns `stopped` with the herdr status and the Claim, as step 6 reports it. Return result `started` with the pane, the agent name, and the Claim.

**Check** — `$ARGUMENTS` is `check`, a Change the Orchestrator started, the pane its Start reported, and the principal. One invocation is one bounded pass.

1. Read the Change with `gh issue view <reference> --repo <store> --json number,state,comments`, and its issue fields with `gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){issueFieldValues(first:50){nodes{... on IssueFieldSingleSelectValue{name field{... on IssueFieldSingleSelect{name}}}}}}}}' -f o=<owner> -f r=<repo> -F n=<N>`; its Lifecycle is the `name` of the value whose field is `Lifecycle`, the worktree root is the root field of the winning `Claim: <session id> <root>` comment — for a Claimed Change the earliest Claim posted after the newest `Handoff:`, and for a released Change the earliest Claim posted before that Handoff and after the Handoff preceding it, which is the Claim the release ended — and its newest `Handoff:` or terminal comment comes from `comments`. `Applied`, `Refined`, or `Abandoned` goes to step 5; `Available` with a Handoff newer than the Claim goes to step 4.
2. Use skill `coding-agents:operate-herdr` for one `read` of the pane and one `wait` on it with a `timeout` of `60000`. A `wait` that ends with the server state `working` shows progress and returns result `checked`.
3. Every other result is answered by exactly one of these operations, and returns result `checked` with the operation taken:
   - A read showing the harness's remaining-context indicator at or below 10% receives one `prompt` with text `/compact`.
   - A pane whose session has ended — an `identity-unavailable` result, or a read at the shell prompt — receives one `relaunch` with the same `name`, `kind`, `pane`, `timeout`, `agentArguments`, and `"mutationAuthorized": true` as its start, then one `prompt` with the Change's issue reference; the relaunched Executor continues from the Change and its newest Handoff.
   - Any other result — `prompt-stalled`, `wait-timeout`, `agent-blocked`, or a wait that ends `idle`, `done`, or `unknown` — receives one `prompt` whose text is the Change's issue reference.
4. Read the stop condition and every question the newest Handoff's blockers carry, and handle them by kind:
   - **Only pane blockers.** When every blocker names the Executor's own session — ended, stalled, or out of context — and `spx worktree status` shows no running work in the worktree, stop the pane with one `operate-herdr` `stop` carrying `"mutationAuthorized": true`, run **Start** again with the worktree root step 1 read and the same principal, and return its result. When `spx worktree status` shows running work, return result `checked` with that status verbatim. This position starts no session except the Executor **Start** starts.
   - **Any question.** Every other blocker is a question for the principal. Use skill `coding-agents:operate-agent-mail` for one `inbox` of the principal with `includeBodies` false and `limit` 200, and look for a record whose `correlation` is `change-<N>-handoff-<Handoff comment id>` and whose `sender` is this position. When such a record exists, the questions were already sent: send nothing and return result `checked` with reason `awaiting-principal` and those message ids. Otherwise use skill `coding-agents:message-agents` to send every question, verbatim with the Change reference, to the principal under that correlation, and return result `checked` with the message ids. The Change stays released until the principal, with its answer in the Change record, orders **Start** for it.
5. When the Change is terminal, run `spx worktree status`. When it shows the worktree with no running Executor work, use skill `coding-agents:operate-herdr` for one `stop` of the pane with `"mutationAuthorized": true`, and return result `collected`. When it still shows running work, return result `checked` with that status verbatim; a later Check collects the pane.

</workflow>

<constraints>

- NEVER start a session through any definition other than `change-executor`, and never start a session outside a herdr pane.
- NEVER write, review, or audit an artifact of the Change; the Executor's launched sessions produce and judge every artifact.
- NEVER answer a question that reopens product or architecture judgment; it goes up the chain of positions.
- NEVER poll in a loop; one invocation is one bounded pass.

</constraints>

<output_format>

Return the result — `started`, `checked`, `collected`, `unavailable`, or `stopped` — with the Change URL, the worktree root, the pane and agent name, each herdr result's `status` verbatim, the blockers acted on and the questions passed up, with their message ids, and, for `stopped`, the exact report that stopped the workflow.

</output_format>

<success_criteria>

- The winning Claim names the Executor's worktree root, and the one session this skill started there runs the `change-executor` definition with the structured-question tool withheld on start and on every relaunch.
- Every stall, compaction, and relaunch was one bounded operation, and a relaunched Executor received only the Change's issue reference.
- Every pane blocker the Executor reported was acted on, and every question it raised was passed up the chain verbatim, once per Handoff.
- The pane was stopped only after the Change was terminal or released and the worktree carried no running work.

</success_criteria>
