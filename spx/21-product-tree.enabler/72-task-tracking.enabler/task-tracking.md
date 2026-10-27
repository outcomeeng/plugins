---
id: 01a1783e-0545-7624-a68a-2e90e7661c81
malleability: spec
---

# Task Tracking

PROVIDES the runtime task-tracking standard — how a workflow keeps repository work alive across heartbeats, timers, and local background work
SO THAT every workflow that waits
CAN choose between ending the turn for a completion notification and collecting the result within the active turn, according to what its agent harness does when background work ends

## Assertions

- ALWAYS: the Claude rendering of `/task-tracking-standards` tells an agent that a backgrounded shell command or an ordinary background subagent re-invokes the session on its completion, so the agent launches it, ends the turn, and resumes from the completion notification ([audit])
- ALWAYS: the Codex rendering of `/task-tracking-standards` tells an agent to run a local command in the foreground with a timeout that covers it and to collect its result within the active turn, or to move the work to the next step boundary, and to collect a subagent launch within the active turn through the native wait capability ([audit])
- NEVER: the Codex rendering of `/task-tracking-standards` tells an agent that the harness re-invokes the session when background work ends ([audit])
