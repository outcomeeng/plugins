"""Compliance evidence: the report blocks instead of shortening its list, and it never writes.

Two governing rules. The first forbids a shorter list in place of a failure:
a read that fails, returns unreadable output, or fills a bound yields a
blocked result naming the failed read or the bound and no row. The violating
cases are the failures of every kind of read the script makes, each in every
way a read fails (a nonzero exit, output that is not JSON, a `gh` that cannot
start), and one store per bound: an issue connection that never ends, an issue
whose field-value connection is full, and a blocker list that is full. The
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
    filled_blockers,
    filled_field_values,
    load_recorded_store,
    load_script,
    report,
    spec_bounds,
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
