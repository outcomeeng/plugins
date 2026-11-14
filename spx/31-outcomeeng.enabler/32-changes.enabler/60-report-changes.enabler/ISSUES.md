# Issues: Report changes

## The waiting-maturity column misstates a Submitted Change that waits for a lower or stands at Applicable

Rule `transitions` of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md), severity blocking, raised by the audit of outcomeeng/changes#897 before Applicable, run `2026-11-14_11-03-42-818-efce4776fbc8`, against the record at Base `e732cdd37183182c00796f700c365b8f1cada8ac`.

**Evidence**: the row `report-columns/waiting-maturity` of `report-changes.md` gives "waiting: the next Maturity, for any other Submitted Change". The `transitions` Mapping of the decision admits two Submitted Changes that wait for no next Maturity. The first is a Change the holder submits because its settled judgment reopened, which waits for the Operator's lower. The second is a Submitted Applicable Change, above which no Maturity exists. The row `waiting-lower`, which named the first case, was dropped from the Node on the Operator's direction, because the reason it read from a submit comment has no home in the transition log. The entry "The Change record decision gives a submit a reason that its transition log cannot hold" in [`spx/31-outcomeeng.enabler/32-changes.enabler/ISSUES.md`](spx/31-outcomeeng.enabler/32-changes.enabler/ISSUES.md) records that contradiction. Three earlier audits of the record passed the row.

**Impact**: report-changes reports a Change that waits for a lower, and a Submitted Applicable Change, as waiting for its next Maturity. The audit gate stopped outcomeeng/changes#897 at Sliced on this finding.

**Settlement condition**: every waiting value of `report-columns` holds for each Change its row covers, either through a value true of every Submitted Change above the Priority decision, such as the Operator's next move, or through a row that tells a lower apart once the decision gives a submit's reason a home.

## The read clause of report-no-write has no evidence `spx/31-outcomeeng.enabler/32-changes.enabler/60-report-changes.enabler/report-changes.md` `report-no-write` `evidence`

Category evidence, severity debt, raised by the CI review of [PR 752](https://github.com/outcomeeng/plugins/pull/752) on head `be723d4b73ab098c1bd655ad094653e7945144ed`, and accepted by the Methodology Director's ruling on that head.

**Evidence**: `report-no-write` states that the report-changes script "writes no file and reads no overlay and no repository content". Its linked test `tests/test_report_changes.compliance.l1.py` observes the gh command shapes, the writes, and the working-directory entries, and observes no read. A script that opened `spx/local/changes.md` would pass it. The shared recorder `outcomeeng_testing/harnesses/audit_change_run_observer.py` records writes and spawns only.

**Impact**: the read half of the rule is unobserved. The Node declares `malleability: spec`, which needs only Validate, the reachability test, and a result for every tagged Assertion, so the gap leaves the Node's state unaffected.

**Settlement condition**: when the report-changes script moves to the record form, the linked test observes the files the script opens and fails for a script that opens any path outside its own file.
