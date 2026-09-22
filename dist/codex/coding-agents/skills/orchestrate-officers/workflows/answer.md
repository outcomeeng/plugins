<required_reading>

Read `${SKILL_DIR}/references/standing-rules.md`.

</required_reading>

<process>

1. Decide a question whose answer is fixed by loaded skills, decisions, specs,
   and checked state.
2. Use skill `coding-agents:operate-agent-mail`. Ask it to send the decision and
   evidence as one `answer` record.
3. Validate the returned record and integer store identity under the parent
   skill's `<essential_principles>`.
4. Hold an unresolved decision in this orchestrating session's pane under the
   standing autonomy rules.

</process>

<success_criteria>

The result contains either one validated durable answer record with its
evidence or one held decision classified by the standing autonomy rules.

</success_criteria>
