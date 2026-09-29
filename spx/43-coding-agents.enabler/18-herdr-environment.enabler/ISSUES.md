# Issues: Herdr Environment

## Herdr response vocabulary the adapter never reads has no owner

`outcomeeng_testing/harnesses/herdr_environment.py` declares the herdr pane-list and worktree-list field names it reads from captured responses: `PANE_LIST_FIELD` (`panes`), `WORKTREE_LIST_SOURCE_FIELD` (`source`), `WORKTREE_LIST_SOURCE_WORKSPACE_FIELD` (`source_workspace_id`), `WORKTREE_LIST_FIELD` (`worktrees`), `LISTED_OPEN_WORKSPACE_FIELD` (`open_workspace_id`), and `LISTED_LINKED_WORKTREE_FIELD` (`is_linked_worktree`). They are herdr's response protocol, and no source module owns them. The adapter never lists panes or worktrees, so moving the names into `src/plugins/coding-agents/skills/operate-herdr/scripts/herdr_environment.py` would create constants no production path consumes, the shape the entry "Compliance scanners ship inside the environment adapters" in `spx/43-coding-agents.enabler/ISSUES.md` records and `source-ownership` rejects from the other direction. Each placement violates one reading of the same rule.

**Impact**: the stop and worktree-grouping evidence reads herdr's captured pane and worktree lists through names only test infrastructure declares. No source contract states what that evidence depends on, and a herdr rename of one of those fields surfaces only when the fixtures are recaptured.

**Settlement condition**: a decision names the owner of herdr response vocabulary the adapter does not read (the adapter, a separately owned herdr protocol module, or the captured fixture family), and the harness reads those names from that owner.

**Evidence**: `spec-tree:test-evidence-auditor` finding `f-002` on head `7ad28895500e40c4c106c1c510a175a6b52ddda9`, rule `source-ownership`.

## Captured responses whose run's exit code is not recorded

`outcomeeng_testing/fixtures/herdr_environment/provenance.json` records the exit code herdr exited with for each error envelope recaptured together with it. Two error envelopes, `responses/errors/agent-prompt.timeout.json` and `responses/errors/agent-start.agent_not_ready.json`, carry no recorded exit code: recapturing either needs a live agent session in a pane, a prompt whose wait times out or a start blocked during startup. The harness does not replay them. The `timeout` code reaches the evidence through the recaptured wait timeout, and `agent_not_ready` through a captured envelope varied to that code. No success capture records its run's exit code either; the harness replays each at zero, the status the adapter reads as success, and the operation mapping test compares a success result's exit code with that zero.

**Impact**: two real herdr envelopes serve no evidence, and the process status every success replay carries has no captured source.

**Settlement condition**: every response artifact in the family records its run's exit code in the provenance manifest, the two error envelopes and the success captures recaptured with it, and the harness replays no response without a recorded exit code.

**Evidence**: `spec-tree:test-evidence-auditor` finding `f-003` on head `7ad28895500e40c4c106c1c510a175a6b52ddda9`, rule `source-ownership`, which the recapture of seven error envelopes with their exit codes repaired for every error envelope the harness replays.
