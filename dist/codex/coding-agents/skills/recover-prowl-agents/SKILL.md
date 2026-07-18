---
name: recover-prowl-agents
description: >-
  ALWAYS invoke this skill when Prowl has restored panes whose stopped coding-agent sessions may need recovery.
allowed-tools: Bash(prowl list --json), Bash(prowl agents --json), Bash(prowl read --pane * --last 80 --wait-stable --json), Bash(python3 "${SKILL_DIR}/scripts/recover_agents.py":*), request_user_input
---

<objective>
A bounded recovery result and a complete post-launch correlation result for exact restored Prowl panes, with SPX selecting each native session and each resumed session re-evaluating whether work should continue or exit.
</objective>

<dependencies>

- Python 3.13+, the plugin's published shipped-script interpreter floor.
- The public `prowl` CLI.
- `spx agent resume --latest` as the sole native runtime and session selector.

</dependencies>

<workflow>

1. Run `prowl list --json` and `prowl agents --json`. Treat Prowl as the sole authority for restored pane topology.
2. Partition live panes by public agent correlation:
   - Retain a pane with exactly one detected `claude` or `codex` agent as an already-correlated target. Read no screen evidence and send no recovery input to establish its status.
   - Exclude a pane occupied by a non-native agent or carrying multiple detected-agent correlations; report its complete identity rather than attempting partial recovery.
   - Treat an unoccupied Git-worktree pane that may have hosted a stopped coding-agent session as a recovery candidate. Read only bounded public screen evidence with `prowl read --pane <complete-pane-uuid> --last 80 --wait-stable --json`.
3. Add an unoccupied candidate only when its complete UUID and visible evidence make the stopped coding-agent session obvious, or when the operator explicitly names that pane. An ordinary shell, conflicting evidence, or uncertain intent remains stopped. Present ambiguous panes through `request_user_input` with their complete pane and worktree identities; never guess.
4. Build one target set from retained already-correlated panes plus selected unoccupied panes. When the set is empty, report that no recovery target was selected and stop without mutation. Retained already-correlated panes remain in the set so a repeated run reaches the adapter's `already-current` result.
5. Run one bounded recovery command, repeating `--pane` for every complete UUID in the target set:

```text
python3 "${SKILL_DIR}/scripts/recover_agents.py" recover --pane <pane-uuid> [--pane <pane-uuid> ...]
```

6. Read the JSON result exactly:
   - `resumed` reports every complete target and establishes launch transport only.
   - `already-current` reports every complete target and sends nothing.
   - `invalid-target`, `pane-occupied`, `invalid-schema`, `prowl-unavailable`, or `command-failed` stops with the exact `status` and `detail`.
7. Run verification exactly once against the same pane UUIDs:

```text
python3 "${SKILL_DIR}/scripts/recover_agents.py" verify --pane <pane-uuid> [--pane <pane-uuid> ...]
```

8. Accept only `verified`. For `correlation-incomplete`, report complete `missingPaneIds`, `duplicatePaneIds`, and `unexpectedAgentPaneIds` values without polling or retrying.

The adapter submits `spx agent resume --latest`, a newline, and the source-owned reassessment instruction as one ordered Prowl input to each selected unoccupied pane. Prowl therefore accepts or rejects the complete recovery input as one transport operation. The resumed session inspects its prior conversation and authoritative current repository and SPX state. Concrete unfinished work with continuing authority proceeds; completed work, deliberate termination, or unclear continuation exits without mutation or background activity.

</workflow>

<testing>

Before release, call the importable `recover(selected_pane_ids, runner)` and `verify(selected_pane_ids, runner)` entrypoints with an injected recording runner, then exercise CLI dispatch through `main(["recover", "--pane", pane_id])` and `main(["verify", "--pane", pane_id])`.

The release matrix covers:

- one selected unoccupied pane -> `resumed`, one exact-pane send, and one atomic `RECOVERY_INPUT`;
- one selected already-correlated pane -> `already-current` and no send;
- absent or duplicate selected pane identity -> `invalid-target` and no send;
- non-native or multiple detected-agent occupancy -> `pane-occupied`, one complete pane/worktree target per occupied pane, and no partial send;
- malformed public Prowl payload -> `invalid-schema`;
- unavailable Prowl command -> `prowl-unavailable`;
- rejected atomic input -> `command-failed` after exactly one send attempt;
- one native-agent correlation per selected pane -> `verified` with complete correlations;
- missing, duplicate, or unexpected correlation -> `correlation-incomplete` with the corresponding complete pane-identity arrays;
- every case -> recorded calls contain only `PROWL_LIST_COMMAND`, `PROWL_AGENTS_COMMAND`, or `recovery_send_command(selected_pane_id)`; any other command fails the release check.

</testing>

<failure_modes>

<failure name="ambiguous pane evidence selected for recovery">

**What happened:** Claude could mistake an ordinary shell or conflicting visible state for a stopped coding-agent session.

**Why it failed:** Pane presence proves topology, not prior session intent; inference would type recovery instructions into a pane whose continuation authority is unknown.

**How to avoid:** Leave ambiguous panes stopped and present their complete pane and worktree identities through `request_user_input` before adding them to the target set.

</failure>

<failure name="occupied pane received recovery input">

**What happened:** Claude risked sending native-session recovery into a pane held by a non-native process by treating every restored pane as unoccupied.

**Why it failed:** Prowl occupancy is authoritative, and partial recovery after detecting invalid occupancy can mutate only part of a target set.

**How to avoid:** Retain exactly one correlated `claude` or `codex` agent as idempotent, but exclude non-native or multiple-agent occupancy before the bounded recovery call.

</failure>

<failure name="launch accepted without complete correlation">

**What happened:** Claude could report transport acceptance as recovery success before every selected pane exposed one correlated native agent.

**Why it failed:** Launch transport does not prove that SPX resumed a session or that Prowl correlated the resulting process to the intended pane.

**How to avoid:** Run `verify` once for the same complete pane UUIDs and accept only `verified`; report every complete missing, duplicate, and unexpected pane identity from `correlation-incomplete`.

</failure>

<failure name="resumed process continued without authority">

**What happened:** Claude could keep a recovered process active merely because `spx agent resume --latest` launched it, even when its prior workflow had completed or stopped deliberately.

**Why it failed:** Runtime and session selection establish no unfinished work, checkpoint, retry, workflow success, or continuation authority.

**How to avoid:** Deliver the reassessment instruction atomically with the resume command and require completed, deliberately terminated, or unclear work to exit without mutation or background activity.

</failure>

</failure_modes>

<constraints>

- NEVER persist or reconstruct Prowl pane topology — Prowl owns it.
- NEVER create, restore, focus, or close a pane during recovery.
- NEVER select by title, focus, position, worktree path alone, or inferred session identity; use the complete pane UUID plus public evidence.
- NEVER type into an occupied, unselected, or ambiguous pane.
- NEVER inspect private runtime storage or transcript files; SPX owns session discovery and selection.
- NEVER start a watcher, polling loop, daemon, background helper, or open-ended wait.
- NEVER treat launch, correlation, or reassessment as workflow success, retry selection, checkpoint restoration, or continuation authority.
- NEVER reproduce credentials or secrets visible in pane evidence; stop and report the exposure without quoting the value.

</constraints>

<success_criteria>

- `recover` passes only with `status` equal to `resumed` or `already-current`; every returned target preserves its complete pane and worktree identity, and every `resumed` target reports `command: "spx agent resume --latest"` plus `reassessmentSent: true`.
- `verify` passes only with `status: "verified"`, `verified` equal to the selected-pane count, one complete correlation per selected pane, and empty `missingPaneIds`, `duplicatePaneIds`, and `unexpectedAgentPaneIds` arrays.
- Any `invalid-target`, `pane-occupied`, `correlation-incomplete`, `invalid-schema`, `prowl-unavailable`, or `command-failed` result fails the corresponding operation and preserves its exact `detail` or correlation arrays.
- Prowl remains the only durable pane-topology authority, every launch uses the selected complete pane UUID, and SPX alone selects the native runtime and session through `spx agent resume --latest`.
- Every newly resumed session receives exactly one reassessment instruction and owns the continue-or-exit decision.
- Repeating recovery against already-correlated selected panes sends nothing.

</success_criteria>
