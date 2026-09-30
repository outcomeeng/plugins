# Issues: Change Execution

## The five definitions ship for Claude Code only

**Evidence**: `/subagent-standards` requires each subagent definition without declared per-harness release acceptance to retain its exact-definition minimal isolated invocation, per `spx/43-instructions.enabler/21-subagents.enabler/subagents.md`. This node retains one such invocation of `change-executor`, `change-author`, `change-verifier`, `change-tester` and `change-implementer` for Claude Code, in `probes/definition-invocation/probe.md`, and the build emits no Codex rendering of them.

**Impact**: a Codex session cannot execute a Change: `/orchestrate-change` Start and `/execute-change` return an explicit unavailable result on Codex.

**Settlement condition**: a Codex Executor start exists, the five definitions list Codex among their targets, and each Codex rendering retains its own minimal isolated invocation.

## The Executor's session start through `--agent` is unobserved

**Evidence**: `probes/definition-invocation/probe.md` launches each of the five definitions as a child of one `Agent` call. `/orchestrate-change` starts the Executor another way: it starts a new Claude Code session in a herdr pane with `--agent` naming `change-executor` and `--disallowedTools` withholding the structured-question tool. No retained run shows a session started that way loading `change-executor`, preloading `/execute-change`, and running without the structured-question tool.

**Impact**: the Executor start is the one launch path every Change execution takes, and it is also the path the harness's classifier refused twice in orchestration sessions. A defect there, such as a definition that does not load as a main-session agent, surfaces only when the first Change is executed.

**Settlement condition**: a retained run in which a session started with `--agent` naming the emitted `change-executor` and the structured-question tool withheld reports that definition as its agent, lacks the structured-question tool, and returns a result `/execute-change` declares.
