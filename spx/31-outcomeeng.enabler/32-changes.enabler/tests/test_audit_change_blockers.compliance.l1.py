"""Compliance evidence: read-blockers reads within its page and issue bounds and blocks at them.

The rule is the spec assertion for the ``audit-change`` runner's
``read-blockers`` operation: it reads a Change's native blockers one page of a
stated size per issue, returns each blocker's canonical identity and whether it
is open, reads at most a stated number of issues when it walks the blockers' own
blockers, and returns a blocked result naming the bound when a read fills it.
The page size and issue count come from that assertion's text, and the blocker
graphs the store replays are built by construction in the harness, so no
expected value is chosen here. The violating cases are a page that holds a full
page of blockers and a walk that needs one issue more than the bound, which no
read may follow.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.audit_change_blockers import (
    RING_LENGTH,
    UNWALKED_CHAIN_LENGTH,
    chain,
    closed_blocker,
    identity,
    read_blockers,
    ring,
    spec_blocker_bound,
    wide,
)
from outcomeeng_testing.harnesses.audit_change_run import load_runner

runner = load_runner()
Result = runner.ResultField
Status = runner.ResultStatus
Reason = runner.BlockReason
ExitCode = runner.ExitCode

FIRST = 1


def test_a_page_below_the_bound_returns_each_blocker_identity_and_open_state_from_one_read() -> (
    None
):
    bound = spec_blocker_bound()
    graph = wide(bound.page_size - 1)

    observed = read_blockers(graph, walk=False)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.STATUS] == Status.OK
    assert observed.result[Result.ISSUE] == identity(FIRST)
    assert observed.result[Result.BLOCKERS] == [
        {Result.ISSUE: identity(number), Result.OPEN: is_open}
        for number, is_open in graph[FIRST]
    ]
    assert observed.result[Result.CYCLES] == []
    assert observed.result[Result.ISSUES_READ] == 1
    assert [call.issue_number for call in observed.calls] == [FIRST]
    assert [call.page_size for call in observed.calls] == [bound.page_size]


def test_a_page_that_fills_the_bound_blocks_naming_it() -> None:
    bound = spec_blocker_bound()

    observed = read_blockers(wide(bound.page_size), walk=False)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.PAGE_BOUND_REACHED
    assert str(bound.page_size) in str(observed.result[Result.BOUND])
    assert Result.BLOCKERS not in observed.result
    assert [call.issue_number for call in observed.calls] == [FIRST]


def test_a_read_without_a_walk_reads_only_the_named_issue() -> None:
    observed = read_blockers(chain(UNWALKED_CHAIN_LENGTH), walk=False)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.BLOCKERS] == [
        {Result.ISSUE: identity(2), Result.OPEN: True}
    ]
    assert observed.result[Result.ISSUES_READ] == 1
    assert [call.issue_number for call in observed.calls] == [FIRST]


def test_a_walk_that_ends_within_the_bound_reads_each_open_blocker_once() -> None:
    bound = spec_blocker_bound()

    observed = read_blockers(chain(bound.max_issues), walk=True)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.CYCLES] == []
    assert observed.result[Result.ISSUES_READ] == bound.max_issues
    assert [call.issue_number for call in observed.calls] == list(
        range(FIRST, bound.max_issues + 1)
    )


def test_a_walk_that_needs_one_issue_more_than_the_bound_blocks_naming_it() -> None:
    bound = spec_blocker_bound()

    observed = read_blockers(chain(bound.max_issues + 1), walk=True)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.PAGE_BOUND_REACHED
    assert str(bound.max_issues) in str(observed.result[Result.BOUND])
    assert Result.CYCLES not in observed.result
    assert len(observed.calls) == bound.max_issues


def test_a_walk_returns_the_cycle_that_open_blockers_close() -> None:
    length = RING_LENGTH

    observed = read_blockers(ring(length), walk=True)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.CYCLES] == [
        [identity(number) for number in range(FIRST, length + 1)] + [identity(FIRST)]
    ]
    assert observed.result[Result.ISSUES_READ] == length


def test_a_walk_does_not_follow_a_closed_blocker() -> None:
    observed = read_blockers(closed_blocker(), walk=True)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.BLOCKERS] == [
        {Result.ISSUE: identity(2), Result.OPEN: False}
    ]
    assert observed.result[Result.CYCLES] == []
    assert observed.result[Result.ISSUES_READ] == 1
    assert [call.issue_number for call in observed.calls] == [FIRST]
