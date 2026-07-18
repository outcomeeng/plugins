---
name: recover-prowl-agents
description: >-
  ALWAYS invoke this skill when Prowl has restored panes whose stopped coding-agent sessions may need recovery.
allowed-tools: Read, Skill, Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/recover_agents.py":*), AskUserQuestion
---

<objective>
A bounded recovery plan delivered through `/operate-prowl` and one complete post-launch correlation result for exact restored Prowl panes, with SPX selecting each native session and each resumed session re-evaluating whether work should continue or exit.
</objective>

<dependencies>

- Python 3.13+, the plugin's published shipped-script interpreter floor.
- `/operate-prowl` for every public Prowl operation.
- `spx agent resume --latest` as the sole native runtime and session selector inside the source-owned recovery input.

</dependencies>

<workflow>

1. Invoke `/operate-prowl` for `list` and `agents`. Require a checked successful result from each and preserve their complete public response values. Prowl remains the sole authority for restored pane topology.
2. Partition live panes by public agent correlation:
   - Retain a pane with exactly one detected `claude` or `codex` agent as an already-correlated target. Read no screen evidence and send no recovery input to establish its status.
   - Exclude a pane occupied by a non-native agent or carrying multiple detected-agent correlations; report its complete identity rather than attempting partial recovery.
   - Treat an unoccupied Git-worktree pane that may have hosted a stopped coding-agent session as a recovery candidate. Invoke `/operate-prowl` for one bounded `read` operation using the candidate's complete pane UUID, `last: 80`, and bounded stability options.
3. Add an unoccupied candidate only when its complete UUID and visible evidence make the stopped coding-agent session obvious, or when the operator explicitly names that pane. An ordinary shell, conflicting evidence, or uncertain intent remains stopped. Present ambiguous panes through `AskUserQuestion` with complete pane and worktree identities; never guess.
4. Build one target set from retained already-correlated panes plus selected unoccupied panes. When the set is empty, report that no recovery target was selected and stop without mutation. Retained already-correlated panes remain in the set so a repeated run reaches `already-current`.
5. Pass the public `items` and `agents` arrays to the bundled script over stdin and run `recover`, repeating `--pane` for every complete target UUID.
6. Read the plan exactly:
   - `resumed` carries one semantic delivery for every selected unoccupied pane.
   - `already-current` carries no delivery.
   - `invalid-target`, `pane-occupied`, or `invalid-schema` stops with exact detail and no partial delivery.
7. For every planned delivery, invoke `/operate-prowl` once for `send` using the complete `paneId`, exact `text`, and immediate-return mode. Preserve the exact status and command exit code for each delivery; do not add a retry or polling phase.
8. Pass the plan and ordered delivery results to the bundled script's `settle` operation. Accept only `resumed` or `already-current`; `command-failed` reports every exact failed pane and environment result.
9. Invoke `/operate-prowl` for `list` and `agents` exactly once more. Pass those public arrays to the bundled script's `verify` operation for the same complete target UUIDs.
10. Accept only `verified`. For `correlation-incomplete`, report complete `missingPaneIds`, `duplicatePaneIds`, and `unexpectedAgentPaneIds` values without polling or retrying.

The source-owned recovery input contains `spx agent resume --latest`, a newline, and the reassessment instruction as one ordered input. The resumed session inspects its prior conversation and authoritative current repository and SPX state. Concrete unfinished work with continuing authority proceeds; completed work, deliberate termination, or unclear continuation exits without mutation or background activity.

</workflow>

<command_forms>

When the shell accepts multiline input:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/recover_agents.py" recover --pane <complete-pane-uuid> <<'JSON'
{"items":[],"agents":[]}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"items":[],"agents":[]}' | python3 "${CLAUDE_SKILL_DIR}/scripts/recover_agents.py" recover --pane <complete-pane-uuid>
```

</command_forms>

<constraints>

- ALWAYS route every public environment operation through `/operate-prowl`.
- NEVER persist or reconstruct Prowl pane topology — Prowl owns it.
- NEVER create, restore, focus, or close a pane during recovery.
- NEVER select by title, focus, position, worktree path alone, or inferred session identity; use the complete pane UUID plus public evidence.
- NEVER type into an occupied, unselected, or ambiguous pane.
- NEVER inspect private runtime storage or transcript files; SPX owns session discovery and selection.
- NEVER start a watcher, polling loop, daemon, background process, or open-ended wait.
- NEVER treat planning, delivery, correlation, or reassessment as workflow success, retry selection, checkpoint restoration, or continuation authority.
- NEVER reproduce credentials or secrets visible in pane evidence; stop and report the exposure without quoting the value.

</constraints>

<testing>

Before release, call `recover(selected_pane_ids, pane_items, agent_items)`, `settle_recovery(plan, delivery_results)`, and `verify(selected_pane_ids, pane_items, agent_items)` with generated public roster domains. Exercise CLI dispatch for `recover`, `settle`, and `verify` with stdin payloads.

The matrix covers unoccupied, already-correlated, absent, duplicate, non-native, and multiply occupied pane targets; absolute-path preservation; one source-owned recovery delivery per unoccupied target; failed environment delivery without partial success; complete post-launch correlation; malformed public payloads; and repeated already-current recovery with no delivery.

</testing>

<success_criteria>

- Recovery planning passes only with `status` equal to `resumed` or `already-current`; every target preserves complete pane and worktree identity.
- Every resumed target receives exactly one source-owned recovery input through `/operate-prowl`; an already-correlated target receives none.
- Verification passes only with `status: "verified"`, one complete correlation per selected pane, and empty missing, duplicate, and unexpected arrays.
- Any invalid target, occupied pane, incomplete correlation, invalid schema, unavailable environment, or failed delivery preserves exact details and identities.
- SPX alone selects the native runtime and session, and each newly resumed session owns the continue-or-exit decision.

</success_criteria>
