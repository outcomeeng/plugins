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

## The decision and the spec give a pane-less incomplete item a pane

The incomplete-item invariant in `spx/43-coding-agents.enabler/18-herdr-environment.enabler/21-herdr-adapter.adr.md` (line 26) projects an agent whose evidence lacks a projected field to a named incomplete item "carrying its pane, every projected field its evidence carries, and the names of the missing fields", and the agent-evidence mapping in `spx/43-coding-agents.enabler/18-herdr-environment.enabler/herdr-environment.md` (line 19) states the same item "carrying its pane". The pane is itself a projected field, `pane_id`, so evidence that lacks it has no pane to carry. `_participant` in `src/plugins/coding-agents/skills/operate-herdr/scripts/herdr_environment.py` projects such evidence to an item with no pane and names `pane_id` under `missingFields`, as its docstring states (lines 785–792). `incomplete_agent_variants` in `outcomeeng_testing/generators/herdr_environment.py` (lines 55–75) drops the pane among its subsets, `test_inventory_maps_every_agent_in_full_or_to_its_named_incomplete_item` in `spx/43-coding-agents.enabler/18-herdr-environment.enabler/tests/test_herdr_environment.mapping.l1.py` asserts the pane-less item for every such subset (lines 504–519), and workflow step 5 of `src/plugins/coding-agents/skills/operate-herdr/SKILL.md` (line 92) describes the incomplete item as "the fields its evidence carries". The implementation, the generator, the test, and the skill agree with one another; the decision and the spec disagree with all four on the pane-missing case.

**Impact**: a reader of the decision or the spec expects every incomplete item to carry a pane and to be addressable by it, while the adapter returns an item with none that no pane selector reaches. The mapping evidence verifies a rule the spec assertion it backs does not state, so the declaration and its evidence describe two different projections.

**Settlement condition**: one rule governs the pane-missing case in every layer. Either the decision and the spec state that an item whose evidence lacks the pane carries no pane and names `pane_id` among its missing fields, or the projection requires `pane_id` and rejects evidence without it; the generator, the mapping test, and the `/operate-herdr` skill text state and exercise that same rule.

**Evidence**: `spec-tree:changes-reviewer` run `2026-09-29_07-52-21-574-3e4ad71a1ae1` on head `af92dcd523770e15497e9b8bc2e8a3622d91f96b`, status `approved`, a consistency finding at severity `debt` against `src/plugins/coding-agents/skills/operate-herdr/scripts/herdr_environment.py:788`; every line number above is taken at that head.

## A session-ending command followed by words passes the prompt gate

The adapter gates a prompt as it gates stop only when the prompt's text, stripped of surrounding whitespace, is exactly a member of `AGENT_SESSION_ENDING_TEXTS`, `/exit` or `/quit` (`src/plugins/coding-agents/skills/operate-herdr/scripts/herdr_environment.py`, declared at line 57, tested at line 614). A prompt whose text opens with either command and carries trailing words, such as `/exit now` or `/quit please`, runs without mutation authorization. No captured behaviour establishes whether Claude Code or Codex ends its session on `/exit <args>` or `/quit <args>`. `test_a_prompt_carrying_the_stop_exit_runs_no_command_without_authorization` in `spx/43-coding-agents.enabler/18-herdr-environment.enabler/tests/test_herdr_environment.compliance.l1.py` builds its longer-message case by appending the command after other text (lines 77–92), so the leading-command form appears in no case, conforming or violating. The exact-match wording recurs in `spx/43-coding-agents.enabler/18-herdr-environment.enabler/21-herdr-adapter.adr.md` (lines 7, 34, and 44), the compliance assertion of `spx/43-coding-agents.enabler/18-herdr-environment.enabler/herdr-environment.md` (line 29), `src/plugins/coding-agents/skills/operate-herdr/SKILL.md` (lines 22, 32, 89, 127, 152, and 165), and `src/plugins/coding-agents/skills/orchestrate-officers/references/standing-rules.md` (lines 52–54) and `src/plugins/coding-agents/skills/orchestrate-officers/workflows/housekeep.md` (lines 27–28).

**Impact**: if either agent ends its session on a session-ending command followed by arguments, a prompt that carries no authorization ends an officer session, the outcome the gate exists to prevent, while every layer that states the gate presents it as complete.

**Settlement condition**: captured Claude Code and Codex behaviour establishes whether `/exit <args>` and `/quit <args>` end the session. If either does, every prompt whose first whitespace-delimited token is a session-ending command is gated, and the decision, the spec, the `/operate-herdr` and officer skill text, and the compliance test state that rule and exercise the leading-command case. If neither does, the decision states that finding and the compliance test carries the leading-command case as a conforming example.

**Evidence**: `spec-tree:changes-reviewer` run `2026-09-29_07-52-21-574-3e4ad71a1ae1` on head `af92dcd523770e15497e9b8bc2e8a3622d91f96b`, status `approved`, a security finding at severity `debt` against `src/plugins/coding-agents/skills/operate-herdr/scripts/herdr_environment.py:614`; every line number above is taken at that head.

## No capture shows open-worktree for a checkout herdr already has open

`src/plugins/coding-agents/skills/operate-herdr/SKILL.md` states for `open-worktree`, at line 34, that the new workspace "is never the named one", and its testing record at line 145 claims captured open responses yield "a workspace other than the named one". The open-worktree invariant in `spx/43-coding-agents.enabler/18-herdr-environment.enabler/21-herdr-adapter.adr.md` (line 9, and the open-worktree invariant under `## Invariants`) states that herdr opens every opened worktree as its own workspace and that the result never carries the named workspace. The one captured open response, `outcomeeng_testing/fixtures/herdr_environment/responses/worktree-open.json`, carries `already_open: false`, a field the adapter never reads. No captured herdr response shows what `herdr worktree open` returns for a checkout herdr already has open, so what the result carries in that case (the existing workspace, a new one, the named one, or an error) is unestablished.

**Impact**: a workflow that opens a checkout herdr already has open relies on a workspace and root pane the skill and the decision promise and no evidence shows. It can address a pane herdr did not open for that request, or treat as fresh a workspace another agent session already occupies.

**Settlement condition**: a live `herdr` 0.9.1 capture of `open-worktree` for a checkout herdr already has open joins the fixture family with its provenance, and the `/operate-herdr` skill text and the decision's open-worktree invariant state what that capture shows.

**Evidence**: `spec-tree:changes-reviewer` run `2026-09-29_08-45-32-122-cb34c99a7af7` on head `bf03df3c772699d0d467b0883e923222389b3aee`, finding `D1`, against `src/plugins/coding-agents/skills/operate-herdr/SKILL.md:34` and `:145`; line numbers are taken at that head.
