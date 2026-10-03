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

## The Executor's `gh api graphql` grant admits store mutations

**Evidence**: `instructions:skill-auditor` finding f-009, severity `WARNING`, against `src/plugins/spec-tree/skills/execute-change/SKILL.md:6`, in the typed skill audit of head `c4ed94bfc0c440a7d0f0a55c0a8b541a0d67de49`. The grant `Bash(gh api graphql:*)` admits issue-field mutations as well as the field and successor reads `canonical-state` requires, while the skill's first constraint limits its session to deterministic commands, integration, and Lifecycle recorded through the Lifecycle skills, which carry their own `gh api graphql` grants.

**Impact**: the Executor's approved surface can change store state outside `/claim-change`, `/release-change` and `/close-change`.

**Settlement condition**: the grant is narrowed to the read forms the Executor runs, and a retained invocation shows the harness admits those reads under the narrowed patterns without a prompt. The matcher's treatment of a pattern that is not a literal prefix of the issued command is the open question recorded in `spx/ISSUES.md` under "A skill-directory token inside an `allowed-tools` pattern may never match".
