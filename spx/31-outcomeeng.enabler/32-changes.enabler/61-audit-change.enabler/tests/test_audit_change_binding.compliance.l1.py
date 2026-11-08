"""Compliance evidence: an audit binds the record body and the Base it read.

The rule is the spec assertion that the runner binds each run to the SHA-256 of
the record body and to the Base it read, names both in its finish result, and
blocks a run whose body or Base differs at finish from the pair it read at
start. The violating cases are the publications that land during a run: a body
edit, and a new Base. A publication that writes only metadata keeps the audit,
so the title edit is the conforming case. The Change Store answers from a
replayed ``gh``.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.audit_change_run import (
    AuditWorkspace,
    RunnerCall,
    StartedRun,
    audit_workspace,
    load_runner,
)

runner = load_runner()
Operation = runner.Operation
Field = runner.RequestField
Result = runner.ResultField
Status = runner.ResultStatus
Reason = runner.BlockReason
Terminal = runner.TerminalStatus
ExitCode = runner.ExitCode
BASE_FIELD = runner.FIELD_NAMES[runner.MetadataKey.BASE]
#: A Base other than the one the captured record names.
OTHER_BASE = "a" * 40


def _finish(workspace: AuditWorkspace, identity: str, opened: StartedRun) -> RunnerCall:
    return workspace.invoke(
        {
            Field.OPERATION: Operation.FINISH,
            Field.ISSUE: identity,
            Field.ROOT: str(workspace.root),
            Field.RUN_TOKEN: opened.run_token,
            Field.TERMINAL_STATUS: Terminal.REJECTED,
        }
    )


def _reconcile(
    workspace: AuditWorkspace, identity: str, opened: StartedRun
) -> RunnerCall:
    return workspace.invoke(
        {
            Field.OPERATION: Operation.RECONCILE,
            Field.ISSUE: identity,
            Field.ROOT: str(workspace.root),
            Field.RUN_TOKEN: opened.run_token,
        }
    )


def test_the_finish_result_names_the_body_and_the_base_the_run_read_at_start() -> None:
    with audit_workspace() as workspace:
        identity = workspace.place_issue()
        opened = workspace.start_run(identity)

        finished = _finish(workspace, identity, opened)

        assert finished.result[Result.STATUS] == Status.OK
        assert opened.read.result[Result.BASE]
        assert (
            finished.result[Result.BODY_SHA256]
            == opened.read.result[Result.BODY_SHA256]
        )
        assert (
            finished.result[Result.BODY_SHA256]
            == opened.started.result[Result.BODY_SHA256]
        )
        assert finished.result[Result.BASE] == opened.read.result[Result.BASE]
        assert finished.result[Result.BASE] == opened.started.result[Result.BASE]


def test_a_body_published_after_the_run_started_blocks_reconcile_and_finish_naming_both_digests() -> (
    None
):
    with audit_workspace() as workspace:
        identity = workspace.place_issue()
        opened = workspace.start_run(identity)
        workspace.edit(identity)

        reconciled = _reconcile(workspace, identity, opened)
        finished = _finish(workspace, identity, opened)

        for call in (reconciled, finished):
            assert call.exit_code == ExitCode.BLOCKED
            assert call.result[Result.REASON] == Reason.RECORD_CHANGED
            assert call.result[Result.RUN_TOKEN] == opened.run_token
            assert (
                call.result[Result.RETAINED_SHA256]
                == opened.read.result[Result.BODY_SHA256]
            )
            assert (
                call.result[Result.LIVE_SHA256] != call.result[Result.RETAINED_SHA256]
            )
            assert call.runner_writes == ()


def test_a_base_published_after_the_run_started_blocks_finish_naming_both_bases() -> (
    None
):
    with audit_workspace() as workspace:
        identity = workspace.place_issue()
        opened = workspace.start_run(identity)
        workspace.set_field(identity, BASE_FIELD, OTHER_BASE)

        finished = _finish(workspace, identity, opened)

        assert finished.exit_code == ExitCode.BLOCKED
        assert finished.result[Result.REASON] == Reason.RECORD_CHANGED
        assert finished.result[Result.RETAINED_BASE] == opened.read.result[Result.BASE]
        assert finished.result[Result.LIVE_BASE] == OTHER_BASE
        assert finished.runner_writes == ()


def test_a_publication_that_writes_only_metadata_keeps_the_audit() -> None:
    with audit_workspace() as workspace:
        identity = workspace.place_issue()
        opened = workspace.start_run(identity)
        workspace.set_title(identity, "A title the publication wrote")

        reconciled = _reconcile(workspace, identity, opened)
        finished = _finish(workspace, identity, opened)

        assert reconciled.result[Result.STATUS] == Status.OK
        assert finished.result[Result.STATUS] == Status.OK
        assert (
            finished.result[Result.BODY_SHA256]
            == opened.read.result[Result.BODY_SHA256]
        )
        assert finished.result[Result.BASE] == opened.read.result[Result.BASE]


def test_a_start_over_a_base_other_than_the_stored_one_blocks_without_a_run() -> None:
    with audit_workspace() as workspace:
        identity = workspace.place_issue()
        read = workspace.invoke(
            {
                Field.OPERATION: Operation.READ_RECORD,
                Field.ISSUE: identity,
                Field.ROOT: str(workspace.root),
            }
        )

        started = workspace.invoke(
            {
                Field.OPERATION: Operation.START,
                Field.ISSUE: identity,
                Field.ROOT: str(workspace.root),
                Field.BODY_SHA256: read.result[Result.BODY_SHA256],
                Field.BASE: OTHER_BASE,
            }
        )

        assert started.exit_code == ExitCode.BLOCKED
        assert started.result[Result.REASON] == Reason.RECORD_CHANGED
        assert started.result[Result.RUN_TOKEN] == runner.NOT_STARTED
        assert started.result[Result.RETAINED_BASE] == OTHER_BASE
        assert started.result[Result.LIVE_BASE] == read.result[Result.BASE]
