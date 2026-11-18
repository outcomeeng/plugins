"""Compliance evidence: read-relations returns absorbers, reads every page, and blocks at its bounds.

The rules are the spec assertions for the ``audit-change`` runner's
``read-relations`` operation. Each violating case is a replayed store scenario
that a faulty reader gets wrong: an issue whose own ``Predecessors`` value names
issues and a child whose ``Predecessors`` value names the named issue, which a
reader of ``Predecessors`` returns as absorbers instead of the issue the
duplicate link names, for the absorbers rule; a Children read that is no filter
on the ``Parent`` field or a page size other than the stated one, and a child
that sits on a page after the first, for the Children read rule; a store that
never ends its Children connection, for the Children-page bound; and an issue
whose field-value connection reports a further page, for the field-value
bound. Each scenario
states what its issues declare, the bounds come from the assertion text, and
the store answers come from replayed fixture files, so no expected value is
chosen here and no call reaches the network.
"""

from __future__ import annotations

import re

from outcomeeng_testing.harnesses.audit_change_relations import (
    ABSORBERS,
    CHILDREN_ON_LATER_PAGE,
    FIELD_VALUES_UNFINISHED,
    NOT_DUPLICATE,
    UNENDING_ISSUES,
    declared,
    read_relations,
    spec_field_value_bound,
    spec_children_page_size,
    spec_issue_page_bound,
)
from outcomeeng_testing.harnesses.audit_change_run import load_runner

runner = load_runner()
Result = runner.ResultField
Status = runner.ResultStatus
Reason = runner.BlockReason
ExitCode = runner.ExitCode


def test_the_absorber_is_the_issue_the_duplicate_link_names_and_no_predecessors_issue() -> (
    None
):
    observed = read_relations(ABSORBERS)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.STATUS] == Status.OK
    assert observed.result[Result.ABSORBERS] == declared(ABSORBERS)


def test_an_issue_not_closed_as_a_duplicate_has_no_absorber() -> None:
    observed = read_relations(NOT_DUPLICATE)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.STATUS] == Status.OK
    assert observed.result[Result.ABSORBERS] == declared(NOT_DUPLICATE)


def test_children_are_read_through_the_parent_field_filter_in_pages_of_the_stated_size() -> (
    None
):
    size = spec_children_page_size()

    observed = read_relations(CHILDREN_ON_LATER_PAGE)

    assert observed.queries
    for query in observed.queries:
        assert "filterBy" in query
        assert runner.PARENT_FIELD in query
        assert re.search(rf"first:\s*{size}\b", query)


def test_a_child_on_a_later_page_is_returned_after_reading_pages_in_order() -> None:
    observed = read_relations(CHILDREN_ON_LATER_PAGE)

    assert observed.exit_code == ExitCode.OK
    assert [
        child[Result.NUMBER] for child in observed.result[Result.CHILDREN]
    ] == declared(CHILDREN_ON_LATER_PAGE)
    assert observed.cursors[0] is None
    assert any(cursor is not None for cursor in observed.cursors[1:])


def test_a_store_that_never_ends_its_children_blocks_naming_the_page_bound() -> None:
    bound = spec_issue_page_bound()
    page_count = int(bound.split()[-2])

    observed = read_relations(UNENDING_ISSUES)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.PAGE_BOUND_REACHED
    assert observed.result[Result.BOUND] == bound
    assert len(observed.store_calls) == page_count
    assert all("filterBy" in query for query in observed.queries)


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
