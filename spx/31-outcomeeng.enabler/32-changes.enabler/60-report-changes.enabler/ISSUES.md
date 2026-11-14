# Issues: Report changes

## The read clause of report-no-write has no evidence `spx/31-outcomeeng.enabler/32-changes.enabler/60-report-changes.enabler/report-changes.md` `report-no-write` `evidence`

Category evidence, severity debt, raised by the CI review of [PR 752](https://github.com/outcomeeng/plugins/pull/752) on head `be723d4b73ab098c1bd655ad094653e7945144ed`, and accepted by the Methodology Director's ruling on that head.

**Evidence**: `report-no-write` states that the report-changes script "writes no file and reads no overlay and no repository content". Its linked test `tests/test_report_changes.compliance.l1.py` observes the gh command shapes, the writes, and the working-directory entries, and observes no read. A script that opened `spx/local/changes.md` would pass it. The shared recorder `outcomeeng_testing/harnesses/audit_change_run_observer.py` records writes and spawns only.

**Impact**: the read half of the rule is unobserved. The Node declares `malleability: spec`, which needs only Validate, the reachability test, and a result for every tagged Assertion, so the gap leaves the Node's state unaffected.

**Settlement condition**: when the report-changes script moves to the record form, the linked test observes the files the script opens and fails for a script that opens any path outside its own file.
