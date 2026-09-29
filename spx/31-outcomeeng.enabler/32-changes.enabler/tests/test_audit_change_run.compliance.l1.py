"""Compliance evidence: an audit-change run writes no file.

Every request passes to the shipped runner on stdin and every result returns on
stdout; the SPX run journal is the only store the audit leaves behind. The
violating inputs are the conditions that made auditors write working files: a
rendered projection far larger than a result, two audits started at once from
one worktree, and a failure part-way through a run — a candidate that changes,
a payload SPX rejects, a request the runner refuses, and a candidate it cannot
take.

Each subprocess invocation is observed for every file the runner process
writes wherever the path lies — a fixed temporary path, the home directory, or
the SPX store included — and for every process it starts, alongside snapshots
of the repository, the SPX store, and the runner's temporary and home
directories. Generated requests enter the runner's entry point in the test
process under the same audit-hook observation.
"""

from __future__ import annotations

import json
from collections.abc import Mapping

import pytest

from outcomeeng_testing.harnesses.audit_change_run import (
    CAPTURED_CHANGE_RECORD,
    CHANGE_TEMPLATE,
    AuditWorkspace,
    CandidateCondition,
    EntryPointCall,
    RunnerCall,
    audit_payloads,
    audit_workspace,
    exercise_malformed_request_objects,
    exercise_unparseable_request_texts,
    json_strings,
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
SpxField = runner.SpxField
PERMITTED_EXECUTABLES = frozenset({runner.SPX_EXECUTABLE, runner.GIT_EXECUTABLE})


def _complete_audit(workspace: AuditWorkspace, relative: str) -> list[RunnerCall]:
    """Drive every runner operation of one rejected audit over ``relative``.

    The first two calls read the candidate and start the run.
    """
    opened = workspace.start_run(relative)
    run_token = opened.run_token
    resolved = workspace.invoke(
        {Field.OPERATION: Operation.RESOLVE_REFERENCE, Field.PATH: relative}
    )
    versioned = workspace.invoke({Field.OPERATION: Operation.TOOL_VERSION})
    calls = [opened.read, opened.started, resolved, versioned]
    payloads = audit_payloads(
        subject=relative,
        content=str(opened.read.result[Result.CONTENT]),
        tool_version=str(versioned.result[Result.TOOL_VERSION]),
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
    for ordinal, finding in enumerate(
        payloads.findings, start=runner.MIN_FINDING_ORDINAL
    ):
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


def _started_executables(calls: list[RunnerCall]) -> set[str]:
    return {command[0] for call in calls for command in call.spawned_commands}


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
        assert [call.runner_writes for call in calls] == [()] * len(calls)
        assert _started_executables(calls) <= PERMITTED_EXECUTABLES
        assert changes.in_repository_outside_store == ()
        assert changes.in_runner_temporary_directory == ()
        assert changes.in_runner_home_directory == ()

        appended = [
            call
            for call in calls
            if call.request[Field.OPERATION]
            in {Operation.ADD_SCOPE, Operation.ADD_FINDING}
        ]
        assert [
            call.request[Field.PAYLOAD] in call.json_object_arguments
            for call in appended
        ] == [False] * len(appended)

        submitted = [
            call.request[Field.PAYLOAD]
            for call in calls
            if call.request[Field.OPERATION] == Operation.ADD_FINDING
        ]
        finished = calls[-1].result
        run_fields = finished[Result.RUN]
        projection = workspace.render(str(finished[Result.RENDER_COMMAND]))
        assert finished[Result.FINDINGS] == submitted
        assert isinstance(run_fields, dict)
        assert run_fields
        assert {field: projection[field] for field in run_fields} == run_fields
        assert workspace.content(relative) in json_strings(projection)
        assert workspace.content(relative) not in json_strings(run_fields)


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
            assert [call.runner_writes for call in calls] == [()] * len(calls)
            assert _started_executables(calls) <= PERMITTED_EXECUTABLES
            assert calls[0].result[Result.CONTENT] == workspace.content(relative)
            run_fields = calls[-1].result[Result.RUN]
            assert isinstance(run_fields, dict)
            assert run_fields[SpxField.RUN_TOKEN] == calls[1].result[Result.RUN_TOKEN]
        assert (
            audits[0][1].result[Result.RUN_TOKEN]
            != audits[1][1].result[Result.RUN_TOKEN]
        )
        assert changes.in_repository_outside_store == ()
        assert changes.in_runner_temporary_directory == ()
        assert changes.in_runner_home_directory == ()


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
        changes = workspace.changes_since(before)

        assert started.exit_code == ExitCode.BLOCKED
        assert started.result[Result.REASON] == Reason.CANDIDATE_CHANGED
        assert started.result[Result.RUN_TOKEN] == runner.NOT_STARTED
        assert started.runner_writes == ()
        assert _started_executables([started]) <= PERMITTED_EXECUTABLES
        assert changes.in_spx_store == ()
        assert changes.in_repository_outside_store == ()
        assert changes.in_runner_temporary_directory == ()
        assert changes.in_runner_home_directory == ()


def test_a_candidate_edited_during_the_run_blocks_reconciliation_without_a_file() -> (
    None
):
    with audit_workspace() as workspace:
        relative = workspace.place(CAPTURED_CHANGE_RECORD)
        opened = workspace.start_run(relative)
        workspace.edit(relative)
        before = workspace.snapshot()

        reconciled = workspace.invoke(
            {
                Field.OPERATION: Operation.RECONCILE,
                Field.PATH: relative,
                Field.RUN_TOKEN: opened.run_token,
            }
        )
        changes = workspace.changes_since(before)

        assert reconciled.exit_code == ExitCode.BLOCKED
        assert reconciled.result[Result.REASON] == Reason.CANDIDATE_CHANGED
        assert reconciled.result[Result.RUN_TOKEN] == opened.run_token
        assert reconciled.runner_writes == ()
        assert _started_executables([reconciled]) <= PERMITTED_EXECUTABLES
        assert changes.in_repository_outside_store == ()
        assert changes.in_runner_temporary_directory == ()
        assert changes.in_runner_home_directory == ()


def test_a_payload_spx_rejects_blocks_with_its_command_diagnostic_and_no_file() -> None:
    with audit_workspace() as workspace:
        relative = workspace.place(CAPTURED_CHANGE_RECORD)
        opened = workspace.start_run(relative)
        before = workspace.snapshot()
        payload = {SpxField.UNIT_ID: relative}

        rejected = workspace.invoke(
            {
                Field.OPERATION: Operation.ADD_SCOPE,
                Field.PATH: relative,
                Field.RUN_TOKEN: opened.run_token,
                Field.PAYLOAD: payload,
            }
        )
        changes = workspace.changes_since(before)

        assert rejected.exit_code == ExitCode.BLOCKED
        assert rejected.result[Result.REASON] == Reason.COMMAND_FAILED
        assert rejected.result[Result.RUN_TOKEN] == opened.run_token
        assert rejected.result[Result.PAYLOAD_KEY] == relative
        assert rejected.result[Result.EXIT_CODE] != 0
        assert rejected.result[Result.STDERR]
        assert runner.SPX_EXECUTABLE in _started_executables([rejected])
        assert _started_executables([rejected]) <= PERMITTED_EXECUTABLES
        assert payload not in rejected.json_object_arguments
        assert rejected.runner_writes == ()
        assert changes.in_repository_outside_store == ()
        assert changes.in_runner_temporary_directory == ()
        assert changes.in_runner_home_directory == ()


def test_a_generated_refused_request_object_blocks_on_stdout_without_a_file() -> None:
    def assert_blocked_without_a_file(
        request: Mapping[str, object], call: EntryPointCall
    ) -> None:
        try:
            accepted = runner.validate_request(request)
        except runner.Blocked:
            accepted = None
        assert accepted is None
        # The observation covers the runner's own process; a started process
        # would write outside it.
        assert call.spawned_commands == ()
        assert call.runner_writes == ()
        assert len(call.stdout_lines) == 1
        assert json.loads(call.stdout_lines[0])[Result.STATUS] == Status.BLOCKED

    exercise_malformed_request_objects(assert_blocked_without_a_file)


def test_a_generated_request_text_the_runner_cannot_parse_as_one_json_object_blocks_without_a_file() -> (
    None
):
    def assert_blocked_without_a_file(call: EntryPointCall) -> None:
        assert call.spawned_commands == ()
        assert call.runner_writes == ()
        assert len(call.stdout_lines) == 1
        assert json.loads(call.stdout_lines[0])[Result.STATUS] == Status.BLOCKED

    exercise_unparseable_request_texts(assert_blocked_without_a_file)


def test_a_request_that_is_not_utf8_text_blocks_on_stdout_without_a_file() -> None:
    with audit_workspace() as workspace:
        relative = workspace.place(CAPTURED_CHANGE_RECORD)
        before = workspace.snapshot()

        blocked = workspace.invoke_utf16(
            {Field.OPERATION: Operation.READ_CANDIDATE, Field.PATH: relative}
        )
        changes = workspace.changes_since(before)

        assert len(blocked.stdout_lines) == 1
        assert blocked.result[Result.STATUS] == Status.BLOCKED
        assert blocked.runner_writes == ()
        assert _started_executables([blocked]) <= PERMITTED_EXECUTABLES
        assert changes.in_repository_outside_store == ()
        assert changes.in_runner_temporary_directory == ()
        assert changes.in_runner_home_directory == ()


@pytest.mark.parametrize("condition", tuple(CandidateCondition))
def test_a_candidate_the_runner_cannot_take_blocks_on_stdout_without_a_file(
    condition: CandidateCondition,
) -> None:
    with audit_workspace() as workspace:
        relative = workspace.place_in_condition(condition, CAPTURED_CHANGE_RECORD)
        before = workspace.snapshot()

        blocked = workspace.invoke(
            {Field.OPERATION: Operation.READ_CANDIDATE, Field.PATH: relative}
        )
        changes = workspace.changes_since(before)

        assert len(blocked.stdout_lines) == 1
        assert blocked.result[Result.STATUS] == Status.BLOCKED
        assert blocked.runner_writes == ()
        assert _started_executables([blocked]) <= PERMITTED_EXECUTABLES
        assert changes.in_repository_outside_store == ()
        assert changes.in_runner_temporary_directory == ()
        assert changes.in_runner_home_directory == ()


@pytest.mark.parametrize(
    "operation",
    tuple(
        operation
        for operation in Operation
        if Field.RUN_TOKEN in runner.REQUIRED_FIELDS[operation]
    ),
)
def test_a_refused_request_naming_a_started_run_blocks_with_its_run_token_and_no_file(
    operation: object,
) -> None:
    with audit_workspace() as workspace:
        relative = workspace.place(CAPTURED_CHANGE_RECORD)
        run_token = workspace.start_run(relative).run_token
        before = workspace.snapshot()

        # Every request field, so the request carries fields its operation
        # does not take, with the operation, the candidate, and the run named.
        blocked = workspace.invoke(
            {
                **dict.fromkeys(Field),
                Field.OPERATION: operation,
                Field.PATH: relative,
                Field.RUN_TOKEN: run_token,
            }
        )
        changes = workspace.changes_since(before)

        assert len(blocked.stdout_lines) == 1
        assert blocked.result[Result.STATUS] == Status.BLOCKED
        assert blocked.result[Result.OPERATION] == operation
        assert blocked.result[Result.RUN_TOKEN] == run_token
        assert blocked.runner_writes == ()
        assert _started_executables([blocked]) <= PERMITTED_EXECUTABLES
        assert changes.in_repository_outside_store == ()
        assert changes.in_runner_temporary_directory == ()
        assert changes.in_runner_home_directory == ()
