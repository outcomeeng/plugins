"""Compliance evidence: read-authority reads within its page bound and blocks at it.

The rule is the spec assertion for the ``audit-change`` runner's
``read-authority`` operation: it reads a Change's field-change events and
comments at a stated page size and for at most a stated number of pages, and
returns a blocked result naming the bound when the read fills it. The page size
and page count come from that assertion's text, and the entries each page holds
come from the recorded store pages the harness replays, so no expected value is
chosen here. The violating case is a store that keeps reporting a further page
for one connection, which no read may follow past the bound.
"""

from __future__ import annotations

import pytest

from outcomeeng_testing.harnesses.audit_change_authority import (
    AuthorityRead,
    read_authority,
    spec_page_bound,
)
from outcomeeng_testing.harnesses.audit_change_run import load_runner

runner = load_runner()
Result = runner.ResultField
Status = runner.ResultStatus
Reason = runner.BlockReason
ExitCode = runner.ExitCode


def test_a_read_that_ends_before_the_bound_returns_every_recorded_entry() -> None:
    bound = spec_page_bound()

    observed = read_authority(filled=None)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.STATUS] == Status.OK
    assert (
        len(observed.result[Result.EVENTS])
        == observed.pages[AuthorityRead.EVENTS].node_count
    )
    assert (
        len(observed.result[Result.COMMENTS])
        == observed.pages[AuthorityRead.COMMENTS].node_count
    )
    for kind in AuthorityRead:
        asked = observed.calls_for(kind)
        assert len(asked) == 1
        assert f"first:{bound.page_size}" in asked[0].query
        assert asked[0].after is None


@pytest.mark.parametrize("filled", list(AuthorityRead))
def test_a_read_that_fills_the_bound_blocks_naming_it(filled: AuthorityRead) -> None:
    bound = spec_page_bound()

    observed = read_authority(filled=filled)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.PAGE_BOUND_REACHED
    assert str(bound.page_size) in str(observed.result[Result.BOUND])
    assert str(bound.max_pages) in str(observed.result[Result.BOUND])
    assert str(filled) in str(observed.result[Result.BOUND])
    asked = observed.calls_for(filled)
    assert len(asked) == bound.max_pages
    assert [call.after for call in asked] == [None] + [
        observed.pages[filled].end_cursor
    ] * (bound.max_pages - 1)
    assert Result.EVENTS not in observed.result
    assert Result.COMMENTS not in observed.result
