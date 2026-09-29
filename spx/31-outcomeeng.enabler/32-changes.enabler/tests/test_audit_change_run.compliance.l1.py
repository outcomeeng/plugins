"""Compliance evidence: an audit-change run writes no file.

Every request passes to the shipped runner on stdin and every result returns on
stdout; the SPX run journal is the only store the audit leaves behind. The
violating inputs are the conditions that made auditors write working files: a
rendered projection far larger than a result, two audits started at once from
one worktree, and a failure part-way through a run.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.audit_change_run import (
    CAPTURED_CHANGE_RECORD,
    CHANGE_TEMPLATE,
    AuditWorkspace,
    RunnerCall,
    audit_payloads,
    audit_workspace,
    load_runner,
    run_in_parallel,
)

runner = load_runner()
Operation = runner.Operation
Field = runner.RequestField
Result = runner.ResultField
Status = runner.ResultStatus
Reason = runner.BlockReason
Terminal = runner.TerminalStatus
ExitCode = runner.ExitCode


def _complete_audit(workspace: AuditWorkspace, relative: str) -> list[RunnerCall]:
    """Drive every runner operation of one rejected audit over ``relative``."""
    calls = [
        workspace.invoke(
            {Field.OPERATION: Operation.READ_CANDIDATE, Field.PATH: relative}
        )
    ]
    calls.append(
        workspace.invoke(
            {Field.OPERATION: Operation.RESOLVE_REFERENCE, Field.PATH: relative}
        )
    )
    calls.append(workspace.invoke({Field.OPERATION: Operation.TOOL_VERSION}))
    candidate_sha256 = calls[0].result[Result.SHA256]
    calls.append(
        workspace.invoke(
            {
                Field.OPERATION: Operation.START,
                Field.PATH: relative,
                Field.CANDIDATE_SHA256: candidate_sha256,
            }
        )
    )
    run_token = calls[-1].result[Result.RUN_TOKEN]
    payloads = audit_payloads(
        subject=relative,
        content=str(calls[0].result[Result.CONTENT]),
        tool_version=str(calls[2].result[Result.TOOL_VERSION]),
    )
    for scope in payloads.scopes:
        calls.append(
            workspace.invoke(
                {
                    Field.OPERATION: Operation.ADD_SCOPE,
                    Field.PATH: relative,
                    Field.RUN_TOKEN: run_token,
                    Field.PAYLOAD: scope,
                }
            )
        )
    for ordinal, finding in enumerate(payloads.findings, start=1):
        calls.append(
            workspace.invoke(
                {
                    Field.OPERATION: Operation.ADD_FINDING,
                    Field.PATH: relative,
                    Field.RUN_TOKEN: run_token,
                    Field.ORDINAL: ordinal,
                    Field.PAYLOAD: finding,
                }
            )
        )
    calls.append(
        workspace.invoke(
            {
                Field.OPERATION: Operation.RECONCILE,
                Field.PATH: relative,
                Field.RUN_TOKEN: run_token,
            }
        )
    )
    calls.append(
        workspace.invoke(
            {
                Field.OPERATION: Operation.FINISH,
                Field.PATH: relative,
                Field.RUN_TOKEN: run_token,
                Field.TERMINAL_STATUS: Terminal.REJECTED,
            }
        )
    )
    return calls


def test_a_complete_audit_writes_no_file_and_its_journal_reproduces_the_projection() -> (
    None
):
    with audit_workspace() as workspace:
        relative = workspace.place(CAPTURED_CHANGE_RECORD)
        before = workspace.snapshot()

        calls = _complete_audit(workspace, relative)
        changes = workspace.changes_since(before)

        assert [call.result[Result.STATUS] for call in calls] == [Status.OK] * len(
            calls
        ), [call.result for call in calls if call.result[Result.STATUS] != Status.OK]
        assert {len(call.stdout_lines) for call in calls} == {1}
        assert changes.in_repository_outside_store == ()
        assert changes.in_runner_temporary_directory == ()

        submitted = [
            call.request[Field.PAYLOAD]
            for call in calls
            if call.request[Field.OPERATION] == Operation.ADD_FINDING
        ]
        finished = calls[-1].result
        projection = workspace.render(str(finished[Result.RENDER_COMMAND]))
        assert finished[Result.FINDINGS] == submitted
        assert {field: projection[field] for field in finished[Result.RUN]} == finished[
            Result.RUN
        ]
        assert set(projection) - set(finished[Result.RUN]) == set(
            runner.EVIDENCE_FIELDS
        )


def test_two_audits_started_at_once_from_one_worktree_each_read_only_their_own_candidate() -> (
    None
):
    with audit_workspace() as workspace:
        candidates = [
            workspace.place(CAPTURED_CHANGE_RECORD),
            workspace.place(CHANGE_TEMPLATE),
        ]
        before = workspace.snapshot()

        audits = run_in_parallel(
            lambda relative: _complete_audit(workspace, relative), candidates
        )
        changes = workspace.changes_since(before)

        for relative, calls in zip(candidates, audits, strict=True):
            assert [call.result[Result.STATUS] for call in calls] == [Status.OK] * len(
                calls
            )
            assert calls[0].result[Result.CONTENT] == workspace.content(relative)
            assert (
                calls[-1].result[Result.RUN][runner.SpxField.RUN_TOKEN]
                == calls[3].result[Result.RUN_TOKEN]
            )
        assert (
            audits[0][3].result[Result.RUN_TOKEN]
            != audits[1][3].result[Result.RUN_TOKEN]
        )
        assert changes.in_repository_outside_store == ()
        assert changes.in_runner_temporary_directory == ()


def test_a_candidate_edited_before_the_run_starts_blocks_without_a_run_or_a_file() -> (
    None
):
    with audit_workspace() as workspace:
        relative = workspace.place(CAPTURED_CHANGE_RECORD)
        read = workspace.invoke(
            {Field.OPERATION: Operation.READ_CANDIDATE, Field.PATH: relative}
        )
        workspace.edit(relative)
        before = workspace.snapshot()

        started = workspace.invoke(
            {
                Field.OPERATION: Operation.START,
                Field.PATH: relative,
                Field.CANDIDATE_SHA256: read.result[Result.SHA256],
            }
        )

        assert started.exit_code == ExitCode.BLOCKED
        assert started.result[Result.REASON] == Reason.CANDIDATE_CHANGED
        assert started.result[Result.RUN_TOKEN] == runner.NOT_STARTED
        assert workspace.changes_since(before).in_repository_outside_store == ()
        assert workspace.changes_since(before).in_runner_temporary_directory == ()


def test_a_candidate_edited_during_the_run_blocks_reconciliation_without_a_file() -> (
    None
):
    with audit_workspace() as workspace:
        relative = workspace.place(CAPTURED_CHANGE_RECORD)
        read = workspace.invoke(
            {Field.OPERATION: Operation.READ_CANDIDATE, Field.PATH: relative}
        )
        started = workspace.invoke(
            {
                Field.OPERATION: Operation.START,
                Field.PATH: relative,
                Field.CANDIDATE_SHA256: read.result[Result.SHA256],
            }
        )
        workspace.edit(relative)
        before = workspace.snapshot()

        reconciled = workspace.invoke(
            {
                Field.OPERATION: Operation.RECONCILE,
                Field.PATH: relative,
                Field.RUN_TOKEN: started.result[Result.RUN_TOKEN],
            }
        )

        assert reconciled.exit_code == ExitCode.BLOCKED
        assert reconciled.result[Result.REASON] == Reason.CANDIDATE_CHANGED
        assert reconciled.result[Result.RUN_TOKEN] == started.result[Result.RUN_TOKEN]
        assert workspace.changes_since(before).in_repository_outside_store == ()
        assert workspace.changes_since(before).in_runner_temporary_directory == ()


def test_a_retained_input_that_differs_from_the_candidate_read_blocks_without_a_file() -> (
    None
):
    # /test Stage 5 exception 3 (time and concurrency): the harness times an
    # edit between the runner's read and SPX's retention of the candidate.
    with audit_workspace() as workspace:
        relative = workspace.place(CAPTURED_CHANGE_RECORD)
        read = workspace.invoke(
            {Field.OPERATION: Operation.READ_CANDIDATE, Field.PATH: relative}
        )
        before = workspace.snapshot()

        started = workspace.invoke_racing_start(
            {
                Field.OPERATION: Operation.START,
                Field.PATH: relative,
                Field.CANDIDATE_SHA256: read.result[Result.SHA256],
            }
        )
        changes = workspace.changes_since(before)

        assert started.exit_code == ExitCode.BLOCKED
        assert started.result[Result.REASON] == Reason.RETAINED_INPUT_MISMATCH
        assert started.result[Result.RUN_TOKEN] != runner.NOT_STARTED
        assert changes.in_repository_outside_store == (relative,)
        assert changes.in_runner_temporary_directory == ()


def test_a_payload_spx_rejects_blocks_with_its_command_diagnostic_and_no_file() -> None:
    with audit_workspace() as workspace:
        relative = workspace.place(CAPTURED_CHANGE_RECORD)
        read = workspace.invoke(
            {Field.OPERATION: Operation.READ_CANDIDATE, Field.PATH: relative}
        )
        started = workspace.invoke(
            {
                Field.OPERATION: Operation.START,
                Field.PATH: relative,
                Field.CANDIDATE_SHA256: read.result[Result.SHA256],
            }
        )
        before = workspace.snapshot()

        rejected = workspace.invoke(
            {
                Field.OPERATION: Operation.ADD_SCOPE,
                Field.PATH: relative,
                Field.RUN_TOKEN: started.result[Result.RUN_TOKEN],
                Field.PAYLOAD: {runner.SpxField.UNIT_ID: relative},
            }
        )

        assert rejected.exit_code == ExitCode.BLOCKED
        assert rejected.result[Result.REASON] == Reason.COMMAND_FAILED
        assert rejected.result[Result.RUN_TOKEN] == started.result[Result.RUN_TOKEN]
        assert rejected.result[Result.PAYLOAD_SOURCE] == runner.PAYLOAD_FROM_STDIN
        assert rejected.result[Result.PAYLOAD_KEY] == relative
        assert rejected.result[Result.EXIT_CODE] != 0
        assert rejected.result[Result.STDERR]
        assert workspace.changes_since(before).in_repository_outside_store == ()
        assert workspace.changes_since(before).in_runner_temporary_directory == ()
