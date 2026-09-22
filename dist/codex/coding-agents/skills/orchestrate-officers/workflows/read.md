<required_reading>

Read `${SKILL_DIR}/references/standing-rules.md`. After a compaction or
restart, also read `${SKILL_DIR}/references/ledger-reconstruction.md` and
`${SKILL_DIR}/references/ledger-contract.md`.

</required_reading>

<process>

1. Require one allowed cause: message, officer state change, crossed bound, or
   operator-named cadence.
2. Use skill `coding-agents:operate-herdr`. Ask it for the relevant pane state,
   and validate the result under the parent skill's `<essential_principles>`.
3. For an ordinary event read, use skill `coding-agents:operate-agent-mail`. Ask
   it for the inbox of the positively identified recipient that raised the
   event, and select the exact per-Change correlation.
4. After compaction or restart, acquire the complete derivation input through
   `${SKILL_DIR}/references/ledger-reconstruction.md`. Refuse a partial
   input.
5. Rebuild the ledger from the acquired records and sealed journal runs.
6. Compare the checked state with the prior state. Produce no report when it is
   unchanged unless operator cadence requested one.

</process>

<success_criteria>

The result names the allowed cause, preserves every checked capability and
journal result, proves the complete Change-correlated acquisition set after a
compaction or restart, and includes either the changed-state projection or an
explicit quiet result.

</success_criteria>
