<required_reading>

`${SKILL_DIR}/references/authority.md`, `${SKILL_DIR}/references/guards.md` and `${SKILL_DIR}/references/status-report.md`.

</required_reading>

<process>

1. Classify the event by its first word after the position tag and dispose of it by the row below. A notice can be stale: read the pane through the backend's capability (`coding-agents:operate-prowl` or `coding-agents:operate-herdr`) before acting on any session signal.

   | Signal                               | Disposition                                                                                                                                                                                             |
   | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | `MAIL`                               | Read the record with bodies; handle it by step 2; record the receipt.                                                                                                                                   |
   | `BLOCKED`                            | Read the pane. A guard prompt: the overseeing position cancels it (`guards.md`). A question: route it by the authority map. Never answer it in the pane yourself unless the operator says to handle it. |
   | `WENT-IDLE`                          | Read the pane's last lines. A finished leg with a next step its skill names: leave it. An idle position with open work: send its next step through `instruct.md`.                                       |
   | `WAITING-ON-BACKGROUND`              | Nothing; the harness re-invokes the session.                                                                                                                                                            |
   | `STALLED`                            | Read the pane and the transcript; treat it as the 15-minute stall trigger.                                                                                                                              |
   | `COMPACT-IDLE`                       | Nothing while the position works; at an idle boundary with context above 60%, follow `restart.md` to compact it.                                                                                        |
   | `COMPACT-AT-BOUNDARY`, `COMPACT-NOW` | Follow `restart.md` to compact it at the next boundary, or now.                                                                                                                                         |
   | `ABSENT`                             | Check the roster and the store: open work with no session goes to `restart.md`.                                                                                                                         |
   | `WATCH-BROKEN`                       | Re-run the failed read once; a second failure is reported to the operator with its line.                                                                                                                |

2. Handle a mail by its kind:
   - A STATUS report: check every line against the step-in triggers. Verify the head, PR and checks against `gh` before believing them. On any trigger, step in through `instruct.md`.
   - A question: find its owner in the authority map. Answer it when the Director owns it, citing the rule or ruling. Ask the owning Maintainer when it is a product or repository fact. Raise it to the operator only when the map gives it to the operator, with the exact passage and the position's recommendation.
   - A fact or answer: verify it against its source, record it in the note, and act on what it unblocks.
3. Append one dated line to the note for every disposition that changed something: what arrived, what was decided, what was sent with its mail id.

</process>

<success_criteria>

- Every signal was read against its pane or record before any action, and every mail ended with a receipt.
- Every step-in trigger a STATUS report showed produced one order in the same turn.

</success_criteria>
