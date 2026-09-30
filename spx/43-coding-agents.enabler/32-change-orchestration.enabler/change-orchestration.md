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

- ALWAYS: `/orchestrate-change` claims one Change for its Executor, naming the Executor's worktree root, and starts one Executor session for it in a herdr pane through `spx/43-coding-agents.enabler/18-herdr-environment.enabler`; on Claude Code the session starts with the spec-tree definition `change-executor` selected, and on Codex the skill returns an explicit unavailable result ([audit])
- ALWAYS: the Executor session's start and every resume withhold the harness's structured-question tool through the harness setting alone; no skill detects whether its session is an Executor ([audit])
- ALWAYS: `/orchestrate-change` names `change-executor` as the one configured definition it starts, and starts no session through any other definition ([audit])
- ALWAYS: a start the harness's classifier refuses is retried once as one command per step with no shell variables, and a second refusal passes to the position holder with the operator's conversation ([audit])
- ALWAYS: the Orchestrator checks each Executor at regular intervals and, finding one stalled or near its context limit, prompts, compacts or restarts it; a restarted Executor continues from the Change and its latest Handoff ([audit])
- ALWAYS: the Orchestrator answers the questions its scope settles, by Priority, and passes every other question up the chain of positions as message records of `spx/43-coding-agents.enabler/21-agent-communication.enabler` ([audit])
- NEVER: the Orchestrator acts as a Verifier ([audit])
