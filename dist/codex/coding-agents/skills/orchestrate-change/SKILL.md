---
name: orchestrate-change
description: >-
  ALWAYS invoke this skill when starting the Executor session for a Change, or checking, restarting, or answering a running Executor. NEVER start an Executor session by hand without this skill.
argument-hint: "<#N | owner/repo#N | issue-url> <absolute-worktree-root> <principal-mail-name> | check <#N | owner/repo#N | issue-url> <pane-id> <principal-mail-name>"
allowed-tools: Read, Bash(spx worktree status:*), Bash(gh issue view:*)
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

<codex_surface>

Codex provides no native argument that starts a session with a configured subagent definition selected and the structured-question tool withheld. On this surface **Start** runs none of its steps: it returns result `unavailable` with the Change reference and this reason, and writes no store state. **Check** runs unchanged for an Executor another surface started.

</codex_surface>

<workflow>

`$ARGUMENTS` selects one mode. Empty arguments, or arguments matching neither mode, return result `stopped` with reason `arguments-required` and the expected shapes from `argument-hint`. Resolve a `#N` reference against the Change store `spx/local/coordination.md` declares; an absent overlay, or an `owner/repo` other than that store, returns `stopped` with the observed value.

Every mode's last token is the principal: the agent-mail name of the position this Orchestrator reports to. Message records go to that name, and `coding-agents:message-agents` resolves this session's own registered sender.

**Start** — `$ARGUMENTS` names a Change, the absolute root of the worktree its Executor works in, and the principal.

1. Read the Change with `gh issue view <reference> --repo <store> --json number,url,state,assignees,comments`. An issue that is not `OPEN` returns `stopped` with its state. Run `spx worktree status`; a root absent from the pool returns `stopped` with the pool listing, and a root another live session holds returns `stopped` with that session's identity.
2. Use skill `coding-agents:operate-herdr` for an `inventory`; an agent whose `cwd` equals the worktree root returns `stopped` with that agent's identity.
3. Use skill `coding-agents:operate-herdr` for one `open-worktree` with `path` the worktree root and `"mutationAuthorized": true` under the operator's standing authorization for the worktrees this position starts Executors in; its root pane is the Executor's pane. A failed open returns `stopped` with the herdr status.
4. Use skill `spec-tree:claim-change` with the Change reference and the worktree root, so the winning Claim names the Executor's worktree. A claim that reports `owned_elsewhere` or any unclaimable state returns `stopped` with that report.
5. Use skill `coding-agents:operate-herdr` for one `start` in that pane, with `name` `change-<N>`, `kind` `claude`, a `timeout` of `120000`, `"mutationAuthorized": true` under the same standing authorization, and `agentArguments` `["--agent", "spec-tree:change-executor", "--disallowedTools", "AskUserQuestion"]`.
6. When the harness's classifier refuses that `start`, submit the same `operate-herdr` request once more. A second refusal returns `stopped` with the refused request and the reason verbatim, and with the Claim step 4 wrote: its URL and the worktree root it names, reported as held with no Executor running. Before returning, use skill `coding-agents:message-agents` to send that fact to the principal, whose release of the Claim the stranded state needs, and include the message id in the result.
7. Use skill `coding-agents:operate-herdr` for one `prompt` whose `text` is the Change's issue reference, with `wait` until `working` and a `timeout` of `120000`; a prompt that does not reach `working` returns `stopped` with the herdr status and the Claim, as step 6 reports it. Return result `started` with the pane, the agent name, and the Claim.

**Check** — `$ARGUMENTS` is `check`, a Change the Orchestrator started, the pane its Start reported, and the principal. One invocation is one bounded pass.

1. Read the Change with `gh issue view <reference> --repo <store> --json number,state,comments,projectItems`; its Status is the `status` name of the project item for the store's project, the worktree root is the root field of the earliest `Claim: <session id> <root>` comment posted after the newest `Handoff:`, and its newest `Handoff:` or terminal comment comes from `comments`. `Applied`, `Refined`, or `Abandoned` goes to step 5; `Available` with a Handoff newer than the Claim goes to step 4.
2. Use skill `coding-agents:operate-herdr` for one `read` of the pane and one `wait` on it with a `timeout` of `60000`. A `wait` that ends with the server state `working` shows progress and returns result `checked`.
3. Every other result is answered by exactly one of these operations, and returns result `checked` with the operation taken:
   - A read showing the harness's remaining-context indicator at or below 10% receives one `prompt` with text `/compact`.
   - A pane whose session has ended — an `identity-unavailable` result, or a read at the shell prompt — receives one `relaunch` with the same `name`, `kind`, `pane`, `timeout`, `agentArguments`, and `"mutationAuthorized": true` as its start, then one `prompt` with the Change's issue reference; the relaunched Executor continues from the Change and its newest Handoff.
   - Any other result — `prompt-stalled`, `wait-timeout`, `agent-blocked`, or a wait that ends `idle`, `done`, or `unknown` — receives one `prompt` whose text is the Change's issue reference.
4. Read the stop condition and every question the newest Handoff's blockers carry. A blocker this position removes by acting — a pane, a launch, a schedule — is answered by taking that action; when every blocker is of that kind, stop the pane with one `operate-herdr` `stop` carrying `"mutationAuthorized": true` and run **Start** again with the worktree root step 1 read and the same principal, returning its result. Otherwise use skill `coding-agents:message-agents` to send every other question, verbatim with the Change reference, to the principal, and return result `checked` with the message ids; the Change stays released until the principal's answer reaches the Change record.
5. When the Change is terminal, run `spx worktree status`. When it shows the worktree with no running Executor work, use skill `coding-agents:operate-herdr` for one `stop` of the pane with `"mutationAuthorized": true`, and return result `collected`. When it still shows running work, return result `checked` with that status verbatim; a later Check collects the pane.

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
