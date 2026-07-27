---
name: recover-prowl-agents
description: >-
  ALWAYS invoke this skill when preparing for or recovering coding-agent sessions after a Prowl restart. NEVER restart Prowl without a prepared exact-session manifest.
argument-hint: "<prepare|recover> <absolute-manifest-path>"
allowed-tools: Read, Write, Skill, Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/recover_agents.py":*), {{! tool('ask_user') !}}
---

<objective>
A durable pre-restart allowlist in which every prepared native session carries one exact identity and one Prowl pane correlation, with no duplicate or unauthorized candidate. An idempotent post-restart recovery in which every non-controller session receives one separately submitted continuation instruction reconciled against its own read context, and no unprepared agent is running.
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

A pane title, terminal presentation, saved transcript, rollout existence, recent file, session-file timestamp, or sessionless roster entry is never identity evidence. Prowl's `working`, `idle`, `blocked`, and `done` values are advisory workflow projections, never native-session eligibility or completion evidence. Preserve a status value when reporting it, but never include or exclude a candidate from that value alone.

Record launch context separately from identity evidence:

- `resumeLocator` is the exact Claude session ID or open JSONL path, and equals `sessionId` for Codex and Pi.
- `nativeHome` is the absolute `CODEX_HOME` owning the exact Codex rollout when applicable; it is null for Claude and Pi.
- Derive both from the live process, its open session file, or operator-confirmed exact storage. NEVER select either by recency.

</identity_evidence>

<native_status_protocol>

Use this bounded protocol only when exact process or high-confidence public-agent evidence is unavailable:

1. Invoke `/operate-prowl` `read` with the exact pane UUID and stable-screen mode.
2. When a selection dialog is visibly open, invoke `/operate-prowl` `key` with `Escape`. The operator's exact `prepare` or `recover` invocation authorizes this exact dialog dismissal, covering this protocol's reuse from `<recover_workflow>` step 11; NEVER send `Escape` to active generation.
3. Apply `<dialog_guard>` to the exact pane. Step 1's read satisfies it only when step 2 dismissed nothing; when step 2 sent `Escape`, invoke `/operate-prowl` `read` once more in stable-screen mode and require that no dialog remains. Stop this candidate when one persists. Then invoke `/operate-prowl` `send` with `/status` for Claude or Codex and `/session` for Pi, using immediate return.
4. Invoke `/operate-prowl` `read` once with stable-screen mode. When slash-command autocomplete consumed the first `Enter`, invoke `/operate-prowl` `key` with `Enter` once and read once more.
5. Record the complete displayed session identity and cwd with `source: native-status`.
6. Invoke `/operate-prowl` `key` with `Escape` once to close the status surface. Step 4's read still satisfies `<dialog_guard>` here because step 5 performs no pane interaction.

Stop preparation when an active session cannot safely reach its native status surface. Never queue a status command into active work or infer the identity from recency instead.

</native_status_protocol>

<dialog_guard>

Every `send` and every `key` requires one immediately preceding `/operate-prowl` `read` in stable-screen mode that establishes the target pane's dialog state: either no dialog is open, or the pane holds exactly one of the authorized dialogs enumerated below. A pane presenting a structured question, selection list, confirmation, permission request, or resume-mode prompt consumes the next input as that dialog's answer rather than as a message.

- A read taken earlier — including the `<recover_workflow>` context-read barrier — never satisfies this guard, because a dialog can open between that read and the input. An intervening action of this skill's own, such as a dismissal, ends immediacy exactly as an external change does.
- A pane holding any dialog other than an authorized one receives no send and no key. Record it as blocked with its complete pane identity, continue with the remaining panes, and report it.
- The authorized dialogs are the ones this skill holds explicit authority for, and each still requires the immediately preceding read that identifies the exact surface: the `<native_status_protocol>` `Escape` dismissal authorized by the operator's exact `prepare` or `recover` invocation, which covers that protocol equally when `<recover_workflow>` step 11 reaches it as a correlation-evidence fallback; that protocol's autocomplete `Enter` and its closing `Escape` over the status surface it opened; the Claude resume-mode prompt answered with one `Enter` in `<recover_workflow>` step 10; and the update, trust, authentication, account-selection, or other usage-affecting dialog that same step resolves, which additionally requires the explicit operator authority that step names and stops the candidate when that authority is absent. Answer no other dialog on the operator's behalf.

</dialog_guard>

<prepare_workflow>

1. Invoke `/operate-prowl` once for `list` and once for `agents`; preserve both complete checked results.
2. Select every positively identified native session represented by an instantiated pre-restart pane. Require exact evidence from `<identity_evidence>` and exclude ordinary shells and unconfirmed ambiguous identities. NEVER filter on Prowl status: a `done` projection can still carry an unfinished native conversation, as the live restart test established.
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
3. Invoke `/operate-prowl` once for `list` and once for `agents`, then run `activate` with the prepared manifest, checked public arrays, and `controllerPaneId` set to the exact post-restart pane the controller occupies. Supply that attestation whenever the public roster reports the controller's own pane without a session identity, which happens when the controller's native transcript resolves under a different project root than its pane's working directory; without it activation reads the controller's pane as a mismatched occupant and stops. The attestation binds that one pane on `current-session` evidence, never relaunches it, and leaves every other pane on the strict roster match.
4. Read the activation plan exactly:
   - `ready` carries complete existing bindings and no activation.
   - `activation-required` carries existing bindings plus ordered `open` or `tab-create` actions.
   - `pane-occupied`, `invalid-target`, or `invalid-schema` stops before mutation.
5. Treat `list` as the instantiated-terminal inventory, not the visible sidebar-worktree inventory. For every `open` action, invoke `/operate-prowl` `open` with the complete prepared worktree path and `mutationAuthorized: true`; the operator's exact `recover` invocation authorizes the visible focus switch and first-tab creation for that prepared path. NEVER enumerate Git worktrees or filesystem directories to invent activation targets. For every `tab-create` action, require the prepared authorized secondary and use the same exact-worktree authorization. Preserve every complete checked result in action order.
6. Run `bind` with the activation plan and ordered `{originalPaneId, transport}` results. An `open` result passes only with `resolution: exact-root`, an exact returned worktree path, and a complete returned pane; `new-root`, `inside-root`, path mismatch, or missing target stops recovery. Preserve `created_tab` as evidence rather than requiring one value: false can identify an existing exact target and must not trigger an extra pane. Accept only `ready`; every binding preserves one original pane and one distinct Prowl-returned post-restart pane.
7. Invoke `/operate-prowl` once for `list` and once for `agents`, then run `recover` with the unchanged prepared manifest, exact bindings, and the same `controllerPaneId` attestation step 3 supplied. Stop on any occupied, missing, duplicate, or mismatched target without partial delivery.
8. Launch one planned native session at a time. Apply `<dialog_guard>` to the exact pane immediately before its send. Invoke `/operate-prowl` once for `send` using its complete `paneId`, exact source-owned native command, and immediate-return mode, then require checked transport evidence that a trailing `Enter` was sent. The command contains only the prepared agent type, exact resume locator or session identity, and applicable native home; NEVER append reassessment prose or replace it with a recency selector. Serialize Codex launches sharing one `nativeHome` and wait for the prior Codex TUI to become input-ready before starting the next, preventing shared SQLite initialization locks.
9. Run `settle` with the exact launch plan and ordered checked transports. Accept only `resumed` or `already-current`; never retry a transport that may have delivered. A transport with no `response.data.input.trailing_enter_sent: true` is not settled.
10. Wait for each launched native TUI to become input-ready through one bounded stable-screen read. When Claude presents its exact old-session resume-mode prompt, select the recommended `Resume from summary` option with one authorized `Enter`; this preserves the exact native identity while avoiding a full-history reload. Resolve update, trust, authentication, account-selection, or any other usage-affecting dialog only within explicit operator authority; stop that candidate when exact recovery remains unavailable.
11. Invoke `/operate-prowl` once more for `list` and `agents`. Build exact post-restart `correlationEvidence`: use exact high-confidence public-agent identity where available and `<native_status_protocol>` or process-backed evidence otherwise.
12. Run `verify` with the prepared manifest, exact bindings, checked public arrays, and correlation evidence. Accept only `verified`, with target count equal to the prepared candidate count and empty missing, duplicate, and unexpected arrays.
13. Establish one global context-read barrier before planning or sending any continuation. In prepared-manifest order, invoke `/operate-prowl` `read` with stable-screen mode for every verified binding, including the active controller and every already-correlated pane. Preserve each complete checked result as `{originalPaneId, paneId, transport}`. Finish all reads before the first reassessment send; NEVER interleave a pane read with continuation delivery. If any pane cannot be read, stop reassessment for the entire set with zero sends.
14. Judge each verified non-controller pane separately from its own barrier read, then run `reassess` with the verified result, the complete ordered `paneReadResults`, and one `restored` entry for every recipient that needs anything at all. Recovery is never a broadcast. Most recipients need nothing: a session that is mid-work, or that already answered its last operator turn, or that is holding a question still visible on its screen, lost nothing to the restart and receives no message — a delivery there costs it a turn and invites redundant work it had not chosen. Supply a `restored` entry only where the restart destroyed something for that one recipient, and say only that: a pending operator question wiped by compaction, a killed command or sub-agent whose result the session may still be counting on, an operator turn that never received its response. State the destroyed fact in one short line and stop; the recipient holds the conversation that decides what follows, and the controller sees one rendered screen. `reassess` prepends the non-controller boundary to each supplied fact and emits nothing for the recipients left out, recording them as judged-intact so a repeated recovery does not revisit them. `already-current` emits no delivery.
15. For every reassessment delivery, apply `<dialog_guard>` to its target pane, then invoke `/operate-prowl` once for `send` using its complete `paneId`, exact source-owned text, and immediate-return mode. These sends occur only after verification and the global context-read barrier and contain no native launch command. Require checked transport evidence that trailing `Enter` was sent; visible text still sitting in an editor is not delivery.
16. Run `settle` with the reassessment plan and ordered checked transports. Accept only `reassessment-sent`, then perform one bounded stable-screen read per recipient and require that read to locate the recipient's own output below the sent text and, per `<dialog_guard>`, to establish that no dialog is open. An apparently empty editor is not that evidence, and the pane's last line is always the status footer, so neither establishes submission; a visible queued-input indicator is submission into a busy recipient and settles that recipient without further input. When that read finds the sent text with no output beneath it, no queued-input indicator, and no open dialog, send one further `Enter` to that pane and read again; that second read settles the recipient only when it locates output or a queued-input indicator, and a recipient still showing neither is reported blocked with its complete pane identity rather than receiving a third submission attempt. A recipient whose read shows an open dialog receives no further input and is reported blocked the same way. Clear the undelivered text from a recipient blocked for want of submission with one `ctrl+u` before reporting it, because text left in the composer prefixes whatever the operator types next; that clear submits nothing and is therefore not the withheld third submission attempt, the second read that established the block still satisfies `<dialog_guard>` for it because no pane interaction intervened, and a recipient blocked by an open dialog receives no input at all, including that clear. Replace the manifest with the returned `prepared` object only after every recipient passes that submission check, so repeated recovery emits no duplicate reassessment.
17. Preserve the activation plan, bindings, launch plan, checked launch transports, verification result, complete pane-read barrier, reassessment plan, checked reassessment transports, and updated manifest together. Report every full old-pane/new-pane/worktree/agent/session correlation.

</recover_workflow>

<command_forms>

```bash
printf '%s\n' '{"items":[],"agents":[],"candidates":[],"correlationEvidence":[]}' | python3 "${CLAUDE_SKILL_DIR}/scripts/recover_agents.py" prepare --pane <pre-restart-pane-uuid>
printf '%s\n' '{"prepared":{},"items":[],"agents":[],"controllerPaneId":null}' | python3 "${CLAUDE_SKILL_DIR}/scripts/recover_agents.py" activate
printf '%s\n' '{"plan":{},"activationResults":[]}' | python3 "${CLAUDE_SKILL_DIR}/scripts/recover_agents.py" bind
printf '%s\n' '{"prepared":{},"bindings":[],"items":[],"agents":[],"controllerPaneId":null}' | python3 "${CLAUDE_SKILL_DIR}/scripts/recover_agents.py" recover
printf '%s\n' '{"plan":{},"deliveryResults":[]}' | python3 "${CLAUDE_SKILL_DIR}/scripts/recover_agents.py" settle
printf '%s\n' '{"prepared":{},"bindings":[],"items":[],"agents":[],"correlationEvidence":[]}' | python3 "${CLAUDE_SKILL_DIR}/scripts/recover_agents.py" verify
printf '%s\n' '{"prepared":{},"bindings":[],"verification":{},"paneReadResults":[],"restored":[{"sessionId":"<session>","text":"<what this restart destroyed for this recipient>"}]}' | python3 "${CLAUDE_SKILL_DIR}/scripts/recover_agents.py" reassess
```

</command_forms>

<constraints>

- ALWAYS route public Prowl operations through `/operate-prowl` and preserve complete checked results.
- ALWAYS preserve original and post-restart pane UUIDs, absolute worktree paths, agent types, native session IDs, exact resume locators, applicable native homes, evidence sources, roles, authorization values, and reassessed-session identities verbatim.
- NEVER reconstruct eligibility or identity from Prowl status, transcript content, saved-history recency, rollout recency, pane presentation, or a latest-session selector.
- NEVER enumerate worktrees blindly; activation targets only complete worktree paths already preserved by prepared native-session candidates.
- NEVER type into an occupied mismatched pane, close a pane, launch an unprepared identity, or execute one native session in multiple panes or worktrees.
- NEVER start a watcher, polling loop, daemon, background process, or open-ended wait.
- NEVER plan or send reassessment before every verified pane has one checked context read; one unreadable pane blocks all continuation sends.
- NEVER send text or keys to a pane holding any dialog other than the ones `<dialog_guard>` enumerates as authorized, and NEVER treat an earlier read as the required check for any input — the guard requires one immediately preceding read per input, because input reaching an unauthorized open dialog answers it instead of arriving as a message.
- NEVER emit a continuation instruction that omits the recipient's non-controller boundary: every instruction states that the recipient is not the recovery controller and must neither invoke recovery nor send text or keys to any pane, because a recipient carrying this skill otherwise recovers an already-recovered set.
- NEVER send a resumed session an instruction to exit, stop, or stand down, and NEVER prescribe its next action, disposition, or conclusion — a continuation instruction states only what the restart destroyed, because the controller reads a rendered screen while the recipient holds the conversation that decides.
- NEVER deliver one instruction to every recipient. Judge each pane separately from its own barrier read and send only where that pane lost something to the restart; a message to a session that lost nothing costs it a turn and can start work it never chose. A loop that delivers identical text to every pane is a broadcast whatever it is called.
- NEVER send a continuation long enough for the recipient TUI to collapse it into a paste attachment, and NEVER spread one across multiple lines. Neither its own trailing `Enter` nor the single `Enter` that `<recover_workflow>` step 16 adds submits a collapsed attachment, so the text arrives nowhere and occupies the recipient's editor until cleared. One short line is the only shape that reaches a recipient, and that budget covers the whole submitted message including the non-controller boundary `reassess` prepends.
- NEVER combine native launch and reassessment in one send, treat interruption metadata as cancellation, substitute repository completion for an unanswered operator request, treat distinct delivered work as satisfying an unreconciled plan, ask again for existing authority, or silently exit when a pending interaction can be restored.

</constraints>

<testing>

Exercise schema-5 preparation, exact Claude resume locators, applicable Codex homes, lazy activation, checked binding, launch-only native command selection for Claude/Codex/Pi, all-pane context-read barriers, strict launch and reassessment settlement, durable reassessment idempotence, secondary authorization, duplicate rejection, path preservation, external exact correlation evidence, extra-agent rejection, and CLI dispatch through the linked mapping, property, and compliance evidence.

</testing>

<failure_modes>

**Sidebar worktrees disappeared from `list`.** Claude treated `prowl list` as the sidebar inventory and concluded Prowl had lost its topology. The live GUI still showed known worktree rows; `list` contained only instantiated terminal panes. Activate only prepared paths with `open`, require `exact-root`, and bind the returned new pane.

**A `done` session was unfinished.** Claude excluded a pane because Prowl reported `done`, but its exact native session resumed into concrete unfinished implementation work. Treat every Prowl status as advisory and decide eligibility from exact native identity evidence.

**Concurrent Codex launches locked SQLite.** Six exact Codex resumes sharing one `CODEX_HOME` started together; three returned to the shell with a database-lock failure. Serialize launches sharing one native home and wait for each prior TUI to become input-ready.

**Claude required summary resumption.** An old exact session opened a native choice between summary and full-history resumption. Accept the recommended summary option with one `Enter`; do not mistake the prompt for failed identity correlation or send continuation prose into it.

**Continuation text looked delivered but remained editable.** A transport return alone did not prove the turn was submitted. In one observed recovery run several sends returned `trailing_enter_sent: true` while their text still sat unsubmitted in the recipient's editor, so that flag is necessary and never sufficient. Only the post-send read distinguishes the two states, and a read that inspects the wrong region reports success either way. A busy recipient adds a third state: the text has left the editor and waits in the recipient's queue, showing a queued-input indicator and no output yet, so a check that recognizes only output would resend into it and submit a stray empty turn. Locate the recipient's own output or its queued-input indicator below the sent text before recording durable reassessment.

**A pasted continuation never reached its recipients.** Claude sent one 1,300-character continuation to 27 recipients. The Claude TUI collapsed it into a `[Pasted text #1]` attachment, and 10 of them held that attachment unsubmitted for forty minutes while `trailing_enter_sent` reported true for every send. Neither the trailing `Enter` nor a later explicit `Enter` submits a collapsed attachment; only `ctrl+u` clears it, and those same recipients accepted a one-line message immediately afterwards. Length alone decided delivery, so the single short line `<recover_workflow>` step 14 and `<constraints>` require is not only the correct shape but the only shape that arrives — a continuation stating one destroyed fact stays under the collapse threshold, and any continuation long enough to exceed it is prescribing rather than restoring.

**A plan was declared absorbed without reading its pane.** A resumed session received a generic continuation instruction before the controller read its visible context. It merged a useful but separate change, then treated an explicit unfinished cutover plan as already covered. Read every verified pane before sending any continuation to any recovered session, then require plan-by-plan acceptance-scope reconciliation; distinct work never completes an unread plan.

**A continuation instruction recruited its recipient as a second recovery controller.** A resumed Codex session received `Session resumed after a Prowl restart. Determine whether it is safe to continue...`, loaded `recover-prowl-agents` and `/operate-prowl`, ran `list` and `agents`, and stood one operator answer away from sending text into other panes — a second recovery of a set the controller had already recovered. Generic restart framing reads as a recovery mandate to any recipient carrying this skill, and the recipient cannot tell from that text that another session owns the recovery. State the recipient's non-controller boundary in every continuation instruction: it is not the recovery controller, and it invokes no recovery and sends no text or keys to any pane.

**A send answered the recipient's open question.** Continuation text sent to a pane holding an open structured-question dialog was consumed as that question's note field and auto-selected its recommended option. The message never arrived as a message, and a question that was waiting on the operator was answered by the controller instead. A pane with an open dialog exposes no neutral input surface, and a read taken before the dialog opened cannot show it. Read each target pane immediately before its send per `<dialog_guard>` and deliver nothing into a dialog that guard does not enumerate as authorized.

**SPX selected another session.** `spx agent resume --latest` selected Pi in a worktree whose prepared candidate was Codex and selected a different Claude session elsewhere. Select the exact native command from the prepared agent type and complete session ID; recency never chooses recovery identity.

**Slash autocomplete consumed Enter.** `/status` remained in the editor because the first `Enter` selected autocomplete instead of opening Status. Detect the visible autocomplete state, send one additional `Enter`, capture identity, and close Status with `Escape`.

**Launch prose remained buffered.** Claude sent the native resume command and reassessment prose as one terminal input. The interactive TUI consumed the launch while the prose remained buffered until the session quit. Send only the native launch command, verify native identity, then send reassessment separately.

**A pending selection became an exit.** The reassessment instruction told a restored Codex session to stop when continuation was unclear. The prior turn was waiting for an operator disposition, so Codex stopped instead of restoring the structured question. Re-present pending questions, selections, approvals, and blockers without choosing for the operator.

**Authentication interruption looked complete.** A Claude response failed with invalid credentials after an explicit operator correction. After login, reassessment inspected Git, declared the repository work complete, and asked for authorization already supplied instead of answering the unsatisfied turn. Retry the last substantive operator request after authentication or tool repair, preserving its original constraints; repository completion never satisfies an unanswered response.

**The controller's own pane blocked activation.** The public roster reported the controller's post-restart pane with an agent but no session identity, because that session's native transcript resolved under the project root of the directory it started in rather than the worktree its pane now occupied. Activation read an unidentifiable agent sitting in a worktree that had a prepared candidate, refused to assume it was the controller, and returned `pane-occupied` with zero bindings — correctly, since adopting an unidentified agent would silently strand the prepared session. Nothing downstream can run without activation, so the whole fleet stayed down over the one pane whose identity was least in doubt. Supply `controllerPaneId` in `activate` and `recover`; it binds that exact pane on `current-session` evidence, never relaunches it, and leaves every other pane on the strict roster match.

**Native storage used another lookup root.** Claude required an exact JSONL path after its project location changed, and Codex required the account-specific `CODEX_HOME` containing its rollout. Preserve the exact resume locator and applicable native home during preparation; never rediscover either by recency after restart.

**The environment adapter leaked its request pipe.** `prowl send` rejected text with “Cannot provide text as both argument and stdin” because the adapter child inherited the JSON request stream. `/operate-prowl` binds absent operation input to null-device stdin; preserve that boundary before recovery delivery.

**Stacked instructions told a session to abandon its pending work.** Claude sent three continuation instructions into one long-lived pane across successive restarts. Two restated the same session identity, and each made abandonment the default disposition:

```text
NEVER send text shaped like this:
  "Continue. If you had been asking the user a question using a tool, ask the
   question again using the same tool."
  "…Continue only when concrete unfinished work remains and continuation is
   still authorized… exit now without modifying files or starting background
   work. Do not remain active merely because recovery resumed the session."
  "…If the workflow is complete, deliberately stopped, or continuation is
   unclear, stop without modifying state or starting background work."
```

Each delivery went out without being recorded against `reassessedSessionIds`, so every restart appended another instruction to a pane that already carried two. The defect is the conditional exit clause, which resolves every ambiguity toward quitting — the same defect as `A pending selection became an exit`, compounded by repetition. Uniform wording across recipients is correct and is not the fault here. Record every delivery in the manifest before the next recovery reads it, send exactly one continuation instruction per session, and never give a resumed session an instruction to exit.

**One instruction went to every recipient and only one recipient needed it.** After a 23-session recovery, Claude delivered the same script-authored paragraph to all 22 non-controller panes, then read them. Exactly one had lost anything: a session whose closing question the operator had declined and then compacted away, leaving the question destroyed and the session idle. That pane needed one sentence — ask it again — and got instead a paragraph telling it to classify its own interruption, and it concluded the operator had settled the matter and held. Of the rest, nine were mid-work, five had already completed their last operator turn, and six were holding questions still visible on their screens; the message cost each a turn, and one dispatched three gate agents in response to work it had already done. The defect was the design, not the wording: a single body sent everywhere cannot state what any particular restart destroyed, because that differs per pane and is knowable only from that pane. Read every pane, decide per pane, and send only where something was destroyed.

**Controller-authored next actions displaced the sessions' own judgment.** Correcting **Stacked instructions told a session to abandon its pending work**, Claude swung to the opposite error: it read each recovered pane's rendered screen and drafted a per-session continuation naming what that session should do next:

```text
NEVER send a per-recipient next action like this:
  "Your gate agents returned 0 tool uses; treat their verdicts as
   unproduced and re-dispatch them before concluding."
  "Retry the pull-request creation once — the failures may have been
   a transient provider incident."
```

A rendered screen is a fraction of a session's conversation, so each instruction shipped the controller's inference as a decision the session had not made, and two of them would have caused expensive redundant work had the operator not intercepted them. The controller cannot see what the session sees. State only what the restart destroyed, leave the next action to the recipient, and route its doubt to the operator.

</failure_modes>

<success_criteria>

- Preparation persists one schema-5 candidate per intended exact native session, including exact launch context, with zero unresolved, duplicate, or unauthorized identity; Prowl status never filters the set.
- Recovery binds every original pane to one distinct post-restart pane in the same worktree and launches only prepared exact native sessions through launch-only sends.
- Settlement proves every planned launch and reassessment transport once without caller-supplied delivery claims or retries.
- Verification reports `verified`, the prepared target count, and empty missing, duplicate, and unexpected agent arrays before reassessment begins.
- Every verified pane has one checked stable-screen context read before any reassessment delivery is planned or sent; one failed read produces zero continuation sends.
- Every non-controller session receives one separately settled reassessment instruction that reconciles explicit plans against delivered scope, restores unsatisfied operator work or its pending interaction, and prevents duplicate delivery through the updated manifest.
- Every send and key carries one immediately preceding read establishing its target pane's dialog state, and a pane holding any dialog other than an authorized one is reported blocked with zero input delivered to it.
- Every emitted continuation instruction states that its recipient is not the recovery controller and invokes no recovery and sends no text or keys to any pane.
- Every emitted continuation instruction is one short line that no recipient TUI collapses into a paste attachment, and no delivery counts as settled while its text remains unsubmitted in a recipient's composer.

</success_criteria>
