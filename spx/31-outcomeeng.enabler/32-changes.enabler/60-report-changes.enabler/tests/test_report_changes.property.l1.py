"""Property evidence: the report lists the matching open Changes of a store, ordered, across every page.

The governing assertion says ``report-changes`` lists each open Change that
passes its filters as one row carrying the store's own values, orders the rows
by the Priority order with a Change that has no Priority standing last and
then by ascending issue number, and reads every page of the store, so the rows
equal the matching open Changes whatever the number of pages.

Cases come from the generator over stores: any number of issues dealt across
any number of pages, with each field and each filter absent or present. The
expected rows come from the statement of the rule in this file, applied to the
generated store, never from the script's matching or ordering code. A script
that stops at the first page, ignores a filter, lists a closed Change, or
orders by anything but Priority and then number returns rows that differ from
the expected ones for some generated store.
"""

from __future__ import annotations

from outcomeeng_testing.generators.report_changes import GeneratedIssue, GeneratedStore
from outcomeeng_testing.harnesses.report_changes import (
    ReportObservation,
    exercise_generated_stores,
    load_script,
)

script = load_script()
Row = script.RowField
Report = script.ReportField


def test_rows_equal_the_matching_open_changes_in_priority_order_over_every_page() -> (
    None
):
    def assert_case(generated: GeneratedStore, observed: ReportObservation) -> None:
        request = generated.request
        last_rank = len(request.priority_order) - 1

        def rank(issue: GeneratedIssue) -> int:
            if issue.priority is None:
                return last_rank
            return request.priority_order.index(issue.priority)

        def has_open_blocker(issue: GeneratedIssue) -> bool:
            return any(
                state == script.BlockerState.OPEN for state in issue.blocker_states
            )

        def passes(issue: GeneratedIssue) -> bool:
            return (
                issue.state == script.IssueState.OPEN
                and (request.product is None or issue.product == request.product)
                and (request.maturity is None or issue.maturity == request.maturity)
                and (request.lifecycle is None or issue.lifecycle == request.lifecycle)
                and (request.holder is None or request.holder in issue.assignees)
                and (
                    request.blocked is None
                    or has_open_blocker(issue)
                    == (request.blocked == script.BlockedFilter.YES)
                )
            )

        expected = sorted(
            (issue for issue in generated.issues if passes(issue)),
            key=lambda issue: (rank(issue), issue.number),
        )

        assert observed.exit_code == script.EXIT_OK
        assert observed.result[Report.STATUS] == script.ReportStatus.OK
        rows = observed.result[Report.ROWS]
        assert [row[Row.NUMBER] for row in rows] == [issue.number for issue in expected]
        for row, issue in zip(rows, expected):
            assert row[Row.URL] == issue.url
            assert row[Row.TITLE] == issue.title
            assert row[Row.PRODUCT] == issue.product
            assert row[Row.MATURITY] == issue.maturity
            assert row[Row.LIFECYCLE] == issue.lifecycle
            assert row[Row.PRIORITY] == issue.priority
            assert row[Row.HOLDER] == list(issue.assignees)
            assert row[Row.PARENT] == issue.parent
        assert len(observed.store_page_calls) == len(generated.page_sizes)

    exercise_generated_stores(assert_case)
