---
id: 01a0f110-cfe6-70b6-8a53-a0deaf6c0c97
malleability: spec
---

# Change Orchestration

PROVIDES the Orchestrator position's duties for one Change — claiming it for an Executor, starting that Executor's agent session, checking its progress, and passing questions up the chain of positions
SO THAT an operator
CAN have each Executable Change executed by its own Executor session without opening that session's pane

The Orchestrator is a position, never one of the five Roles: it holds no Role for the Change it orchestrates and produces no artifact of it. The Executor it starts holds the Change and executes it through `spx/31-outcomeeng.enabler/32-changes.enabler/65-change-execution.enabler`.

## Assertions

### Compliance

- ALWAYS: `/orchestrate-change` claims one Change for its Executor, naming the Executor's worktree root, and starts one Executor session for it in the root pane `spx/43-coding-agents.enabler/18-herdr-environment.enabler` returns when it creates the Executor's worktree, for a root absent from the pool, or opens the existing one, either grouped with the herdr workspace the invocation names; on Claude Code the session starts with the spec-tree definition `change-executor` selected, and on Codex the skill returns an explicit unavailable result ([audit])
- ALWAYS: the Executor session's start and every resume withhold the harness's structured-question tool through the harness setting alone; no skill detects whether its session is an Executor ([audit])
- ALWAYS: `/orchestrate-change` names `change-executor` as the one configured definition it starts, and starts no session through any other definition ([audit])
- ALWAYS: a start the harness's classifier refuses is retried once, only after retracing the refused request, the classifier's reason, and each step that shaped the request, and changed only by the correction that retrace finds; a second refusal stops the start and reports the refused request, the reason, and the Claim still held to the principal the Orchestrator reports to ([audit])
- ALWAYS: the Orchestrator checks each Executor at regular intervals and, finding one stalled or near its context limit, prompts, compacts or restarts it; a restarted Executor relaunches into the pane its stop kept, after the Change is claimed again for that worktree, and continues from the Change and its latest Handoff ([audit])
- ALWAYS: the Orchestrator answers no question the Executor raises; it passes each one verbatim, once per Handoff, to the principal it reports to as a message record of `spx/43-coding-agents.enabler/21-agent-communication.enabler` ([audit])
- NEVER: the Orchestrator acts as a Verifier ([audit])
