<required_reading>

`${CLAUDE_SKILL_DIR}/references/authority.md`, `${CLAUDE_SKILL_DIR}/references/guards.md` and `${CLAUDE_SKILL_DIR}/references/status-report.md`.

</required_reading>

<process>

1. Every monitor line ends with `→` and the disposition it calls for; apply it, and use the row below for detail. A notice can be stale: read the pane through the backend's capability (`coding-agents:operate-prowl` or `coding-agents:operate-herdr`) before acting on any session signal.

   | Signal                               | Disposition                                                                                                                                                                                                                                                         |
   | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | `MAIL`                               | Read the record with bodies; handle it by step 2; record the receipt.                                                                                                                                                                                               |
   | `BLOCKED`                            | Read the pane. A read a position of higher rank ordered: approve it. A denied tool call, a destructive-command prompt or a guard prompt: Escape, then tell the position to do it differently: one command at a time, or `trash` in place of `rm`; never approve it. |
   | `WENT-IDLE`                          | Read the pane's last lines. A finished leg with a next step its skill names: leave it. An idle position with open work: send its next step through `instruct.md`.                                                                                                   |
   | `STALLED`                            | Read the pane and the transcript; treat it as the 15-minute stall trigger.                                                                                                                                                                                          |
   | `COMPACT-IDLE`                       | At or above 75% with the turn ended: compact it through `restart.md` before it receives anything new. Below 75%: nothing.                                                                                                                                           |
   | `COMPACT-AT-BOUNDARY`, `COMPACT-NOW` | Follow `restart.md` to compact it at the next boundary, or now.                                                                                                                                                                                                     |
   | `ABSENT`                             | Check the roster and the store: open work with no session goes to `restart.md`.                                                                                                                                                                                     |
   | `WATCH-BROKEN`                       | Re-run the failed read once; a second failure is reported to the operator with its line.                                                                                                                                                                            |

2. Handle a mail by its kind:
   - A STATUS report: check every line against the step-in triggers. Verify the head, PR and checks against `gh` before believing them. On any trigger, step in through `instruct.md`.
   - A question: find its owner in the authority map. Answer it when the Director owns it, citing the rule or ruling. Ask the owning Maintainer when it is a product or repository fact. Raise it to the operator only when the map gives it to the operator, with the exact passage and the position's recommendation.
   - A fact or answer: verify it against its source, record it in `state.md`, and act on what it unblocks.
3. Rewrite the affected lines of `state.md` for every disposition that changed something. A new operator rule or an observed failure goes into this skill instead, the same turn.

</process>

<success_criteria>

- Every signal was read against its pane or record before any action, and every mail ended with a receipt.
- Every step-in trigger a STATUS report showed produced one order in the same turn.

</success_criteria>
