# Issues: Change Execution

## The seven definitions ship for Claude Code only

**Evidence**: `/subagent-standards` requires each subagent definition without declared per-harness release acceptance to retain its exact-definition minimal isolated invocation, per `spx/43-instructions.enabler/21-subagents.enabler/subagents.md`. The build emits no Codex rendering of `change-executor`, `change-author`, `change-verifier`, `change-tester`, `change-implementer`, `change-skill-author` and `change-subagent-author`.

**Impact**: a Codex session cannot execute a Change: `/orchestrate-change` Start and `/execute-change` return an explicit unavailable result on Codex.

**Settlement condition**: a Codex Executor start exists, the seven definitions list Codex among their targets, and each Codex rendering retains its own minimal isolated invocation.

## The two instruction round definitions have no retained invocation

**Evidence**: `probes/definition-invocation/probe.md` retains one invocation of each of `change-executor`, `change-author`, `change-verifier`, `change-tester` and `change-implementer` for Claude Code. No retained run launches `change-skill-author` or `change-subagent-author`, and the probe assertion names all seven definitions.

**Impact**: the probe assertion has no current attested result, so the node merges as Declared until the protocol covers the two definitions.

**Settlement condition**: `probes/definition-invocation/probe.md` covers `change-skill-author` and `change-subagent-author`, and a retained attested run of the protocol records each definition loading natively, starting as the child session of one launch by its exact name, and returning a result its fronted skill or its own workflow declares.

## The Executor's session start through `--agent` is unobserved

**Evidence**: `probes/definition-invocation/probe.md` launches each of the five definitions as a child of one `Agent` call. `/orchestrate-change` starts the Executor another way: it starts a new Claude Code session in a herdr pane with `--agent` naming `change-executor` and `--disallowedTools` withholding the structured-question tool. No retained run shows a session started that way loading `change-executor`, preloading `/execute-change`, and running without the structured-question tool.

**Impact**: the Executor start is the one launch path every Change execution takes, and it is also the path the harness's classifier refused twice in orchestration sessions. A defect there, such as a definition that does not load as a main-session agent, surfaces only when the first Change is executed.

**Settlement condition**: a retained run in which a session started with `--agent` naming the emitted `change-executor` and the structured-question tool withheld reports that definition as its agent, lacks the structured-question tool, and returns a result `/execute-change` declares.
