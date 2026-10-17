"""Compliance evidence: read-relations returns absorbers, reads every page, and blocks at its bounds.

The rules are the spec assertions for the ``audit-change`` runner's
``read-relations`` operation. Each violating case is a replayed store scenario
that a faulty reader gets wrong: issues whose ``Predecessors`` value only
contains the named issue's number as a prefix of another number, or that the
named issue's own value names, for the absorbers rule; a child that sits on a
page after the first, for the page-order rule; a store that never ends its
issue connection, for the issue-page bound; and an issue whose field-value
connection reports a further page, for the field-value bound. Each scenario
states what its issues declare, the bounds come from the assertion text, and
the store answers come from replayed fixture files, so no expected value is
chosen here and no call reaches the network.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.audit_change_relations import (
    ABSORBERS,
    CHILDREN_ON_LATER_PAGE,
    FIELD_VALUES_UNFINISHED,
    UNENDING_ISSUES,
    declared,
    read_relations,
    spec_field_value_bound,
    spec_issue_page_bound,
)
from outcomeeng_testing.harnesses.audit_change_run import load_runner

runner = load_runner()
Result = runner.ResultField
Status = runner.ResultStatus
Reason = runner.BlockReason
ExitCode = runner.ExitCode


def test_absorbers_are_the_issues_whose_predecessors_name_the_issue_and_no_other() -> (
    None
):
    observed = read_relations(ABSORBERS)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.STATUS] == Status.OK
    assert observed.result[Result.ABSORBERS] == declared(ABSORBERS)


def test_a_child_on_a_later_page_is_returned_after_reading_pages_in_order() -> None:
    observed = read_relations(CHILDREN_ON_LATER_PAGE)

    assert observed.exit_code == ExitCode.OK
    assert [
        child[Result.NUMBER] for child in observed.result[Result.CHILDREN]
    ] == declared(CHILDREN_ON_LATER_PAGE)
    assert observed.cursors[0] is None
    assert all(cursor is not None for cursor in observed.cursors[1:])
    assert len(observed.store_calls) == 3


def test_a_store_that_never_ends_its_issues_blocks_naming_the_page_bound() -> None:
    bound = spec_issue_page_bound()
    page_count = int(bound.split()[-2])

    observed = read_relations(UNENDING_ISSUES)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.PAGE_BOUND_REACHED
    assert observed.result[Result.BOUND] == bound
    assert len(observed.store_calls) == page_count


def test_a_filled_field_value_connection_blocks_and_returns_no_product_or_parent() -> (
    None
):
    bound = spec_field_value_bound()

    observed = read_relations(FIELD_VALUES_UNFINISHED)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.PAGE_BOUND_REACHED
    assert observed.result[Result.BOUND] == bound
    assert Result.PRODUCT not in observed.result
    assert Result.PARENT not in observed.result
