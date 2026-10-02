---
name: orchestrate-change
description: >-
  ALWAYS invoke this skill when starting the Executor session for a Change, or checking, restarting, or answering a running Executor. NEVER start an Executor session by hand without this skill.
argument-hint: "<#N | owner/repo#N | issue-url> <absolute-worktree-root> <herdr-workspace> <own-mail-name> <principal-mail-name> | check <#N | owner/repo#N | issue-url> <pane-id> <own-mail-name> <principal-mail-name>"
allowed-tools: Read, Bash(spx worktree status:*), Bash(gh issue view:*), Bash(gh api graphql:*)
---

<objective>
One Change held by the worktree of one Executor session this Orchestrator started with the spec-tree definition `change-executor` selected, checked until that session closes or releases the Change, with every Executor-session stop acted on and every other release, with its questions, passed to its principal.
</objective>

<essential_principles>

- The Orchestrator is a position, never a Role of the Change: it produces no artifact of the Change and never acts as a Verifier.
- `change-executor` is the one definition this skill starts a session with; the session's own `/execute-change` launches every other session of the Change.
- Across the Changes this position orchestrates, blockers and questions are settled in the order of each Change's `Priority` issue field.
- This position runs **Check** for each Executor it started at the regular interval its principal sets, until **Check** returns `collected`; each run is one bounded pass, and no pass waits for the next.
- The harness setting alone withholds the structured-question tool from the Executor session, on its start and on every relaunch; no skill detects whether its session is an Executor.
- Every pane operation runs through `coding-agents:operate-herdr`. Every message record is sent after this instruction: Use skill `coding-agents:message-agents`.

</essential_principles>

<codex_surface>

Codex provides no native argument that starts a session with a configured subagent definition selected and the structured-question tool withheld. On this surface **Start** runs none of its steps: it returns result `unavailable` with the Change reference and this reason, and writes no store state. **Check** runs unchanged for an Executor another surface started.

</codex_surface>

<workflow>

`$ARGUMENTS` selects one mode. Empty arguments, or arguments matching neither mode, return result `stopped` with reason `arguments-required` and the expected shapes from `argument-hint`. Resolve a `#N` reference against the Change store `spx/local/coordination.md` declares; an absent overlay, or an `owner/repo` other than that store, returns `stopped` with the observed value.

Every mode's last two tokens are this position's own registered agent-mail name and the principal: the agent-mail name of the position this Orchestrator reports to. Every message request to `coding-agents:message-agents` carries this position's own name as `sender` and the principal as `recipient`.

The invocation is the mutation authorization, and it covers exactly the targets it names: the worktree root **Start** names, created or opened grouped with the herdr workspace Start names, with the root pane herdr returns for it, and the pane **Check** names. Every `"mutationAuthorized": true` below applies to one of those targets; no other workspace or pane is mutated.

**Start** — `$ARGUMENTS` names a Change, the absolute root of the worktree its Executor works in, the id of the herdr workspace that worktree is grouped with, this position's own mail name, and the principal.

1. Read the Change with `gh issue view <reference> --repo <store> --json number,url,state,assignees,comments`. An issue that is not `OPEN` returns `stopped` with its state. Run `spx worktree status`; a root another live session holds returns `stopped` with that session's identity, and whether the root appears in the pool listing selects step 3's operation.
2. Use skill `coding-agents:operate-herdr` for an `inventory`; an agent whose `cwd` equals the worktree root returns `stopped` with that agent's identity.
3. Use skill `coding-agents:operate-herdr` for one worktree operation with `workspace` the herdr workspace the invocation names, `path` the worktree root, and `"mutationAuthorized": true` for that root and workspace: `create-worktree` when the root is absent from the pool listing, and `open-worktree` otherwise. The root pane the result's `worktree` returns is the Executor's pane. A failed operation returns `stopped` with the herdr status.
4. Use skill `spec-tree:claim-change` with the Change reference and the worktree root, so the winning Claim names the Executor's worktree. A claim that reports `owned_elsewhere` or any unclaimable state returns `stopped` with that report.
5. Use skill `coding-agents:operate-herdr` for one `start` in that pane, with `name` `change-<N>`, `kind` `claude`, a `timeout` of `120000`, `"mutationAuthorized": true` for that same root, and `agentArguments` `["--agent", "spec-tree:change-executor", "--disallowedTools", "AskUserQuestion"]`. Any result other than a ready session or a classifier refusal returns `stopped` with the herdr status, and reports the Claim and sends the principal the fact exactly as step 6 does for a second refusal, with the herdr status in place of the refusal.
6. When the harness's classifier refuses that `start`, step back before any other action and retrace what led to the refusal: the refused request as sent, the reason the classifier gave, and each earlier step that shaped the request. Correct any defect the retrace finds, then submit the `operate-herdr` request once more, changed only by that correction; never reword it to hide what the classifier objected to. A second refusal returns `stopped` with the refused request and the reason verbatim, and with the Claim step 4 wrote: its URL and the worktree root it names, reported as held with no Executor running. Before returning, use skill `coding-agents:message-agents` to send that fact to the principal, whose release of the Claim the stranded state needs: `kind` `fact`, `correlation` `change-<N>-start`, `subject` `Change <N>: Executor start refused, Claim held`, `ackRequired` true, and the refused request, the reason and the Claim as `body`. Include the message id in the result.
7. Use skill `coding-agents:operate-herdr` for one `prompt` whose `text` is the Change's issue reference, with `wait` until `working` and a `timeout` of `120000`; a prompt that does not reach `working` returns `stopped` with the herdr status, and reports the Claim and sends the principal the fact exactly as step 6 does for a second refusal, with the herdr status in place of the refusal. Return result `started` with the pane, the agent name, and the Claim.

**Check** — `$ARGUMENTS` is `check`, a Change the Orchestrator started, the pane its Start reported, this position's own mail name, and the principal. One invocation is one bounded pass.

1. Read the Change with `gh issue view <reference> --repo <store> --json number,state,comments`, and its issue fields with `gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){issueFieldValues(first:50){nodes{... on IssueFieldSingleSelectValue{name field{... on IssueFieldSingleSelect{name}}}}}}}}' -f o=<owner> -f r=<repo> -F n=<N>`; its Lifecycle is the `name` of the value whose field is `Lifecycle`, the worktree root is the root field of the winning `Claim: <session id> <root>` comment — for a Claimed Change the earliest Claim posted after the newest `Handoff:`, and for a released Change the earliest Claim posted before that Handoff and after the Handoff preceding it, which is the Claim the release ended — and its newest `Handoff:` or terminal comment comes from `comments`. `Applied`, `Refined`, or `Abandoned` goes to step 5; `Available` with a Handoff newer than the Claim goes to step 4.
2. Use skill `coding-agents:operate-herdr` for one `read` of the pane and one `wait` on it with a `timeout` of `60000`. A `wait` that ends with the server state `working` shows progress and returns result `checked`.
3. Every other result is answered by exactly one of these operations, and returns result `checked` with the operation taken:
   - A read showing the harness's remaining-context indicator at or below 10% receives one `prompt` with text `/compact`.
   - A pane whose session has ended — an `identity-unavailable` result, or a read at the shell prompt — receives one `relaunch` with the same `name`, `kind`, `pane`, `timeout`, `agentArguments`, and `"mutationAuthorized": true` as its start, then one `prompt` with the Change's issue reference; the relaunched Executor continues from the Change and its newest Handoff.
   - Any other result — `prompt-stalled`, `wait-timeout`, `agent-blocked`, or a wait that ends `idle`, `done`, or `unknown` — receives one `prompt` whose text is the Change's issue reference.
4. Read the newest Handoff's `Blockers` and `Hazards` lines. A `Blockers` entry that is a Change URL is a dependency, every other `Blockers` entry is a question, and `Hazards` states why the work stopped. Handle the release by what those lines record:
   - **Executor session.** When `Blockers` is `none`, `Hazards` states that the Executor session itself ended, stalled, or ran out of context, and `spx worktree status` shows no running work in the worktree, restart the Executor in the pane the invocation names. Stop its session with one `operate-herdr` `stop` carrying `"mutationAuthorized": true`, which leaves the pane at its shell. Use skill `spec-tree:claim-change` with the Change reference and the worktree root step 1 read; a claim that reports `owned_elsewhere` or any unclaimable state returns `stopped` with that report. Then run one `relaunch` into that pane with the same `name`, `kind`, `timeout`, `agentArguments`, and `"mutationAuthorized": true` as Start's `start`, handling a classifier refusal or any other failed result as **Start** steps 5 and 6 handle a failed `start`, and send one `prompt` as **Start** step 7 does. Return result `started` with the pane, the agent name, and the Claim. When `spx worktree status` shows running work, return result `checked` with that status verbatim. This position starts no session except the Executor **Start** starts and this restart relaunches.
   - **Every other release.** A question, a dependency, or any other stop `Hazards` states — a repeated defect class, a failed launch or unusable result, a blocked gate — goes to the principal once per Handoff; this position restarts no Executor for it. Use skill `coding-agents:operate-agent-mail` for one `inbox` of the principal with `includeBodies` false and `limit` 200, and look for a record whose `correlation` is `change-<N>-handoff-<Handoff comment id>` and whose `sender` is this position's own mail name. When such a record exists, the release was already reported: send nothing and return result `checked` with reason `awaiting-principal` and those message ids. Otherwise use skill `coding-agents:message-agents` for one request: `kind` `question` when `Blockers` carries a question and `fact` otherwise, that `correlation`, `subject` `Change <N>: Executor released`, `ackRequired` true, and as `body` every question verbatim, the `Blockers` and `Hazards` lines verbatim, and the Change reference. Return result `checked` with the message id. The Change stays released until the principal, with any answer in the Change record, orders **Start** for it.
5. When the Change is terminal, run `spx worktree status`. When it shows the worktree with no running Executor work, use skill `coding-agents:operate-herdr` for one `stop` of the pane with `"mutationAuthorized": true`, which ends the Executor session and leaves the pane at its shell, and return result `collected`. When it still shows running work, return result `checked` with that status verbatim; a later Check collects the pane.

</workflow>

<constraints>

- NEVER start a session through any definition other than `change-executor`, and never start a session outside a herdr pane.
- NEVER write, review, or audit an artifact of the Change; the Executor's launched sessions produce and judge every artifact.
- NEVER answer a question that reopens product or architecture judgment; it goes up the chain of positions.
- NEVER poll in a loop; one invocation is one bounded pass.

</constraints>

<output_format>

Return the result — `started`, `checked`, `collected`, `unavailable`, or `stopped` — with the Change URL, the worktree root, the herdr workspace Start named, the pane and agent name, each herdr result's `status` verbatim, the Executor-session stop acted on or the release reported to the principal, with its message id, and, for `stopped`, the exact report that stopped the workflow.

</output_format>

<success_criteria>

- The winning Claim names the Executor's worktree root, and the one session this skill started there runs the `change-executor` definition with the structured-question tool withheld on start and on every relaunch.
- The Executor's worktree came from one `create-worktree` or `open-worktree` grouped with the herdr workspace Start named, never from a raw Git or herdr command.
- Every stall, compaction, and relaunch was one bounded operation, a restart relaunched into the pane its stop kept after the Change was claimed again for that worktree, and a relaunched Executor received only the Change's issue reference.
- Every Executor-session stop the Handoff's `Hazards` recorded was acted on, and every other release was reported to the principal once per Handoff, with each question verbatim.
- An Executor session was stopped only after the Change was terminal or released and the worktree carried no running work, and its pane stayed at its shell.

</success_criteria>
