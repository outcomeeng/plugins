---
name: supervise-agents
description: >-
  ALWAYS invoke this skill when monitoring several coding agents in Prowl,
  unblocking agents in other panes, or continuing supervision after a shared
  authentication, capacity, or environment condition changes.
allowed-tools: Skill, Bash(python3:*), Bash(prowl agents:*), Bash(prowl read:*), Bash(prowl send:*)
---

<objective>

A supervised set of coding-agent panes in which recoverable shared blockers are
resolved and each operating agent continues its own work without the supervisor
taking ownership of that work.

</objective>

<dependencies>

Invoke `/prowl-cli` before operating on panes. The prototype requires `prowl`
on `PATH` and uses only explicit pane UUIDs returned by `prowl agents --json`.

</dependencies>

<responsibility_boundary>

The supervisor owns:

- discovering panes that need attention,
- reading stable pane output,
- classifying and correlating shared external blockers,
- requesting one operator action when the external condition requires it,
- notifying affected panes after the condition changes,
- confirming that panes return to work or expose a new blocker.

Each operating agent owns its workflow state, successful work, run identities,
retry selection, and continuation decisions. NEVER tell an operating agent which
of its internal steps remain valid or which exact steps to rerun.

</responsibility_boundary>

<workflow>

1. Run `prowl agents --json`. Resolve the current pane and exclude it from
   intervention targets.
2. For every `blocked` pane, run
   `prowl read --pane <uuid> --last 200 --wait-stable --json` and classify the
   immediate stop condition from explicit output.
3. Correlate panes only when their output names the same external condition,
   such as an authentication change, provider capacity, unavailable dependency,
   or shared checkout state. Do not infer a shared incident from timing alone.
4. Complete every independent supervisory action before escalating. When one
   operator action is required, ask once for the action that unlocks the most
   affected panes.
5. Pass `<notification_gate>` before sending anything to another pane.
6. After the condition changes, notify each affected pane with the changed fact
   only. Example: `Codex authentication has changed. Re-evaluate the blocker and
   continue from your current state.`
7. Confirm with `prowl agents --json` and `prowl read --wait-stable` that each
   notified pane becomes `working`, reaches `done`, or reports a different
   blocker. The operating agent decides how to continue.
8. Run the foreground waiter:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/wait_for_panes.py"
   ```

9. When it returns, inspect only the pane UUIDs in its `panes` field through
   `prowl read --wait-stable`. Treat IDs in `removed` as roster-removal facts;
   never try to read or notify them. Act on the evidence, then start the waiter
   again.
10. `done` is the sole terminal Prowl status in this prototype. When every pane
    is already `done`, the restarted waiter remains blocked until a pane appears
    or changes. End supervision only when the operator interrupts it.

</workflow>

<notification_gate>

STOP before notifying another pane. Refresh `prowl agents --json` and proceed
only when every check passes:

- Explicit evidence shows the external condition changed: direct command output
  or an operator confirmation names the resolved condition.
- Every target pane still exists in the refreshed roster.
- The current supervisor pane is absent from the target set.
- The message states only the changed external fact and asks the operating agent
  to re-evaluate its blocker; it does not prescribe retries or reconstruct
  workflow state.

If any check fails, do not send. Refresh evidence or leave one explicit
operator-owned dependency.

</notification_gate>

<constraints>

- NEVER parse harness transcript files or inspect transcript directories; SPX
  owns transcript adapters.
- NEVER target a pane by title or position; use its full pane UUID.
- NEVER send workflow-specific retry instructions that take responsibility from
  the operating agent.
- NEVER run more than one waiter per machine; its lock rejects a second process.
- ALWAYS run the waiter in the foreground and wait for its JSON result.
- ALWAYS re-read changed panes after the waiter returns; a content hash is a
  wake-up signal, not an interpretation.

</constraints>

<error_handling>

- `BlockingIOError` means another machine-wide waiter owns
  `/tmp/outcomeeng-pane-wait.lock`; do not start a replacement.
- A nonzero `prowl` exit, malformed JSON, or 15-second command timeout ends the
  waiter. Surface the error rather than adding an internal restart loop.
- An ID in `removed` is not an error and is never readable; reconcile the roster
  and continue supervising the remaining panes.

</error_handling>

<failure_modes>

**Observation without recovery.** A watchdog completed 90 observation cycles
without recovering agents from repeated capacity incidents. Avoid: classify a
shared blocker, perform or request its resolution, notify affected panes, and
confirm forward progress before waiting again.

**Taking over the operating workflow.** Supervision tried to preserve an
operating agent's successful verifier results and select its retries. Avoid:
communicate only the changed external condition and let the operating agent
re-evaluate its own workflow.

</failure_modes>

<success_criteria>

- Every recoverable shared blocker observed during the supervision cycle has a
  resolution action or one explicit operator-owned dependency.
- `prowl agents --json` shows every notified pane as `working`, `done`, or
  blocked on a newly classified condition; `prowl read --wait-stable` confirms
  the matching pane output.
- The notification gate records a refreshed target roster and excludes the
  supervisor's pane before every `prowl send`.
- No operating agent's workflow state or retry selection is reconstructed by
  the supervisor.
- A second waiter invocation exits nonzero on the singleton lock rather than
  creating another polling process.

</success_criteria>
