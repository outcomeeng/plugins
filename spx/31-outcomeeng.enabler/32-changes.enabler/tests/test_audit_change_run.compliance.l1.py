"""Compliance evidence: an audit-change run writes no file.

Every request passes to the shipped runner on stdin and every result returns on
stdout; the SPX run journal is the only store the audit leaves behind. The
violating inputs are the conditions that made auditors write working files: a
rendered projection far larger than a result, two audits started at once from
one worktree, and a failure part-way through a run.

Each invocation is observed for every file the runner process writes wherever
the path lies — a fixed temporary path, the home directory, or the SPX store
included — and for every process it starts, alongside snapshots of the
repository, the SPX store, and the runner's temporary and home directories.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import PurePosixPath

import pytest

from outcomeeng_testing.harnesses.audit_change_run import (
    CAPTURED_CHANGE_RECORD,
    CHANGE_TEMPLATE,
    WINDOWS_1252_CHANGE_RECORD,
    AuditPayloads,
    AuditWorkspace,
    RunnerCall,
    audit_payloads,
    audit_workspace,
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
            assert run_fields[SpxField.RUN_TOKEN] == calls[3].result[Result.RUN_TOKEN]
        assert (
            audits[0][3].result[Result.RUN_TOKEN]
            != audits[1][3].result[Result.RUN_TOKEN]
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
        changes = workspace.changes_since(before)

        assert reconciled.exit_code == ExitCode.BLOCKED
        assert reconciled.result[Result.REASON] == Reason.CANDIDATE_CHANGED
        assert reconciled.result[Result.RUN_TOKEN] == started.result[Result.RUN_TOKEN]
        assert reconciled.runner_writes == ()
        assert _started_executables([reconciled]) <= PERMITTED_EXECUTABLES
        assert changes.in_repository_outside_store == ()
        assert changes.in_runner_temporary_directory == ()
        assert changes.in_runner_home_directory == ()


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
        assert changes.in_spx_store != ()
        assert started.runner_writes == ()
        assert _started_executables([started]) <= PERMITTED_EXECUTABLES
        assert changes.in_repository_outside_store == (relative,)
        assert changes.in_runner_temporary_directory == ()
        assert changes.in_runner_home_directory == ()


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
        payload = {SpxField.UNIT_ID: relative}

        rejected = workspace.invoke(
            {
                Field.OPERATION: Operation.ADD_SCOPE,
                Field.PATH: relative,
                Field.RUN_TOKEN: started.result[Result.RUN_TOKEN],
                Field.PAYLOAD: payload,
            }
        )
        changes = workspace.changes_since(before)

        assert rejected.exit_code == ExitCode.BLOCKED
        assert rejected.result[Result.REASON] == Reason.COMMAND_FAILED
        assert rejected.result[Result.RUN_TOKEN] == started.result[Result.RUN_TOKEN]
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


@dataclass(frozen=True)
class _OpenRun:
    """A started run over the captured record, and payloads a request can carry."""

    workspace: AuditWorkspace
    relative: str
    run_token: str
    payloads: AuditPayloads


def _read_request(path: str) -> str:
    return json.dumps({Field.OPERATION: Operation.READ_CANDIDATE, Field.PATH: path})


def _finding_request(run: _OpenRun, ordinal: object, rule: object) -> str:
    finding = run.payloads.findings[0]
    return json.dumps(
        {
            Field.OPERATION: Operation.ADD_FINDING,
            Field.PATH: run.relative,
            Field.RUN_TOKEN: run.run_token,
            Field.ORDINAL: ordinal,
            Field.PAYLOAD: {**finding, SpxField.RULE: rule},
        }
    )


# The refusals the runner contract in the audit-change SKILL.md declares, one
# request per declared refusal, each paired with the reason the contract names.
_DECLARED_REFUSALS: dict[str, tuple[Callable[[_OpenRun], str], object]] = {
    "truncated-json": (
        lambda run: _read_request(run.relative)[:-1],
        Reason.INVALID_REQUEST,
    ),
    "json-array": (
        lambda run: f"[{_read_request(run.relative)}]",
        Reason.INVALID_REQUEST,
    ),
    "unlisted-operation": (
        lambda run: json.dumps(
            {
                Field.OPERATION: Operation.READ_CANDIDATE.upper(),
                Field.PATH: run.relative,
            }
        ),
        Reason.INVALID_REQUEST,
    ),
    "missing-field": (
        lambda run: json.dumps({Field.OPERATION: Operation.READ_CANDIDATE}),
        Reason.INVALID_REQUEST,
    ),
    "extra-field": (
        lambda run: json.dumps(
            {
                Field.OPERATION: Operation.READ_CANDIDATE,
                Field.PATH: run.relative,
                Field.RUN_TOKEN: run.run_token,
            }
        ),
        Reason.INVALID_REQUEST,
    ),
    "ordinal-above-maximum": (
        lambda run: _finding_request(
            run,
            runner.MAX_FINDING_ORDINAL + 1,
            run.payloads.findings[0][SpxField.RULE],
        ),
        Reason.INVALID_REQUEST,
    ),
    "rule-not-a-rule-id": (
        lambda run: _finding_request(
            run, 1, str(run.payloads.findings[0][SpxField.RULE]).upper()
        ),
        Reason.INVALID_REQUEST,
    ),
    "payload-without-unit-id": (
        lambda run: json.dumps(
            {
                Field.OPERATION: Operation.ADD_SCOPE,
                Field.PATH: run.relative,
                Field.RUN_TOKEN: run.run_token,
                Field.PAYLOAD: {
                    key: value
                    for key, value in run.payloads.scopes[0].items()
                    if key != SpxField.UNIT_ID
                },
            }
        ),
        Reason.INVALID_REQUEST,
    ),
    "unlisted-terminal-status": (
        lambda run: json.dumps(
            {
                Field.OPERATION: Operation.FINISH,
                Field.PATH: run.relative,
                Field.RUN_TOKEN: run.run_token,
                Field.TERMINAL_STATUS: Terminal.APPROVED.upper(),
            }
        ),
        Reason.INVALID_REQUEST,
    ),
    "absolute-path": (
        lambda run: _read_request(str(run.workspace.root / run.relative)),
        Reason.PATH_REJECTED,
    ),
    "parent-traversing-path": (
        lambda run: _read_request(
            str(PurePosixPath(run.relative).parent / ".." / run.relative)
        ),
        Reason.PATH_REJECTED,
    ),
    "unnormalized-path": (
        lambda run: _read_request(f"./{run.relative}"),
        Reason.PATH_REJECTED,
    ),
    "candidate-linked-outside-the-repository": (
        lambda run: _read_request(run.workspace.place_link_outside(CHANGE_TEMPLATE)),
        Reason.PATH_REJECTED,
    ),
    "windows-1252-candidate": (
        lambda run: _read_request(run.workspace.place(WINDOWS_1252_CHANGE_RECORD)),
        Reason.PATH_REJECTED,
    ),
    "absent-candidate": (
        lambda run: _read_request(run.workspace.path_for(CHANGE_TEMPLATE)),
        Reason.CANDIDATE_MISSING,
    ),
}


@pytest.mark.parametrize(
    ("build_request", "reason"),
    list(_DECLARED_REFUSALS.values()),
    ids=list(_DECLARED_REFUSALS),
)
def test_an_invalid_request_part_way_through_a_run_blocks_on_stdout_without_a_file(
    build_request: Callable[[_OpenRun], str], reason: object
) -> None:
    with audit_workspace() as workspace:
        relative = workspace.place(CAPTURED_CHANGE_RECORD)
        read = workspace.invoke(
            {Field.OPERATION: Operation.READ_CANDIDATE, Field.PATH: relative}
        )
        version = workspace.invoke({Field.OPERATION: Operation.TOOL_VERSION})
        started = workspace.invoke(
            {
                Field.OPERATION: Operation.START,
                Field.PATH: relative,
                Field.CANDIDATE_SHA256: read.result[Result.SHA256],
            }
        )
        run = _OpenRun(
            workspace=workspace,
            relative=relative,
            run_token=str(started.result[Result.RUN_TOKEN]),
            payloads=audit_payloads(
                subject=relative,
                content=str(read.result[Result.CONTENT]),
                tool_version=str(version.result[Result.TOOL_VERSION]),
            ),
        )
        request_text = build_request(run)
        before = workspace.snapshot()

        blocked = workspace.invoke_text(request_text)
        changes = workspace.changes_since(before)

        assert blocked.exit_code != ExitCode.OK
        assert len(blocked.stdout_lines) == 1
        assert blocked.stderr == ""
        assert blocked.result[Result.STATUS] == Status.BLOCKED
        assert blocked.result[Result.REASON] == reason
        assert blocked.result[Result.RUN_TOKEN] in {
            runner.NOT_STARTED,
            run.run_token,
        }
        assert blocked.runner_writes == ()
        assert runner.SPX_EXECUTABLE not in _started_executables([blocked])
        assert _started_executables([blocked]) <= PERMITTED_EXECUTABLES
        assert changes.in_spx_store == ()
        assert changes.in_repository_outside_store == ()
        assert changes.in_runner_temporary_directory == ()
        assert changes.in_runner_home_directory == ()
