<required_reading>

Read `${CLAUDE_SKILL_DIR}/references/standing-rules.md`. After a compaction or
restart, also read `${CLAUDE_SKILL_DIR}/references/ledger-reconstruction.md` and
`${CLAUDE_SKILL_DIR}/references/ledger-contract.md`.

</required_reading>

<process>

1. Require one allowed cause: message, officer state change, crossed bound, or
   operator-named cadence.
2. Record that cause as a ledger event before the read acts on it.
   Use skill `coding-agents:operate-agent-mail`. Ask it to send one
   durable `fact` record carrying the allowed cause and its payload under the
   Change's correlation, and validate the returned record's integer store
   identity under the parent skill's `<essential_principles>`.
3. Use skill `coding-agents:operate-herdr`. Ask it for the relevant pane state,
   and validate the result under the parent skill's `<essential_principles>`.
4. For an ordinary event read, use skill `coding-agents:operate-agent-mail`. Ask
   it for the inbox of the positively identified recipient that raised the
   event, and select the exact per-Change correlation.
5. When the read surfaces an operator instruction naming an officer session, or
   an officer fact describing an operator interaction, record that as this
   session's own failure to keep the operator out of that officer's pane. Use
   skill `coding-agents:operate-agent-mail`. Ask it to send one durable `fact`
   record carrying the failure, the evidence that raised it, and the officer it
   concerns under the Change's correlation, and validate the returned record's
   integer store identity under the parent skill's `<essential_principles>`.
6. After compaction or restart, acquire the complete derivation input through
   `${CLAUDE_SKILL_DIR}/references/ledger-reconstruction.md`. Refuse a partial
   input.
7. Rebuild the ledger from the acquired records and sealed journal runs.
8. Compare the checked state with the prior state. Produce no report when it is
   unchanged unless operator cadence requested one.

</process>

<success_criteria>

The result names the allowed cause and carries the validated durable `fact`
record and integer store identity that made that cause a ledger event, carries
the same for every orchestrating-session failure the read surfaced or states
that it surfaced none, preserves every checked capability and journal result,
proves the complete Change-correlated acquisition set after a compaction or
restart, and includes either the changed-state projection or an explicit quiet
result.

</success_criteria>
