# Issues: Change Execution

## The Codex renderings of the five definitions carry no retained invocation

**Evidence**: `/subagent-standards` requires each subagent definition without declared per-harness release acceptance to retain its exact-definition minimal isolated invocation, per `spx/43-instructions.enabler/21-subagents.enabler/subagents.md`. The build emits `change-executor`, `change-author`, `change-verifier`, `change-tester` and `change-implementer` for both Claude Code and Codex, and this node retains one minimal isolated invocation of each for Claude Code only.

**Impact**: the Codex renderings load and run unobserved. `/orchestrate-change` returns an explicit unavailable result on Codex and starts no Executor there, so no Codex session reaches these definitions through the supported path.

**Settlement condition**: a Codex Executor start exists, and each definition's Codex rendering retains its own minimal isolated invocation.
