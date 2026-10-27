"""Compliance evidence: the blocker reads return identity and openness within their bounds.

The rule is the spec assertion for the ``audit-change`` runner's blocker
operations: a Change's native blockers are read one page of a stated size per
issue, each blocker is returned with its canonical identity and whether it is
open, a walk of the blockers' own blockers reads at most a stated number of
issues, and a read that fills a bound returns a blocked result naming it. The
page size and the issue bound come from that assertion's text, and the store
answers come from replayed fixture files, so no expected value is chosen here
and no call reaches the network. The violating cases are a blocker page that
fills the page size, which no read may follow, and a chain of blockers
longer than the walk may read, which no walk may follow to its end.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.audit_change_blockers import (
    BLOCKERS_UNFINISHED,
    OPEN_AND_CLOSED,
    WALK_PAST_BOUND,
    WALK_WITHIN_BOUND,
    answered_blocker_count,
    declared_blockers,
    declared_graph,
    request_blockers,
    spec_issue_bound,
    spec_page_size,
)
from outcomeeng_testing.harnesses.audit_change_run import load_runner

runner = load_runner()
Result = runner.ResultField
Status = runner.ResultStatus
Reason = runner.BlockReason
ExitCode = runner.ExitCode
Operation = runner.Operation


def test_a_read_returns_each_blocker_with_its_identity_and_openness_in_one_page() -> (
    None
):
    page_size = spec_page_size()

    observed = request_blockers(OPEN_AND_CLOSED, Operation.READ_BLOCKERS)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.STATUS] == Status.OK
    assert observed.result[Result.BLOCKERS] == declared_blockers(OPEN_AND_CLOSED)
    assert len(observed.store_calls) == 1
    assert observed.page_sizes() == (str(page_size),)


def test_a_blocker_page_that_fills_the_page_size_blocks_naming_the_page_size() -> None:
    page_size = spec_page_size()
    assert answered_blocker_count(BLOCKERS_UNFINISHED) == page_size

    observed = request_blockers(BLOCKERS_UNFINISHED, Operation.READ_BLOCKERS)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.PAGE_BOUND_REACHED
    assert str(page_size) in str(observed.result[Result.BOUND])
    assert Result.BLOCKERS not in observed.result
    assert len(observed.store_calls) == 1


def test_a_walk_within_the_bound_returns_each_issue_with_its_blockers() -> None:
    bound = spec_issue_bound()
    graph = declared_graph(WALK_WITHIN_BOUND)
    assert len(graph) <= bound

    observed = request_blockers(WALK_WITHIN_BOUND, Operation.WALK_BLOCKERS)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.STATUS] == Status.OK
    assert observed.result[Result.GRAPH] == graph
    assert list(observed.issues_asked) == [entry[Result.ISSUE] for entry in graph]


def test_a_walk_that_fills_the_issue_bound_blocks_naming_it_and_reads_no_further() -> (
    None
):
    bound = spec_issue_bound()

    observed = request_blockers(WALK_PAST_BOUND, Operation.WALK_BLOCKERS)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.PAGE_BOUND_REACHED
    assert str(bound) in str(observed.result[Result.BOUND])
    assert Result.GRAPH not in observed.result
    assert len(observed.store_calls) == bound
    assert len(set(observed.issues_asked)) == bound
