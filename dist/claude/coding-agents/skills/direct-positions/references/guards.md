<overview>

What a command guard, a classifier refusal or a permission prompt ends, and what follows. Read it before handling any refusal or prompt, in the Director session or a position's pane.

</overview>

<guards>

| Decline                                                                     | What follows                                                                                                                                                     |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A dangerous-command-guard prompt, including a guard timeout under host load | Cancel it: Escape or No. Never answer Yes. The position continues with a sanctioned command.                                                                     |
| A guard block on a command holding one operation                            | The command family ends. Never retry it by any route.                                                                                                            |
| A guard block on a compound command                                         | Run its parts again one at a time, every string written out literally, with no shell variable or substitution.                                                   |
| A permission prompt raised by a destructive command                         | Escape, then tell the agent how to do it differently: no copy-and-delete, run from the scratchpad.                                                               |
| A harness classifier refusal                                                | It binds the outcome, not the command. Never pursue the same outcome through another tool, split or wording. Report it to the operator with the reason verbatim. |

A position never escalates a guard block on a read-only command to the operator: it reads the exact blocked command, then runs the declared commands plainly with full output.

</guards>

<classifier_triggers>

These Director actions drew classifier refusals and are never repeated:

- Relaying an operator rule or answer to a position as the operator's word.
- Ordering a position to overrule an audit verdict.
- Typing into another session's prompt to drive it, outside a skill that owns that operation.
- Writing a body or comment that carries authority text ("attested by …", "operator approved …").

</classifier_triggers>

<stray_state>

- A stray untracked file blocking a gate is committed, then removed with `git rm` on the work branch; it never waits for the operator.
- Local test suites do not run on the operator's host for a gate: probe first, CI runs the tests. A local markdown or link check on a linked development build is advisory; CI's pinned toolchain decides.

</stray_state>
