# Issues: Change Execution

## The five definitions ship for Claude Code only

**Evidence**: `/subagent-standards` requires each subagent definition without declared per-harness release acceptance to retain its exact-definition minimal isolated invocation, per `spx/43-instructions.enabler/21-subagents.enabler/subagents.md`. This node retains one such invocation of `change-executor`, `change-author`, `change-verifier`, `change-tester` and `change-implementer` for Claude Code, in `probes/definition-invocation/probe.md`, and the build emits no Codex rendering of them.

**Impact**: a Codex session cannot execute a Change: `/orchestrate-change` Start and `/execute-change` return an explicit unavailable result on Codex.

**Settlement condition**: a Codex Executor start exists, the five definitions list Codex among their targets, and each Codex rendering retains its own minimal isolated invocation.
