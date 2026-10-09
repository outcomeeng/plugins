"""Compliance evidence: read-published returns the published body or blocks with its declared reason.

The rule is the spec assertion for the ``audit-change`` runner's
``read-published`` operation: it takes exactly an operation name and a
canonical ``<owner>/<repo>#<N>`` issue identity, reads that issue's body through
one ``gh`` query, writes nothing, and returns the body, the empty string when
the store holds none. The violating cases are the three the assertion names: a
malformed request, generated outside the stated request shape, blocks with
``invalid-request`` before any query; a ``gh`` call that fails or cannot start
blocks with ``command-failed``; and a store answer without a body string blocks
with ``unreadable-output``. The store answers come from replayed fixture files
and the failure from a recorded ``gh`` result, so no expected body is chosen
here and no call reaches the network.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from outcomeeng_testing.harnesses.audit_change_published import (
    EMPTY_BODY_ANSWER,
    PUBLISHED_BODY_ANSWER,
    PUBLISHED_ISSUE,
    PublishedObservation,
    bodyless_answers,
    exercise_malformed_published_requests,
    read_published,
    read_published_with_failed_gh,
    read_published_without_gh,
    recorded_failure,
    stored_body,
)
from outcomeeng_testing.harnesses.audit_change_run import load_runner

runner = load_runner()
Operation = runner.Operation
Result = runner.ResultField
Status = runner.ResultStatus
Reason = runner.BlockReason
ExitCode = runner.ExitCode


def test_a_canonical_request_returns_the_published_body_from_one_gh_query_and_writes_nothing() -> (
    None
):
    owner, _, rest = PUBLISHED_ISSUE.partition("/")
    repository, _, number = rest.partition("#")

    observed = read_published(PUBLISHED_BODY_ANSWER)

    assert observed.exit_code == ExitCode.OK
    assert len(observed.stdout_lines) == 1
    assert observed.result[Result.OPERATION] == Operation.READ_PUBLISHED
    assert observed.result[Result.STATUS] == Status.OK
    assert observed.result[Result.ISSUE] == PUBLISHED_ISSUE
    assert observed.result[Result.BODY] == stored_body(PUBLISHED_BODY_ANSWER)
    assert len(observed.store_calls) == 1
    (query,) = observed.store_calls
    assert query[0] == runner.GH_EXECUTABLE
    for part in (owner, repository, number):
        assert any(argument.endswith(f"={part}") for argument in query)
    assert observed.runner_writes == ()
    assert observed.spawned_commands == ()


def test_a_store_holding_no_body_returns_the_empty_string() -> None:
    observed = read_published(EMPTY_BODY_ANSWER)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.STATUS] == Status.OK
    assert observed.result[Result.BODY] == ""
    assert len(observed.store_calls) == 1
    assert observed.runner_writes == ()


@pytest.mark.parametrize("answer", bodyless_answers(), ids=lambda path: path.stem)
def test_a_store_answer_without_a_body_string_blocks_as_unreadable_output(
    answer: Path,
) -> None:
    observed = read_published(answer)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.OPERATION] == Operation.READ_PUBLISHED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.UNREADABLE_OUTPUT
    assert Result.BODY not in observed.result
    assert len(observed.store_calls) == 1
    assert observed.runner_writes == ()


def test_a_failed_gh_call_blocks_as_command_failed_with_its_diagnostic() -> None:
    failure = recorded_failure()

    observed = read_published_with_failed_gh()

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.COMMAND_FAILED
    assert observed.result[Result.EXIT_CODE] == failure.exit_code
    assert observed.result[Result.STDERR] == failure.stderr
    assert str(observed.result[Result.COMMAND]).startswith(runner.GH_EXECUTABLE)
    assert Result.BODY not in observed.result
    assert len(observed.store_calls) == 1
    assert observed.runner_writes == ()


def test_a_gh_call_that_cannot_start_blocks_as_command_failed() -> None:
    observed = read_published_without_gh()

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.COMMAND_FAILED
    assert str(observed.result[Result.COMMAND]).startswith(runner.GH_EXECUTABLE)
    assert Result.BODY not in observed.result
    assert len(observed.store_calls) == 1
    assert observed.runner_writes == ()


def test_a_generated_malformed_request_blocks_as_invalid_request_before_any_query() -> (
    None
):
    def assert_refused_without_a_query(
        _request: Mapping[str, object], observed: PublishedObservation
    ) -> None:
        assert observed.exit_code == ExitCode.INVALID_REQUEST
        assert len(observed.stdout_lines) == 1
        assert observed.result[Result.OPERATION] == Operation.READ_PUBLISHED
        assert observed.result[Result.STATUS] == Status.BLOCKED
        assert observed.result[Result.REASON] == Reason.INVALID_REQUEST
        assert Result.BODY not in observed.result
        assert observed.store_calls == ()
        assert observed.runner_writes == ()
        assert observed.spawned_commands == ()

    exercise_malformed_published_requests(assert_refused_without_a_query)
