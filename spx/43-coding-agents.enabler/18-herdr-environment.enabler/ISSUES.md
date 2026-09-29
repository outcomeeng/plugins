# Issues: Herdr Environment

## Herdr response vocabulary the adapter never reads has no owner

`outcomeeng_testing/harnesses/herdr_environment.py` declares the herdr pane-list and worktree-list field names it reads from captured responses: `PANE_LIST_FIELD` (`panes`), `WORKTREE_LIST_SOURCE_FIELD` (`source`), `WORKTREE_LIST_SOURCE_WORKSPACE_FIELD` (`source_workspace_id`), `WORKTREE_LIST_FIELD` (`worktrees`), `LISTED_OPEN_WORKSPACE_FIELD` (`open_workspace_id`), and `LISTED_LINKED_WORKTREE_FIELD` (`is_linked_worktree`). They are herdr's response protocol, and no source module owns them. The adapter never lists panes or worktrees, so moving the names into `src/plugins/coding-agents/skills/operate-herdr/scripts/herdr_environment.py` would create constants no production path consumes, the shape the entry "Compliance scanners ship inside the environment adapters" in `spx/43-coding-agents.enabler/ISSUES.md` records and `source-ownership` rejects from the other direction. Each placement violates one reading of the same rule.

**Impact**: the stop and worktree-grouping evidence reads herdr's captured pane and worktree lists through names only test infrastructure declares. No source contract states what that evidence depends on, and a herdr rename of one of those fields surfaces only when the fixtures are recaptured.

**Settlement condition**: a decision names the owner of herdr response vocabulary the adapter does not read (the adapter, a separately owned herdr protocol module, or the captured fixture family), and the harness reads those names from that owner.

**Evidence**: `spec-tree:test-evidence-auditor` finding `f-002` on head `7ad28895500e40c4c106c1c510a175a6b52ddda9`, rule `source-ownership`.

## Captured responses whose run's exit code is not recorded

`outcomeeng_testing/fixtures/herdr_environment/provenance.json` records the exit code herdr exited with for every error envelope in the family. No success capture records its run's exit code; the harness replays each at zero, the status the adapter reads as success, and the operation mapping test compares a success result's exit code with that zero.

**Impact**: the process status every success replay carries has no captured source.

**Settlement condition**: every response artifact in the family records its run's exit code in the provenance manifest, the success captures recaptured with it, and the harness replays no response without a recorded exit code.

**Evidence**: `spec-tree:test-evidence-auditor` finding `f-003` on head `7ad28895500e40c4c106c1c510a175a6b52ddda9`, rule `source-ownership`, which the recapture of seven error envelopes with their exit codes repaired for every error envelope the harness replays.

## The `/operate-herdr` surface carries three standing skill-audit warnings

An approving skill audit of `src/plugins/coding-agents/skills/operate-herdr` raises three warnings that no must-fix finding accompanies:

- **`f-007`, rule `internal-consistency`**, `src/plugins/coding-agents/skills/operate-herdr/SKILL.md:27`: the `<operation_surface>` row for `create-worktree` lists `path` as optional, while line 36, `<workflow>` step 3 at line 89, the constraint at line 128, and the success criterion at line 166 require an absolute `path` on every `create-worktree`.
- **`f-008`, rule `script-validation-messages`**, `src/plugins/coding-agents/skills/operate-herdr/scripts/herdr_environment.py:561` and `:678`: the rejections of an invalid agent state and of an invalid read source name only the location. Neither echoes the rejected value or lists the valid `AgentState` or `ReadSource` members, unlike the argument rejection at line 694, which names the rejected argument and the valid arguments.
- **`f-009`, rule `caller-independence`**, `src/plugins/coding-agents/skills/operate-herdr/SKILL.md:164`: the success criterion says each projected herdr error code "reaches the caller as its named status" instead of stating a property of the result itself.

**Impact**: under `f-007`, a reader who takes the operation table as the request contract builds a `create-worktree` without `path`, which the workflow, the constraint, and the success criterion forbid; the table and the prose give two answers to one question. Under `f-008`, a caller holding either rejection cannot tell which value was refused or which values the adapter accepts without reading the herdr response or the script. Under `f-009`, the criterion is judged by whether a caller receives the status, so it cannot be checked against the result alone.

**Settlement condition**: each warning settles on its own. `f-007` settles when the `create-worktree` row of `<operation_surface>` states the same `path` rule as the skill's workflow, constraints, and success criteria. `f-008` settles when the agent-state and read-source rejections each carry the rejected value and the valid `AgentState` or `ReadSource` members, in the shape the argument rejection already uses. `f-009` settles when the success criterion states the result's own property, each projected herdr error code carried as its named status with the code and message verbatim, and names no caller.

**Evidence**: `instructions:skill-auditor` round-3 audit of `src/plugins/coding-agents/skills/operate-herdr` on head `6dc4bce4043f8b60b5602424fdd943cf4d4d6e6a`, verdict `APPROVED` with no must-fix finding, warnings `f-007`, `f-008`, and `f-009`; every line number above is taken at head `3b1732d8c2234850be6334c98ef87f2df6cba99b`.
