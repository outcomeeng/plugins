"""Compliance evidence: retain-record retains the composed Change Draft through SPX or blocks.

The rule is the spec assertion for the ``audit-change`` runner's
``retain-record`` operation: it composes the Change Draft of the named issue
from each part's home in the store, retains it through one ``spx change draft
create`` command that reads the Draft on stdin with the Product's checkout
root as the working directory, and returns the retained Draft's path under
that root and its digest. The violating cases are the ones the assertion
names: a draft store that retains other content than the Draft it received
blocks with ``retained-input-mismatch``, and a store or ``spx`` command that
fails or cannot start blocks with ``command-failed``. The store answers come
from replayed fixture files and the failures from recorded command results,
so no record is chosen here and no call reaches the network.
"""

from __future__ import annotations

import hashlib

from outcomeeng_testing.harnesses.audit_change_published import recorded_failure
from outcomeeng_testing.harnesses.audit_change_record import (
    RECORD_ISSUE,
    DraftStoreCondition,
    StoreCondition,
    recorded_spx_failure,
    retain_record,
    stored_record,
)
from outcomeeng_testing.harnesses.audit_change_run import load_runner

runner = load_runner()
Operation = runner.Operation
Result = runner.ResultField
Status = runner.ResultStatus
Reason = runner.BlockReason
ExitCode = runner.ExitCode


def test_a_record_is_retained_through_one_spx_command_that_reads_the_composed_draft_on_stdin() -> (
    None
):
    observed = retain_record()

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.OPERATION] == Operation.RETAIN_RECORD
    assert observed.result[Result.STATUS] == Status.OK
    assert observed.result[Result.ISSUE] == RECORD_ISSUE
    (create,) = observed.calls_of(runner.SPX_EXECUTABLE)
    assert create.argv == runner.DRAFT_CREATE_COMMAND
    assert create.cwd.resolve() == observed.root.resolve()
    assert create.stdin is not None
    assert observed.retained_drafts == {observed.result[Result.PATH]: create.stdin}
    assert (
        observed.result[Result.SHA256]
        == hashlib.sha256(create.stdin.encode(runner.TEXT_ENCODING)).hexdigest()
    )


def test_the_retained_draft_carries_the_title_body_and_field_values_the_store_holds() -> (
    None
):
    record = stored_record()

    observed = retain_record()

    (create,) = observed.calls_of(runner.SPX_EXECUTABLE)
    assert create.stdin is not None
    front_matter, _, body = create.stdin.partition(record.body.rstrip())
    assert body.strip() == ""
    assert record.title in front_matter
    for value in record.field_values.values():
        assert str(value) in front_matter
    for key in (Result.MATURITY, Result.LIFECYCLE, Result.BASE):
        assert observed.result[key] == record.field_values[runner.FIELD_HOMES[key]]


def test_a_draft_store_that_retains_other_content_blocks_as_retained_input_mismatch() -> (
    None
):
    observed = retain_record(draft_store=DraftStoreCondition.ALTERING)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.OPERATION] == Operation.RETAIN_RECORD
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.RETAINED_INPUT_MISMATCH
    assert observed.result[Result.RETAINED_SHA256] != observed.result[Result.SHA256]
    assert Result.PATH not in observed.result


def test_a_failed_spx_command_blocks_as_command_failed_with_its_diagnostic() -> None:
    failure = recorded_spx_failure()

    observed = retain_record(draft_store=DraftStoreCondition.FAILING)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.COMMAND_FAILED
    assert observed.result[Result.EXIT_CODE] == failure.exit_code
    assert observed.result[Result.STDERR] == failure.stderr
    assert str(observed.result[Result.COMMAND]).startswith(runner.SPX_EXECUTABLE)
    assert Result.PATH not in observed.result
    assert observed.retained_drafts == {}


def test_a_failed_store_command_blocks_as_command_failed_before_any_draft_is_retained() -> (
    None
):
    failure = recorded_failure()

    observed = retain_record(store=StoreCondition.FAILING)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.COMMAND_FAILED
    assert observed.result[Result.EXIT_CODE] == failure.exit_code
    assert observed.result[Result.STDERR] == failure.stderr
    assert str(observed.result[Result.COMMAND]).startswith(runner.GH_EXECUTABLE)
    assert observed.calls_of(runner.SPX_EXECUTABLE) == ()
    assert observed.retained_drafts == {}


def test_a_store_command_that_cannot_start_blocks_as_command_failed() -> None:
    observed = retain_record(store=StoreCondition.UNRUNNABLE)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.REASON] == Reason.COMMAND_FAILED
    assert str(observed.result[Result.COMMAND]).startswith(runner.GH_EXECUTABLE)
    assert observed.retained_drafts == {}


def test_an_spx_command_that_cannot_start_blocks_as_command_failed() -> None:
    observed = retain_record(draft_store=DraftStoreCondition.UNRUNNABLE)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.REASON] == Reason.COMMAND_FAILED
    assert str(observed.result[Result.COMMAND]).startswith(runner.SPX_EXECUTABLE)
    assert Result.PATH not in observed.result
    assert observed.retained_drafts == {}
