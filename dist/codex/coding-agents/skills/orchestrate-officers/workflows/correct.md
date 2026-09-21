<required_reading>

Read `${SKILL_DIR}/references/standing-rules.md`.

</required_reading>

<process>

1. Require that this skill launched the target pane.
2. Read the officer pane and validate the herdr result before repeating a
   stalled prompt.
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
