<required_reading>

Read `${SKILL_DIR}/references/standing-rules.md`.

</required_reading>

<process>

1. Require that the target pane is one the operator's invocation assigned to
   this fleet.
2. Use skill `coding-agents:operate-herdr`. Ask it to read the officer pane and
   validate that result before repeating a stalled prompt; every pane read and
   keystroke below runs through that same capability.
3. Answer a guarded prompt only when the latest officer fact establishes the
   action as the next step in its governing flow, sending that keystroke with
   the standing pane authorization as `"mutationAuthorized": true`.
4. Dismiss a prompt no such fact supports and remove its cause, sending that
   keystroke with the standing pane authorization as
   `"mutationAuthorized": true`. Never interrupt a running Verifier pass.

</process>

<success_criteria>

The result preserves the checked pane state, latest officer fact, selected
correction, and successful herdr operation, with no interruption of a Verifier.

</success_criteria>
