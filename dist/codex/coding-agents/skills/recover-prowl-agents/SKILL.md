---
name: recover-prowl-agents
description: >-
  ALWAYS invoke this skill when preparing or executing recovery of coding-agent sessions after Prowl restarts.
argument-hint: "<JSON recovery candidates>"
allowed-tools: Read, Skill, Bash(printf:*), Bash(python3 "${SKILL_DIR}/scripts/recover_agents.py":*), request_user_input
---

<objective>
A bounded recovery plan for exact restored Prowl panes whose expected native sessions have pre-restart liveness evidence or explicit operator confirmation, followed by one complete identity correlation result.
</objective>

<dependencies>

- Python 3.13+, the plugin's published shipped-script interpreter floor.
- `/operate-prowl` for every public Prowl operation.
- `spx agent resume --latest` as the sole native runtime selector inside the source-owned recovery input.
- One durable candidate record supplied through `$ARGUMENTS`, containing complete pane, worktree, native-session, evidence, role, and secondary-authorization values.

</dependencies>

<workflow>

1. Interpret `$ARGUMENTS` as the durable candidate record captured before restart. Each candidate MUST contain complete `paneId`, absolute `worktreePath`, `sessionId`, `evidence`, `role`, and `secondaryAuthorized` fields. `evidence` is `live-process` only when the pre-restart observation proved a running native process; use `operator-confirmed` only when the operator explicitly identifies that exact pane and session.
2. Reject a candidate derived only from a pane roster entry, terminal presentation, saved transcript, rollout path, session-file recency, or post-restart inference. Those observations preserve possible recovery context but prove neither prior liveness nor intent to resume.
3. Reconcile candidates by worktree before mutation. One candidate is `primary`. Multiple candidates for one worktree require exactly one primary, distinct complete session identities, and `secondaryAuthorized: true` on every secondary after explicit operator authorization. Otherwise stop with the complete conflicting identities.
4. Invoke `/operate-prowl` for `list` and `agents`. Require a checked successful result from each and preserve their complete public response values. Prowl remains the sole authority for restored topology.
5. Correlate every candidate to its exact restored pane and worktree. Retain a pane already occupied by the expected `claude` or `codex` session as already correlated. Reject absent panes, non-native occupants, mismatched sessions, duplicate session identities, and multiple correlations without partial delivery.
6. Pass the public `items` and `agents` arrays plus the exact `candidates` array to the bundled script over stdin and run `recover`, repeating `--pane` for every candidate pane UUID. When no eligible candidate remains, stop without mutation.
7. Read the plan exactly: `resumed` carries one semantic delivery for every selected unoccupied pane; `already-current` carries no delivery; `invalid-target`, `pane-occupied`, or `invalid-schema` stops with exact detail and no partial delivery.
8. For every planned delivery, invoke `/operate-prowl` once for `send` using the complete `paneId`, exact `text`, and immediate-return mode. Bind that planned `paneId` to the complete checked environment result under `transport`; NEVER derive or supply a separate delivered claim. Add no retry or polling phase.
9. Pass the plan and ordered `{paneId, transport}` delivery results to `settle`. Accept only `resumed` or `already-current`; `command-failed` reports every exact failed pane and environment result.
10. Invoke `/operate-prowl` for `list` and `agents` exactly once more. Pass those arrays and the unchanged candidates to `verify`. Accept only `verified`, which requires one native agent with the expected session identity in every selected pane. For `correlation-incomplete`, report complete `missingPaneIds`, `duplicatePaneIds`, and `unexpectedAgentPaneIds` values without polling or retrying.

The source-owned recovery input contains `spx agent resume --latest`, the expected complete session identity, the authorized recovery role, and the reassessment instruction. The resumed session verifies its identity and inspects authoritative repository and SPX state. Concrete unfinished work with continuing authority proceeds; completed, superseded, `owned_elsewhere`, deliberately terminated, identity-mismatched, or unclear work exits without mutation or background activity.

</workflow>

<command_forms>

When the shell accepts multiline input:

```bash
python3 "${SKILL_DIR}/scripts/recover_agents.py" recover --pane <complete-pane-uuid> <<'JSON'
{"items":[],"agents":[],"candidates":[]}
JSON

python3 "${SKILL_DIR}/scripts/recover_agents.py" settle <<'JSON'
{"plan":{},"deliveryResults":[{"paneId":"<complete-pane-uuid>","transport":{"schemaVersion":1,"operation":"send","status":"succeeded","commandExitCode":0,"response":{}}}]}
JSON

python3 "${SKILL_DIR}/scripts/recover_agents.py" verify --pane <complete-pane-uuid> <<'JSON'
{"items":[],"agents":[],"candidates":[]}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"items":[],"agents":[],"candidates":[]}' | python3 "${SKILL_DIR}/scripts/recover_agents.py" recover --pane <complete-pane-uuid>
printf '%s\n' '{"plan":{},"deliveryResults":[{"paneId":"<complete-pane-uuid>","transport":{"schemaVersion":1,"operation":"send","status":"succeeded","commandExitCode":0,"response":{}}}]}' | python3 "${SKILL_DIR}/scripts/recover_agents.py" settle
printf '%s\n' '{"items":[],"agents":[],"candidates":[]}' | python3 "${SKILL_DIR}/scripts/recover_agents.py" verify --pane <complete-pane-uuid>
```

</command_forms>

<constraints>

- ALWAYS route every public environment operation through `/operate-prowl`.
- NEVER persist or reconstruct Prowl pane topology — Prowl owns it.
- NEVER create, restore, focus, or close a pane during recovery.
- NEVER select by title, focus, position, worktree path alone, pane presentation, saved transcript, rollout path, or inferred session identity; require the complete candidate contract.
- NEVER resume two candidates for one worktree without one primary, distinct session identities, and explicit authorization for every secondary.
- NEVER type into an occupied, unselected, mismatched-session, or ambiguous pane.
- NEVER inspect private transcript content to infer liveness or continuation; saved history is not process evidence.
- NEVER start a watcher, polling loop, daemon, background process, or open-ended wait.
- NEVER treat planning, delivery, correlation, or reassessment as workflow success, retry selection, checkpoint restoration, or continuation authority.
- NEVER reproduce credentials or secrets visible in pane evidence; stop and report the exposure without quoting the value.

</constraints>

<testing>

Before release, call `recover(selected_pane_ids, pane_items, agent_items, candidate_items)`, `settle_recovery(plan, delivery_results)`, and `verify(selected_pane_ids, pane_items, agent_items, candidate_items)` with generated public roster domains. Exercise CLI dispatch for `recover`, `settle`, and `verify` with stdin payloads.

The matrix covers unoccupied, already-correlated, absent, duplicate, non-native, and multiply occupied pane targets; unsupported liveness evidence; duplicate worktrees; authorized secondaries; duplicate and mismatched session identities; absolute-path preservation; one source-owned recovery delivery per unoccupied target; failed environment delivery without partial success; complete post-launch correlation; malformed public payloads; and repeated already-current recovery with no delivery.

</testing>

<example>

A pre-restart record contains one primary session and one intentional verifier in the same worktree. Preserve both only after the operator authorizes the verifier as a secondary:

```json
{ "candidates": [{ "paneId": "<primary-pane>", "worktreePath": "<absolute-worktree>", "sessionId": "<primary-session>", "evidence": "live-process", "role": "primary", "secondaryAuthorized": false }, { "paneId": "<verifier-pane>", "worktreePath": "<absolute-worktree>", "sessionId": "<verifier-session>", "evidence": "live-process", "role": "secondary", "secondaryAuthorized": true }] }
```

Run `recover`, deliver each planned input once, run `settle`, then run `verify` with the unchanged candidates. A verifier missing its expected session identity yields `correlation-incomplete`; never replace that result with repeated reads.

</example>

<failure_modes>

**A saved rollout was treated as a live pre-restart session.** Claude revived an idle historical session because its rollout file existed even though no native process was running. The resumed session found its work already merged and classified itself `owned_elsewhere`. Require `live-process` evidence or explicit operator confirmation; saved history alone never enters the candidate set.

**Two sessions from one worktree were resumed without reconciliation.** Claude revived an older coding session beside the current coordinating session because both panes remained visible. Both processes inspected one checkout and could have raced on its branch. Require one primary per worktree and explicit authorization for every distinct secondary.

**One native session ran in two panes.** Claude resumed the same session identity twice after a restored pane and a later agent launch converged on one transcript. Concurrent writers could corrupt session state and issue commands from different working directories. Reject duplicate session identities before delivery and require exact session correlation after launch.

</failure_modes>

<success_criteria>

- Recovery planning passes only with `status` equal to `resumed` or `already-current`; every target preserves complete pane, worktree, expected session, evidence, and role identity.
- Every resumed target receives exactly one source-owned recovery input through `/operate-prowl`; an already-correlated target receives none.
- Verification passes only with `status: "verified"`, one expected distinct native-session correlation per selected pane, and empty missing, duplicate, and unexpected arrays.
- Any invalid target, occupied pane, incomplete correlation, invalid schema, unavailable environment, or failed delivery preserves exact details and identities.
- SPX alone selects the native runtime and session, and each newly resumed session owns the continue-or-exit decision.

</success_criteria>
