# Issues: Report changes

## The read clause of report-no-write has no evidence `spx/31-outcomeeng.enabler/32-changes.enabler/60-report-changes.enabler/report-changes.md` `report-no-write` `evidence`

Category evidence, severity debt, raised by the CI review of [PR 752](https://github.com/outcomeeng/plugins/pull/752) on head `be723d4b73ab098c1bd655ad094653e7945144ed`, and accepted by the Methodology Director's ruling on that head.

**Evidence**: `report-no-write` states that the report-changes script "writes no file and reads no overlay and no repository content". Its linked test `tests/test_report_changes.compliance.l1.py` observes the gh command shapes, the writes, and the working-directory entries, and observes no read. A script that opened `spx/local/changes.md` would pass it. The shared recorder `outcomeeng_testing/harnesses/audit_change_run_observer.py` records writes and spawns only.

**Impact**: the read half of the rule is unobserved. The Node declares `malleability: spec`, which needs only Validate, the reachability test, and a result for every tagged Assertion, so the gap leaves the Node's state unaffected.

**Settlement condition**: when the report-changes script moves to the record form, the linked test observes the files the script opens and fails for a script that opens any path outside its own file.

## `l1` tests cross an `l2` boundary

**Evidence:** A run of every `l1` test file of the Product Tree at commit `744cf8cf23`, traced through the Python audit events of each test's setup, call and teardown, records that these `l1` files cross a boundary [`l1-boundaries`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md) places at `l2`:

- `tests/test_report_changes.compliance.l1.py`: write a file, make a temporary directory
- `tests/test_report_changes.mapping.l1.py`: write a file, make a temporary directory
- `tests/test_report_changes.property.l1.py`: write a file, make a temporary directory
- `tests/test_report_changes.scenario.l1.py`: write a file, make a temporary directory

**Impact:** Each run of these files starts processes or writes into temporary trees on the host every Position shares, so local and CI gates spend that load on every run.

**Settlement condition:** Each listed file covers the same linked Assertions in process, with no lower line or branch coverage of this Node's code, or the evidence that needs the boundary stands in an `l2` file written for it.
