---
name: orchestrate-change
description: >-
  ALWAYS invoke this skill when starting the Executor session for a Change, or checking, restarting, or answering a running Executor. NEVER start an Executor session by hand without this skill.
argument-hint: "<#N | owner/repo#N | issue-url> <absolute-worktree-root> <principal-mail-name> | check <#N> <principal-mail-name>"
allowed-tools: Read, {{! tool('use_skill') !}}, Bash(spx worktree status:*), Bash(gh issue view:*)
---

<objective>
One Change held by the worktree of one Executor session this Orchestrator started with the spec-tree definition `change-executor` selected, checked until that session closes or releases the Change, with every question it raised answered by this position's action or passed to its principal.
</objective>

<essential_principles>

- The Orchestrator is a position, never a Role of the Change: it produces no artifact of the Change and never acts as a Verifier.
- `change-executor` is the one definition this skill starts a session with; the session's own `/execute-change` launches every other session of the Change.
- Across the Changes this position orchestrates, blockers and questions are settled in the order of each Change's `Priority` project field.
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

1. Read the Change with `gh issue view <reference> --repo <store> --json number,url,state,assignees,comments`. Require the issue `OPEN`. Run `spx worktree status` and require the named root present in the pool with no running session; a root another live session holds returns `stopped` with that session's identity.
2. Use skill `coding-agents:operate-herdr` for an `inventory`, and require exactly one pane whose `cwd` equals the worktree root and that hosts no agent session. None or several returns `stopped` with the inventory result.
3. Use skill `spec-tree:claim-change` with the Change reference and the worktree root, so the winning Claim names the Executor's worktree. A claim that reports `owned_elsewhere` or any unclaimable state returns `stopped` with that report.
4. Use skill `coding-agents:operate-herdr` for one `start` in that pane, with `name` `change-<N>`, `kind` `claude`, a `timeout` of `120000`, `"mutationAuthorized": true` under the operator's standing authorization for the panes this position starts, and `agentArguments` `["--agent", "{{! subagent_name('spec-tree', 'change-executor', 'claude') !}}", "--disallowedTools", "{{! tool('ask_user', 'claude') !}}"]`.
5. When the harness's classifier refuses that `start`, submit the same `operate-herdr` request once more. A second refusal returns `stopped` with the refused request and the reason verbatim, and with the Claim step 3 wrote: its URL and the worktree root it names, reported as held with no Executor running. Before returning, use skill `coding-agents:message-agents` to send that fact to the principal, whose release of the Claim the stranded state needs, and include the message id in the result.
6. Use skill `coding-agents:operate-herdr` for one `prompt` whose `text` is the Change's issue reference, with `wait` until `working` and a `timeout` of `120000`; a prompt that does not reach `working` returns `stopped` with the herdr status and the Claim, as step 5 reports it. Return result `started` with the pane, the agent name, and the Claim.

**Check** — `$ARGUMENTS` is `check`, a Change the Orchestrator started, and the principal. One invocation is one bounded pass.

1. Read the Change with `gh issue view <N> --repo <store> --json state,comments,projectItems`; its Status is the `status` name of the project item for the store's project, and its newest `Handoff:` or terminal comment comes from `comments`. `Applied`, `Refined`, or `Abandoned` goes to step 5; `Available` with a Handoff newer than the Claim goes to step 4.
2. Use skill `coding-agents:operate-herdr` for one `read` of the Executor's pane and one `wait` with a `timeout` of `60000`. A `wait` that ends with the server state `working` shows progress and returns result `checked`.
3. A `prompt-stalled`, `wait-timeout`, or `agent-blocked` result is answered by one `prompt` whose text is the Change's issue reference. A read showing the harness's remaining-context indicator at or below 10% is answered by one `prompt` with text `/compact`. A pane whose session has ended receives one `relaunch` with the same `name`, `kind`, `timeout`, and `agentArguments` as its start, then one `prompt` with the Change's issue reference; the relaunched Executor continues from the Change and its newest Handoff. Return result `checked` with the operation taken.
4. Read the stop condition and every question the newest Handoff's blockers carry. A blocker this position removes by acting — a pane, a launch, a schedule — is answered by taking that action; when every blocker is of that kind, stop the pane with one `operate-herdr` `stop` carrying `"mutationAuthorized": true` and run **Start** again with the same worktree root and principal, returning its result. Otherwise use skill `coding-agents:message-agents` to send every other question, verbatim with the Change reference, to the principal, and return result `checked` with the message ids; the Change stays released until the principal's answer reaches the Change record.
5. When the Change is terminal and `spx worktree status` shows the worktree with no running Executor work, use skill `coding-agents:operate-herdr` for one `stop` of the pane with `"mutationAuthorized": true`, and return result `collected`.

</workflow>

<constraints>

- NEVER start a session through any definition other than `change-executor`, and never start a session outside a herdr pane.
- NEVER write, review, or audit an artifact of the Change; the Executor's launched sessions produce and judge every artifact.
- NEVER answer a question that reopens product or architecture judgment; it goes up the chain of positions.
- NEVER poll in a loop; one invocation is one bounded pass.

</constraints>

<output_format>

Return the result — `started`, `checked`, `collected`, `unavailable`, or `stopped` — with the Change URL, the worktree root, the pane and agent name, each herdr result's `status` verbatim, the questions answered and passed up with their message ids, and, for `stopped`, the exact report that stopped the workflow.

</output_format>

<success_criteria>

- The winning Claim names the Executor's worktree root, and the one session this skill started there runs the `change-executor` definition with the structured-question tool withheld on start and on every relaunch.
- Every stall, compaction, and relaunch was one bounded operation, and a relaunched Executor received only the Change's issue reference.
- Every question the Executor raised was answered within the Orchestrator's scope or passed up the chain verbatim.
- The pane was stopped only after the Change was terminal or released and the worktree carried no running work.

</success_criteria>
