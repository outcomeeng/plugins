"""Mapping evidence: the report maps a row's root, blockers, changeset, next action, and waiting state.

The two governing assertions state, for each column, the store value it maps
from. The replayed store is a recorded multi-page fixture whose answers hold
a Change in each waiting state, a Parent cycle, an absent Parent, a Change
with no Handoff, a Handoff whose ``Branch or PR`` line reads ``none``, a
Handoff that names a branch, and a Handoff that names a pull request with a
check that has not concluded success, and a Claimed Change that was released
and claimed again, with its field-change events. The fixture's ``direct`` rows are those
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


def test_a_reclaimed_change_waits_on_the_holder_of_the_claim_after_its_newest_available_move() -> (
    None
):
    """Design record.

    Assertion: a `Claimed` Change's waiting state maps to `holder: <login>` with
    the session and claim root of its winning Claim, the earliest Claim comment
    posted after the newest Handoff that a Lifecycle move to Available follows.
    Production subject: the script's entry point reading a Claimed Change whose
    comments hold three Claims, each followed by a Handoff, and whose
    field-change events hold a move to Available after each of the first two.
    Case provenance: the recorded store's reclaimed Change, whose comments and
    events the fixture records; the stale Claims are the ones before the last.
    Oracle owner: the fixture's direct row, read by hand from those answers by
    the spec sentence.
    Rejected mutation: the script's winning-claim bound compares against the
    oldest Available move instead of the newest, or ignores the moves and takes
    the first Claim since creation, or bounds by the newest Handoff overall.
    Failure observation: the row's waiting entry differs from the direct row,
    names a stale Claim's session, or names no winning Claim's session.
    """
    recorded = load_recorded_store()

    observed = report(recorded)

    assert observed.exit_code == script.EXIT_OK
    assert recorded.events
    rows = {row[Row.NUMBER]: row for row in observed.result[Report.ROWS]}
    directs = {direct[Row.NUMBER]: direct for direct in recorded.direct}
    for number, events in recorded.events.items():
        assert events
        claims = [
            comment
            for comment in recorded.comments[number]
            if comment["body"].startswith(script.CLAIM_PREFIX)
        ]
        stale, winning = claims[:-1], claims[-1]
        assert stale
        waiting = rows[int(number)][Row.WAITING]
        assert waiting == directs[int(number)][Row.WAITING]
        session, claim_root = winning["body"].split()[1:3]
        assert (
            f"{winning['author']['login']} (session {session}, root {claim_root})"
            in waiting[0]
        )
        for comment in stale:
            stale_session, stale_root = comment["body"].split()[1:3]
            assert stale_session not in waiting[0]
            assert stale_root not in waiting[0]
    assert observed.event_page_calls


def test_a_claimed_change_with_no_claim_comment_waits_on_its_assignees() -> None:
    """Design record.

    Assertion: a `Claimed` Change's waiting state maps to `holder: <login>`; a
    Claimed Change with no Claim comment has no winning Claim, so the entry
    names its assignee logins and records that no claim was found.
    Production subject: the script's entry point reading a Claimed Change whose
    comments hold no Claim.
    Case provenance: the recorded store's Claimed Change that has no comments
    and two assignees.
    Oracle owner: the fixture's direct row, read by hand from those answers.
    Rejected mutation: the script names no assignee, names only the first
    assignee, or reports a session and root it never read.
    Failure observation: the row's waiting entry differs from the direct row or
    omits an assignee login or the no-claim marker.
    """
    recorded = load_recorded_store()

    observed = report(recorded)

    assert observed.exit_code == script.EXIT_OK
    rows = {row[Row.NUMBER]: row for row in observed.result[Report.ROWS]}
    unclaimed = [
        direct
        for direct in recorded.direct
        if direct[Row.WAITING][0].startswith(script.Waiting.HOLDER)
        and not any(
            comment["body"].startswith(script.CLAIM_PREFIX)
            for comment in recorded.comments.get(str(direct[Row.NUMBER]), [])
        )
    ]
    assert unclaimed
    for direct in unclaimed:
        waiting = rows[direct[Row.NUMBER]][Row.WAITING]
        assert waiting == direct[Row.WAITING]
        assert len(direct[Row.HOLDER]) > 1
        assert waiting[0].startswith(f"{script.Waiting.HOLDER}: ")
        for login in direct[Row.HOLDER]:
            assert login in waiting[0]
        assert f"claim {script.NO_NEXT_ACTION}" in waiting[0]
