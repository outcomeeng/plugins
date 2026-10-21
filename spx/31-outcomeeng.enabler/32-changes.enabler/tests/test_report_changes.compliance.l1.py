"""Compliance evidence: the report blocks instead of shortening its list, and it never writes.

Two governing rules. The first forbids a shorter list in place of a failure:
a read that fails, returns unreadable output, or fills a bound yields a
blocked result naming the failed read or the bound and no row. The violating
cases are the failures of every kind of read the script makes, each in every
way a read fails (a nonzero exit, output that is not JSON, a `gh` that cannot
start), and one store per bound: an issue connection that never ends, an issue
whose field-value connection is full, a blocker list that is full, an assignee
connection that is full, and an event timeline that never ends. The
bounds come from the spec assertion text, and the counts that fill them come
from the bounds. A script that skips a failed read, or returns the rows it has,
returns rows where the rule demands none.

The second forbids a write. The script runs under an audit-hook recorder in an
empty working directory, and every `gh` command it issues is classified by the
vocabulary of `gh`, HTTP, and GraphQL, which those tools own.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.report_changes import (
    GH_API,
    GH_ISSUE,
    GH_PULL_REQUEST,
    GH_READ_METHOD,
    GH_VIEW,
    GRAPHQL_WRITE_OPERATION,
    Fault,
    FaultKind,
    ReadKind,
    filled_assignees,
    filled_blockers,
    filled_field_values,
    load_recorded_store,
    load_script,
    omitting_a_held_priority,
    report,
    spec_bounds,
    unending_events,
    unending_issues,
)

script = load_script()
Report = script.ReportField


def test_a_failed_read_of_any_kind_blocks_naming_the_read_and_returns_no_row() -> None:
    recorded = load_recorded_store()
    pull_requests = [
        direct[script.RowField.CHANGESET][script.ChangesetField.REF]
        for direct in recorded.direct
        if isinstance(direct[script.RowField.CHANGESET], dict)
        and direct[script.RowField.CHANGESET][script.ChangesetField.KIND]
        == script.ChangesetKind.PULL_REQUEST
    ]

    for read in ReadKind:
        subjects = pull_requests if read == ReadKind.CHECKS else [recorded.store]
        for kind in FaultKind:
            observed = report(recorded, fault=Fault(read, kind))

            assert observed.exit_code == script.EXIT_BLOCKED, (read, kind)
            assert observed.result[Report.STATUS] == script.ReportStatus.BLOCKED
            assert Report.ROWS not in observed.result
            assert any(
                subject in observed.result[Report.READ] for subject in subjects
            ), (read, kind)
            assert observed.result[Report.DETAIL]


def test_an_issue_connection_that_never_ends_blocks_naming_the_page_bound() -> None:
    bounds = spec_bounds()

    observed = report(unending_issues(load_recorded_store()))

    assert observed.exit_code == script.EXIT_BLOCKED
    assert observed.result[Report.STATUS] == script.ReportStatus.BLOCKED
    assert observed.result[Report.BOUND] == bounds.issues
    assert Report.ROWS not in observed.result
    assert len(observed.store_page_calls) == bounds.page_count


def test_a_full_field_value_connection_blocks_naming_its_bound() -> None:
    bounds = spec_bounds()

    observed = report(
        filled_field_values(load_recorded_store(), bounds.field_value_count)
    )

    assert observed.exit_code == script.EXIT_BLOCKED
    assert observed.result[Report.STATUS] == script.ReportStatus.BLOCKED
    assert observed.result[Report.BOUND] == bounds.field_values
    assert Report.ROWS not in observed.result


def test_a_full_blocker_list_blocks_naming_its_bound() -> None:
    bounds = spec_bounds()

    observed = report(filled_blockers(load_recorded_store(), bounds.blocker_count))

    assert observed.exit_code == script.EXIT_BLOCKED
    assert observed.result[Report.STATUS] == script.ReportStatus.BLOCKED
    assert observed.result[Report.BOUND] == bounds.blockers
    assert Report.ROWS not in observed.result


def test_a_full_assignee_connection_blocks_naming_its_bound() -> None:
    """Design record.

    Assertion: NEVER return a shorter list when a read fills a bound; the
    `100 assignees` bound.
    Production subject: the script's entry point reading a store whose first
    issue returns as many assignees as the bound.
    Case provenance: the count comes from the bound in the spec assertion text.
    Oracle owner: the spec assertion text names the bound and demands no row.
    Rejected mutation: the script drops its assignee-limit check and returns
    rows.
    Failure observation: the exit code is not blocked, the bound is absent, and
    rows are present.
    """
    bounds = spec_bounds()

    observed = report(filled_assignees(load_recorded_store(), bounds.assignee_count))

    assert observed.exit_code == script.EXIT_BLOCKED
    assert observed.result[Report.STATUS] == script.ReportStatus.BLOCKED
    assert observed.result[Report.BOUND] == bounds.assignees
    assert Report.ROWS not in observed.result


def test_an_event_timeline_that_never_ends_blocks_naming_the_event_bound() -> None:
    """Design record.

    Assertion: NEVER return a shorter list when a read fills a bound; the
    `100 events per page, 10 pages` bound.
    Production subject: the script's entry point reading a Claimed Change whose
    field-change event timeline reports a further page on every page.
    Case provenance: the page count comes from the bound in the spec assertion
    text; the Claimed Change is in the recorded store.
    Oracle owner: the spec assertion text names the bound and demands no row.
    Rejected mutation: the script returns the moves it has after the last page
    instead of blocking.
    Failure observation: the exit code is not blocked, the bound is absent, rows
    are present, or the event pages read differ from the bound's page count.
    """
    bounds = spec_bounds()

    observed = report(unending_events(load_recorded_store()))

    assert observed.exit_code == script.EXIT_BLOCKED
    assert observed.result[Report.STATUS] == script.ReportStatus.BLOCKED
    assert observed.result[Report.BOUND] == bounds.events
    assert Report.ROWS not in observed.result
    assert len(observed.event_page_calls) == bounds.event_page_count


def test_a_priority_the_order_omits_blocks_naming_the_priority_order_and_returns_no_row() -> (
    None
):
    """Design record.

    Assertion: NEVER return a shorter list in place of a failure; a Change
    whose Priority the declared Priority order omits yields a blocked result
    naming the priority-order read and no row.
    Production subject: the script's entry point reading a store whose open
    Change holds a Priority that `--priority-order` does not list.
    Case provenance: the recorded store; the omitted Priority is the first
    Priority an open Change holds in reading order, dropped from the recorded
    Priority order.
    Oracle owner: the script's priority-order read name, exported by the script,
    and the spec assertion text, which demands a blocked result and no row.
    Rejected mutation: the script drops or misplaces the Change whose Priority
    the order omits and returns the rows it has.
    Failure observation: the exit code is not blocked, the read name differs
    from the script's, the detail omits the Change or the Priority, or rows are
    present.
    """
    omitted = omitting_a_held_priority(load_recorded_store())

    observed = report(omitted.store)

    assert observed.exit_code == script.EXIT_BLOCKED
    assert observed.result[Report.STATUS] == script.ReportStatus.BLOCKED
    assert observed.result[Report.READ] == script.PRIORITY_ORDER_READ
    assert f"{omitted.store.store}#{omitted.number}" in observed.result[Report.DETAIL]
    assert repr(omitted.priority) in observed.result[Report.DETAIL]
    assert Report.ROWS not in observed.result


def test_the_script_issues_reading_commands_only_and_writes_no_file() -> None:
    recorded = load_recorded_store()

    for replayed in (recorded, unending_issues(recorded)):
        observed = report(replayed)

        assert observed.calls
        for call in observed.calls:
            if call.graphql_query is not None:
                assert not call.graphql_query.lstrip().startswith(
                    GRAPHQL_WRITE_OPERATION
                )
            elif call.command == GH_API:
                assert call.rest_method == GH_READ_METHOD
            else:
                assert call.command in (GH_ISSUE, GH_PULL_REQUEST)
                assert call.verb == GH_VIEW
        assert observed.writes == ()
        assert observed.working_directory_entries == ()
