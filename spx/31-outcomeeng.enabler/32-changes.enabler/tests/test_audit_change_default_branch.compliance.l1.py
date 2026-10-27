"""Compliance evidence: resolve-reference blocks when Git cannot answer the default-branch question.

The rule is the spec assertion for the ``audit-change`` runner's
``resolve-reference`` operation: when the read of origin's default branch prints
no default branch, the result is blocked with ``unreadable-output``; when that
read exits nonzero or the lookup of the path cannot be executed, the result is
blocked with ``command-failed``; every block carries no ``defaultBranch`` and a
failed default-branch read leads to no path lookup. The violating cases are a
real repository whose remote holds no ``HEAD`` reference, a default-branch read
that succeeds with no output, and a path lookup that cannot start ``git``; the
last two come from a controlled process boundary under the failure-simulation
exception, and every other command runs for real. A real repository with a
default-branch reference returns a resolution, which shows the block is not a
false positive.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.audit_change_default_branch import (
    LOOK_UP_PATH_SUBCOMMAND,
    PathCondition,
    default_branch_situation,
    resolve_reference,
    resolve_reference_with_empty_default_branch,
    resolve_reference_with_unstartable_path_lookup,
)
from outcomeeng_testing.harnesses.audit_change_run import load_runner

runner = load_runner()
Result = runner.ResultField
Status = runner.ResultStatus
Reason = runner.BlockReason
ExitCode = runner.ExitCode


def test_a_remote_without_a_head_reference_blocks_as_command_failed_before_any_path_lookup() -> (
    None
):
    with default_branch_situation(
        PathCondition.COMMITTED_TO_ORIGIN_DEFAULT, origin_head=False
    ) as situation:
        observed = resolve_reference(situation)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.COMMAND_FAILED
    assert observed.result[Result.EXIT_CODE] != 0
    assert str(observed.result[Result.COMMAND]).startswith(runner.GIT_EXECUTABLE)
    assert Result.DEFAULT_BRANCH not in observed.result
    assert not any(LOOK_UP_PATH_SUBCOMMAND in c for c in observed.commands)


def test_a_default_branch_read_that_prints_nothing_blocks_as_unreadable_output() -> (
    None
):
    with default_branch_situation(
        PathCondition.COMMITTED_TO_ORIGIN_DEFAULT
    ) as situation:
        observed = resolve_reference_with_empty_default_branch(situation)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.UNREADABLE_OUTPUT
    assert Result.DEFAULT_BRANCH not in observed.result
    assert not any(LOOK_UP_PATH_SUBCOMMAND in c for c in observed.commands)


def test_a_path_lookup_that_cannot_start_git_blocks_as_command_failed() -> None:
    with default_branch_situation(
        PathCondition.COMMITTED_TO_ORIGIN_DEFAULT
    ) as situation:
        observed = resolve_reference_with_unstartable_path_lookup(situation)

    assert observed.exit_code == ExitCode.BLOCKED
    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert observed.result[Result.REASON] == Reason.COMMAND_FAILED
    assert str(observed.result[Result.COMMAND]).startswith(runner.GIT_EXECUTABLE)
    assert Result.DEFAULT_BRANCH not in observed.result


def test_a_repository_with_a_head_reference_returns_a_resolution_instead_of_blocking() -> (
    None
):
    with default_branch_situation(
        PathCondition.COMMITTED_TO_ORIGIN_DEFAULT
    ) as situation:
        observed = resolve_reference(situation)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.STATUS] == Status.OK
    assert Result.DEFAULT_BRANCH in observed.result
