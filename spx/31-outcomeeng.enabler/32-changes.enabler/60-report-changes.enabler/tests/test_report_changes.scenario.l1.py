"""Scenario evidence: the report-changes script lists a store page that holds one open Change.

The governing assertion is existential: given a store page that holds one open
Change, the script returns one row for that Change under the request and
result names the script exports. The case is the inert fixture
``one-open-change.json``, a whole store answer with invented identities, read
by path and replayed through the injected command runner.

Design record.

Assertion: given a store page that holds one open Change, when the script lists
the store, then it returns one row for that Change.
Production subject: the script's entry point reading the one-page store.
Case provenance: the whole-payload fixture, whose one issue is the Change.
Oracle owner: the fixture's ``direct`` row, read by hand from its answer.
Rejected mutation: the script returns no row, a second row, or a row for
another Change.
Failure observation: the status is not ok, the rows are not one, or the row's
number, URL, or title differs from the Change's.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.report_changes import (
    ONE_OPEN_CHANGE_STORE,
    load_recorded_store,
    load_script,
    report,
)

script = load_script()
Report = script.ReportField
Row = script.RowField


def test_a_store_page_with_one_open_change_lists_one_row_for_it() -> None:
    replayed = load_recorded_store(ONE_OPEN_CHANGE_STORE)
    [change] = replayed.direct

    observed = report(replayed)

    assert observed.exit_code == script.EXIT_OK
    assert observed.result[Report.STATUS] == script.ReportStatus.OK
    rows = observed.result[Report.ROWS]
    assert len(rows) == 1
    assert rows[0][Row.NUMBER] == change[Row.NUMBER]
    assert rows[0][Row.URL] == change[Row.URL]
    assert rows[0][Row.TITLE] == change[Row.TITLE]
