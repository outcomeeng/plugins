---
name: recover-prowl-agents
description: >-
  ALWAYS invoke this skill when preparing for or recovering coding-agent sessions after a Prowl restart. NEVER restart Prowl without a prepared exact-session manifest.
argument-hint: "<prepare|recover> <absolute-manifest-path>"
allowed-tools: Read, Write, Skill, Bash(printf:*), Bash(python3 "${SKILL_DIR}/scripts/recover_agents.py":*), request_user_input
---

<objective>
A durable pre-restart allowlist or an idempotent post-restart recovery in which every prepared native session has one exact Prowl pane correlation, every non-controller session receives one separately settled continuation instruction, and no unprepared agent is running.
</objective>

<dependencies>

- Python 3.13+, the plugin's published shipped-script interpreter floor.
- `/operate-prowl` for every public Prowl operation.
- A Prowl-native input-ready prompt for any session whose exact identity or launch context is unavailable from high-confidence public process or agent evidence.
- One absolute manifest path supplied through `$ARGUMENTS`.

</dependencies>

<routing>

Parse `$ARGUMENTS` as exactly one mode and one absolute manifest path:

| Mode      | Workflow                                       |
| --------- | ---------------------------------------------- |
| `prepare` | Run `<prepare_workflow>` before Prowl stops.   |
| `recover` | Run `<recover_workflow>` after Prowl restarts. |

Reject an absent mode, unsupported mode, relative path, extra positional value, or a `recover` path that does not contain a schema-5 `prepared` manifest.

</routing>

<identity_evidence>

A candidate requires one exact evidence source:

| Source               | Required observation                                                                 |
| -------------------- | ------------------------------------------------------------------------------------ |
| `process-argument`   | The live native process argument contains the complete session identity.             |
| `open-session-file`  | The live process holds an open native session file whose name contains the identity. |
| `native-status`      | The exact pane's native status surface displays the session identity and cwd.        |
| `current-session`    | The running controller exposes its own complete session identity.                    |
| `public-agent`       | `/operate-prowl agents` reports an exact high-confidence session in the pane.        |
| `operator-confirmed` | The operator explicitly confirms the exact pane, worktree, agent type, and session.  |

A pane title, terminal presentation, saved transcript, rollout existence, recent file, session-file timestamp, or sessionless roster entry is never identity evidence.

Record launch context separately from identity evidence:

- `resumeLocator` is the exact Claude session ID or open JSONL path, and equals `sessionId` for Codex and Pi.
- `nativeHome` is the absolute `CODEX_HOME` owning the exact Codex rollout when applicable; it is null for Claude and Pi.
- Derive both from the live process, its open session file, or operator-confirmed exact storage. NEVER select either by recency.

</identity_evidence>

<native_status_protocol>

Use this bounded protocol only when exact process or high-confidence public-agent evidence is unavailable:

1. Invoke `/operate-prowl` `read` with the exact pane UUID and stable-screen mode.
2. When a selection dialog is visibly open, invoke `/operate-prowl` `key` with `Escape`. The `prepare` invocation authorizes this exact dialog dismissal; NEVER send `Escape` to active generation.
3. Invoke `/operate-prowl` `send` with `/status` for Claude or Codex and `/session` for Pi, using immediate return.
4. Invoke `/operate-prowl` `read` once with stable-screen mode. When slash-command autocomplete consumed the first `Enter`, invoke `/operate-prowl` `key` with `Enter` once and read once more.
5. Record the complete displayed session identity and cwd with `source: native-status`.
6. Invoke `/operate-prowl` `key` with `Escape` once to close the status surface.

Stop preparation when an active session cannot safely reach its native status surface. Never queue a status command into active work or infer the identity from recency instead.

</native_status_protocol>

<prepare_workflow>

1. Invoke `/operate-prowl` once for `list` and once for `agents`; preserve both complete checked results.
2. Select only process-backed native agents with status `working`, `idle`, or `blocked`. Exclude `done`, stale pane detections without a live process, ordinary shells, and every unconfirmed ambiguous identity.
3. Establish every selected pane's complete worktree, agent type (`claude`, `codex`, or `pi`), native session, exact `resumeLocator`, applicable `nativeHome`, evidence source, role, and secondary authorization through `<identity_evidence>`. Use `<native_status_protocol>` only for unresolved exact identity.
4. Reconcile by worktree. Require exactly one primary; every distinct secondary requires `secondaryAuthorized: true` after explicit operator authorization. Reject duplicate native sessions globally.
5. Build the script input with checked public `items`, `agents`, exact `candidates`, and exact `correlationEvidence`. Each candidate uses `paneId`, `worktreePath`, `sessionId`, `resumeLocator`, `nativeHome`, `agentType`, `evidence`, `role`, and `secondaryAuthorized`; each evidence item uses `paneId`, `worktreePath`, `sessionId`, `agentType`, and `source`.
6. Run `prepare`, repeating `--pane` for every selected pre-restart pane UUID. Accept only `status: prepared` and schema version 5.
7. Write the complete prepared result to the absolute manifest path. Preserve the checked list and agent responses beside it when the caller requests a snapshot directory; never replace the script's candidate result with a hand-authored summary.
8. Report the full manifest path and candidate count. Prowl may restart only after every intended live session appears exactly once and unresolved identity count is zero.

</prepare_workflow>

<recover_workflow>

1. Read the schema-5 `prepared` manifest from the exact absolute path. Never substitute another snapshot, a historical roster, or post-restart inference.
2. Treat an already resumed controller as a normal prepared candidate. Its post-restart pane UUID may differ; never launch a duplicate controller.
3. Invoke `/operate-prowl` once for `list` and once for `agents`, then run `activate` with the prepared manifest and checked public arrays.
4. Read the activation plan exactly:
   - `ready` carries complete existing bindings and no activation.
   - `activation-required` carries existing bindings plus ordered `open` or `tab-create` actions.
   - `pane-occupied`, `invalid-target`, or `invalid-schema` stops before mutation.
5. For every `open` action, invoke `/operate-prowl` `open` with the complete worktree path. For every `tab-create` action, require the prepared authorized secondary and treat the operator's exact `recover` invocation as authorization for that action's named worktree. Preserve every complete checked result in action order.
6. Run `bind` with the activation plan and ordered `{originalPaneId, transport}` results. Accept only `ready`; every binding preserves one original pane and one distinct Prowl-returned post-restart pane.
7. Invoke `/operate-prowl` once for `list` and once for `agents`, then run `recover` with the unchanged prepared manifest and exact bindings. Stop on any occupied, missing, duplicate, or mismatched target without partial delivery.
8. For every planned launch, invoke `/operate-prowl` once for `send` using its complete `paneId`, exact source-owned native command, and immediate-return mode. The command contains only the prepared agent type, exact resume locator or session identity, and applicable native home; NEVER append reassessment prose or replace it with a recency selector.
9. Run `settle` with the exact launch plan and ordered checked transports. Accept only `resumed` or `already-current`; never retry a transport that may have delivered.
10. Wait for each launched native TUI to become input-ready through one bounded stable-screen read. Resolve visible update, trust, authentication, or account-selection dialogs only within explicit operator authority; stop that candidate when exact recovery remains unavailable.
11. Invoke `/operate-prowl` once more for `list` and `agents`. Build exact post-restart `correlationEvidence`: use exact high-confidence public-agent identity where available and `<native_status_protocol>` or process-backed evidence otherwise.
12. Run `verify` with the prepared manifest, exact bindings, checked public arrays, and correlation evidence. Accept only `verified`, with target count equal to the prepared candidate count and empty missing, duplicate, and unexpected arrays.
13. Run `reassess` with the verified result. `already-current` emits no delivery. `reassessment-ready` emits one source-owned continuation instruction for each verified non-controller session absent from `reassessedSessionIds`.
14. For every reassessment delivery, invoke `/operate-prowl` once for `send` using its complete `paneId`, exact source-owned text, and immediate-return mode. These sends occur only after verification and contain no native launch command.
15. Run `settle` with the reassessment plan and ordered checked transports. Accept only `reassessment-sent`; replace the manifest with the returned `prepared` object so repeated recovery emits no duplicate reassessment.
16. Preserve the activation plan, bindings, launch plan, checked launch transports, verification result, reassessment plan, checked reassessment transports, and updated manifest together. Report every full old-pane/new-pane/worktree/agent/session correlation.

</recover_workflow>

<command_forms>

```bash
printf '%s\n' '{"items":[],"agents":[],"candidates":[],"correlationEvidence":[]}' | python3 "${SKILL_DIR}/scripts/recover_agents.py" prepare --pane <pre-restart-pane-uuid>
printf '%s\n' '{"prepared":{},"items":[],"agents":[]}' | python3 "${SKILL_DIR}/scripts/recover_agents.py" activate
printf '%s\n' '{"plan":{},"activationResults":[]}' | python3 "${SKILL_DIR}/scripts/recover_agents.py" bind
printf '%s\n' '{"prepared":{},"bindings":[],"items":[],"agents":[]}' | python3 "${SKILL_DIR}/scripts/recover_agents.py" recover
printf '%s\n' '{"plan":{},"deliveryResults":[]}' | python3 "${SKILL_DIR}/scripts/recover_agents.py" settle
printf '%s\n' '{"prepared":{},"bindings":[],"items":[],"agents":[],"correlationEvidence":[]}' | python3 "${SKILL_DIR}/scripts/recover_agents.py" verify
printf '%s\n' '{"prepared":{},"bindings":[],"verification":{}}' | python3 "${SKILL_DIR}/scripts/recover_agents.py" reassess
```

</command_forms>

<constraints>

- ALWAYS route public Prowl operations through `/operate-prowl` and preserve complete checked results.
- ALWAYS preserve original and post-restart pane UUIDs, absolute worktree paths, agent types, native session IDs, exact resume locators, applicable native homes, evidence sources, roles, authorization values, and reassessed-session identities verbatim.
- NEVER reconstruct eligibility or identity from transcript content, saved history, rollout recency, pane presentation, or a latest-session selector.
- NEVER type into an occupied mismatched pane, close a pane, launch an unprepared identity, or execute one native session in multiple panes or worktrees.
- NEVER start a watcher, polling loop, daemon, background process, or open-ended wait.
- NEVER combine native launch and reassessment in one send, treat interruption metadata as cancellation, substitute repository completion for an unanswered operator request, ask again for existing authority, or silently exit when a pending interaction can be restored.

</constraints>

<testing>

Exercise schema-5 preparation, exact Claude resume locators, applicable Codex homes, lazy activation, checked binding, launch-only native command selection for Claude/Codex/Pi, strict launch and reassessment settlement, durable reassessment idempotence, secondary authorization, duplicate rejection, path preservation, external exact correlation evidence, extra-agent rejection, and CLI dispatch through the linked mapping, property, and compliance evidence.

</testing>

<failure_modes>

**Prowl restart produced no restored panes.** Claude treated old pane UUIDs as restart-stable and stopped recovery. Prowl materializes worktree terminals lazily; preserve old panes as provenance, activate prepared worktrees through `/operate-prowl`, and bind the returned new panes.

**SPX selected another session.** `spx agent resume --latest` selected Pi in a worktree whose prepared candidate was Codex and selected a different Claude session elsewhere. Select the exact native command from the prepared agent type and complete session ID; recency never chooses recovery identity.

**Slash autocomplete consumed Enter.** `/status` remained in the editor because the first `Enter` selected autocomplete instead of opening Status. Detect the visible autocomplete state, send one additional `Enter`, capture identity, and close Status with `Escape`.

**Launch prose remained buffered.** Claude sent the native resume command and reassessment prose as one terminal input. The interactive TUI consumed the launch while the prose remained buffered until the session quit. Send only the native launch command, verify native identity, then send reassessment separately.

**A pending selection became an exit.** The reassessment instruction told a restored Codex session to stop when continuation was unclear. The prior turn was waiting for an operator disposition, so Codex stopped instead of restoring the structured question. Re-present pending questions, selections, approvals, and blockers without choosing for the operator.

**Authentication interruption looked complete.** A Claude response failed with invalid credentials after an explicit operator correction. After login, reassessment inspected Git, declared the repository work complete, and asked for authorization already supplied instead of answering the unsatisfied turn. Retry the last substantive operator request after authentication or tool repair, preserving its original constraints; repository completion never satisfies an unanswered response.

**Native storage used another lookup root.** Claude required an exact JSONL path after its project location changed, and Codex required the account-specific `CODEX_HOME` containing its rollout. Preserve the exact resume locator and applicable native home during preparation; never rediscover either by recency after restart.

**The environment adapter leaked its request pipe.** `prowl send` rejected text with “Cannot provide text as both argument and stdin” because the adapter child inherited the JSON request stream. `/operate-prowl` binds absent operation input to null-device stdin; preserve that boundary before recovery delivery.

</failure_modes>

<success_criteria>

- Preparation persists one schema-5 candidate per intended process-backed live session, including exact launch context, with zero unresolved identities and no stale, done, duplicate, or unauthorized candidate.
- Recovery binds every original pane to one distinct post-restart pane in the same worktree and launches only prepared exact native sessions through launch-only sends.
- Settlement proves every planned launch and reassessment transport once without caller-supplied delivery claims or retries.
- Verification reports `verified`, the prepared target count, and empty missing, duplicate, and unexpected agent arrays before reassessment begins.
- Every non-controller session receives one separately settled reassessment instruction that restores unsatisfied operator work or its pending interaction, and the updated manifest prevents duplicate delivery.

</success_criteria>
