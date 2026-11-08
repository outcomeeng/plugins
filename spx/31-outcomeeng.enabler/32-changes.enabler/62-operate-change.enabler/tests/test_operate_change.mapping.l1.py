"""Mapping evidence for the operate-change script.

Each row of the spec's transitions, maturity-ready, and store-writes tables is
one case. The script reaches the Change Store only through its command runner,
so each case runs it against the simulated GitHub store of
`outcomeeng_testing.harnesses.operate_change`. The rows, the states a row does
not admit, and the records come from
`outcomeeng_testing.generators.operate_change`, which carries the spec's
tables; the vocabulary comes from the script that owns it.
"""

from __future__ import annotations

from typing import Any

import pytest

from outcomeeng_testing.generators.operate_change import (
    ADVANCES_INTO,
    ROWS,
    STORE_HOMES,
    Part,
    ready,
    refused_states,
    state_store,
    transition_request,
)
from outcomeeng_testing.harnesses.operate_change import (
    LOGIN,
    Field,
    IdentityKey,
    LogKey,
    Maturity,
    ObservedKey,
    RequestKey,
    ResultKey,
    SimulatedGitHub,
    Status,
    Transition,
    run,
    script,
    write_kind,
)


def observed(github: SimulatedGitHub, number: int = 10) -> dict[ObservedKey, Any]:
    issue = github.issues[number]
    return {
        ObservedKey.MATURITY: issue.fields.get(Field.MATURITY),
        ObservedKey.LIFECYCLE: issue.fields.get(Field.LIFECYCLE),
        ObservedKey.ASSIGNEES: tuple(issue.assignees),
        ObservedKey.STATE: issue.state,
    }


# ------------------------------------------------------------ transitions


@pytest.mark.parametrize("transition", list(Transition))
def test_transition_changes_only_what_its_row_states(transition: Transition) -> None:
    row = ROWS[transition]
    github = state_store(row.start)
    before = observed(github)

    result = run(github, transition_request(transition, github))

    after = observed(github)
    assert result[ResultKey.STATUS] == Status.DONE, result
    changed = {key: after[key] for key in after if after[key] != before[key]}
    assert changed == row.changes


@pytest.mark.parametrize("transition", list(Transition))
def test_transition_reports_any_other_state_without_a_write(
    transition: Transition,
) -> None:
    states = refused_states(transition)
    assert states
    for state in states:
        github = state_store(state)

        result = run(github, transition_request(transition, github))

        assert result[ResultKey.STATUS] == Status.REFUSED, (state, result)
        assert github.writes() == [], state


# ---------------------------------------------------------- maturity-ready


@pytest.mark.parametrize("row", list(Maturity))
def test_advance_only_when_the_record_meets_its_row(row: Maturity) -> None:
    github, payload = ready(row)

    assert run(github, payload)[ResultKey.STATUS] == Status.DONE
    assert github.issues[10].fields[Field.MATURITY] == ADVANCES_INTO[row]

    missed, missed_payload = ready(row, met=False)
    before = missed.issues[10].fields[Field.MATURITY]

    assert run(missed, missed_payload)[ResultKey.STATUS] == Status.REFUSED
    assert missed.issues[10].fields[Field.MATURITY] == before
    assert missed.writes() == []


# ------------------------------------------------------------- store-writes


@pytest.mark.parametrize("part", list(Part))
def test_each_part_reaches_its_one_home(part: Part) -> None:
    transition, home = STORE_HOMES[part]
    github = state_store(ROWS[transition].start)
    payload = transition_request(transition, github)

    assert run(github, payload)[ResultKey.STATUS] == Status.DONE

    kinds = [write_kind(command) for command in github.writes()]
    assert kinds.count(home) == 1
    if part == Part.HOLDER:
        assert github.issues[10].assignees == [LOGIN]
    if part == Part.TRANSITION:
        block = script.parse_block(github.blocks(10)[-1])
        assert block[LogKey.TRANSITION] == transition
        assert (
            block[LogKey.SESSION] == payload[RequestKey.IDENTITY][IdentityKey.SESSION]
        )
