"""Mapping evidence: the report maps a row's root, blockers, changeset, next action, and waiting state.

The two governing assertions state, for each column, the store value it maps
from. The replayed store is a recorded multi-page fixture whose answers hold
a Change in each waiting state, a Parent cycle, an absent Parent, a Change
with no Handoff, a Handoff whose ``Branch or PR`` line reads ``none``, a
Handoff that names a branch, and a Handoff that names a pull request with a
check that has not concluded success. The fixture's ``direct`` rows are those
columns read by hand from its answers, so the script's mapping code selects
neither a case nor an expected row. The waiting-state domain is the script's
own ``Waiting`` enumeration, and the fixture is checked to cover every member.
A script that follows a cycle, drops a closed blocker, reads the oldest
Handoff, or omits ``checks`` returns a column that differs from the fixture's
direct read.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.report_changes import (
    load_recorded_store,
    load_script,
    report,
)

script = load_script()
Row = script.RowField
Report = script.ReportField
Kind = script.ChangesetKind


def test_root_blockers_changeset_and_next_action_equal_the_direct_reads() -> None:
    recorded = load_recorded_store()

    observed = report(recorded)

    assert observed.exit_code == script.EXIT_OK
    rows = observed.result[Report.ROWS]
    assert len(rows) == len(recorded.direct)
    for row, direct in zip(rows, recorded.direct):
        assert row[Row.NUMBER] == direct[Row.NUMBER]
        assert row[Row.ROOT] == direct[Row.ROOT]
        assert row[Row.BLOCKERS] == direct[Row.BLOCKERS]
        assert row[Row.CHANGESET] == direct[Row.CHANGESET]
        assert row[Row.NEXT_ACTION] == direct[Row.NEXT_ACTION]
    roots = [direct[Row.ROOT] for direct in recorded.direct]
    changesets = [direct[Row.CHANGESET] for direct in recorded.direct]
    assert script.UNRESOLVED_ROOT in roots
    assert any(isinstance(root, int) for root in roots)
    assert script.NO_CHANGESET in changesets
    assert any(
        isinstance(changeset, dict)
        and changeset[script.ChangesetField.KIND] == Kind.BRANCH
        for changeset in changesets
    )
    assert any(
        isinstance(changeset, dict)
        and changeset[script.ChangesetField.KIND] == Kind.PULL_REQUEST
        for changeset in changesets
    )
    assert script.NO_NEXT_ACTION in [
        direct[Row.NEXT_ACTION] for direct in recorded.direct
    ]


def test_waiting_state_equals_the_direct_read_for_every_waiting_state() -> None:
    recorded = load_recorded_store()

    observed = report(recorded)

    assert observed.exit_code == script.EXIT_OK
    rows = observed.result[Report.ROWS]
    assert len(rows) == len(recorded.direct)
    for row, direct in zip(rows, recorded.direct):
        assert row[Row.NUMBER] == direct[Row.NUMBER]
        assert row[Row.WAITING] == direct[Row.WAITING]
    direct_entries = [
        entry for direct in recorded.direct for entry in direct[Row.WAITING]
    ]
    for state in script.Waiting:
        assert any(entry.startswith(state) for entry in direct_entries)
