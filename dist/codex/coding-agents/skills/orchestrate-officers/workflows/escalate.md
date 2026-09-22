<required_reading>

Read `${SKILL_DIR}/references/standing-rules.md`.

</required_reading>

<process>

1. Lead with evidence, consequence, options, and one recommendation.
2. Classify the decision through the standing autonomous and operator-held
   classes.
3. For an autonomous class, record the decision as a ledger event.
   Use skill `coding-agents:operate-agent-mail`. Ask it to send one
   durable `decision` fact record carrying the class, the choice, and the
   reasoning under the Change's correlation, and validate the returned record's
   integer store identity under the parent skill's `<essential_principles>`.
4. Hold only the affected decision and continue every independent officer.
5. Write the escalation as text in this session's own pane, under the standing
   rule on delivering a held decision.

</process>

<success_criteria>

The result names the decision class and disposition and reaches the operator as
pane text rather than a structured question; an autonomous disposition includes
the validated durable `decision` fact record and its integer store identity, so
the reasoning is derivable from the sources the ledger is built from, while a
held disposition pauses only its dependent action.

</success_criteria>
