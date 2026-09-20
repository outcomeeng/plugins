<required_reading>

Read `${SKILL_DIR}/references/standing-rules.md`.

</required_reading>

<process>

1. Require one allowed cause: message, officer state change, crossed bound, or
   operator-named cadence.
2. Use the inbox capability for records and the environment capability for the
   relevant pane state. Validate every result under the parent skill's
   `<essential_principles>`.
3. After compaction or restart, rebuild the ledger from the returned records
   and sealed verification-journal data.
4. Compare the checked state with the prior state. Produce no report when it is
   unchanged unless operator cadence requested one.

</process>

<success_criteria>

The result names the allowed cause, preserves every checked capability result,
and includes either the changed-state projection or an explicit quiet result.

</success_criteria>
