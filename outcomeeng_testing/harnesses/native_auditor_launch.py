"""Drive every native auditor-dispatch row at the process boundary.

The runner completes every installation and parent-session command it receives
and records each one, under the `/test` Stage 5 interaction-protocols and
failure-simulation exceptions: the evidence concerns the shape and environment
of the commands the producer issues and the state it materializes, which a real
dispatch would hide behind a model turn and a credentialed account. Saved-login
writes go to the credential runner the authentication case already owns. The
harness exposes observations only.
"""

from __future__ import annotations

import json
from collections.abc import Collection, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Final

from outcomeeng.distribution.installation import CLAUDE_EXECUTABLE, CODEX_HOME_ENV
from outcomeeng.distribution.native_auditor_dispatch import (
    AGENTS_DIRECTORY,
    BLOCKED_MARKER,
    FIXTURE_DIRECTORY,
    NativeAuditorDispatchObservation,
    native_auditor_rows,
)
from outcomeeng.validation.implementation_audit_contract import (
    EVENT_RUN_ID_FIELD,
    RUN_EVENTS_FIELD,
    RUN_TERMINAL_STATUS_FIELD,
    RUN_TOKEN_FIELD,
    AuditTerminalStatus,
)
from outcomeeng_testing.harnesses.discovery_auth import AUTH_FILENAME
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    NativeCall,
    NativeCredentialRunner,
    NativeFault,
)
from outcomeeng_testing.harnesses.installation import repository_root
from outcomeeng_testing.harnesses.native_auditor_dispatch import (
    run_native_auditor_dispatch,
)
from outcomeeng_testing.harnesses.native_profile_execution import (
    CLAUDE_CREDENTIAL_VARIABLES,
)
from outcomeeng_testing.harnesses.native_profile_failures import NativeFailureRunner
from outcomeeng_testing.harnesses.native_profile_launch import (
    RecordingRunner,
    RowLaunch,
    ambient_environment,
    launch_case,
    row_launches,
)


PLANTED_RUN_TOKEN = "2026-01-02_03-04-05-678-0123456789ab"
PLANTED_RUN_FILE_NAME = f"run-{PLANTED_RUN_TOKEN}.jsonl"
PLANTED_RUN_FILE = f"runs/{PLANTED_RUN_FILE_NAME}"
PLANTED_TERMINAL_STATUS = AuditTerminalStatus.APPROVED.value
PLANTED_PROJECTION: Final[Mapping[str, object]] = {
    RUN_TOKEN_FIELD: PLANTED_RUN_TOKEN,
    RUN_TERMINAL_STATUS_FIELD: PLANTED_TERMINAL_STATUS,
    RUN_EVENTS_FIELD: [{EVENT_RUN_ID_FIELD: PLANTED_RUN_FILE_NAME}],
}
PLANTED_PROJECTION_QUOTING_BLOCKED: Final[Mapping[str, object]] = {
    **PLANTED_PROJECTION,
    "summary": f"A finding quotes the word {BLOCKED_MARKER}.",
}


class LaunchReturn(Enum):
    """What the dispatched auditor returns to the parent session."""

    RUN_TOKEN = "run-token"
    FREE_FORM = "free-form"
    PROJECTION_QUOTING_BLOCKED = "projection-quoting-blocked"
    PROJECTION_ONLY = "projection-only"
    UNSTRUCTURED = "unstructured"
    BLOCKED = "blocked"


def _returned_message(returned: LaunchReturn) -> str:
    projection = json.dumps(PLANTED_PROJECTION)
    if returned is LaunchReturn.RUN_TOKEN:
        return (
            f"run token {PLANTED_RUN_TOKEN}\nrun file {PLANTED_RUN_FILE}\n{projection}"
        )
    if returned is LaunchReturn.FREE_FORM:
        return (
            f"The audit is sealed under token {PLANTED_RUN_TOKEN}. Its record is "
            f"{PLANTED_RUN_FILE}.\nThe rendered verdict follows.\n{projection}"
        )
    if returned is LaunchReturn.PROJECTION_QUOTING_BLOCKED:
        return f"Here is the verdict.\n{json.dumps(PLANTED_PROJECTION_QUOTING_BLOCKED)}"
    if returned is LaunchReturn.PROJECTION_ONLY:
        return f"Here is the verdict.\n```json\n{projection}\n```"
    if returned is LaunchReturn.UNSTRUCTURED:
        return f"The audit finished with token {PLANTED_RUN_TOKEN} and file {PLANTED_RUN_FILE}."
    return f"{BLOCKED_MARKER}: the auditor could not start the run"


def _machine_stream(argv: Sequence[str], message: str) -> str:
    """The parent session's machine stream carrying `message` as its last assistant text."""
    if argv[0] == CLAUDE_EXECUTABLE:
        event: dict[str, object] = {"type": "result", "result": message}
    else:
        event = {
            "type": "item.completed",
            "item": {"type": "agent_message", "text": message},
        }
    return json.dumps(event) + "\n"


@dataclass(frozen=True)
class DispatchCall:
    """One recorded command and the materialized state present when it ran."""

    argv: tuple[str, ...]
    home: Path
    environment: Mapping[str, str]
    state_files: Mapping[Path, bytes] = field(repr=False)
    """Bytes of every file under an `agents` or `fixture` directory of the row's state, keyed relative to it."""
    saved_login: bytes | None = field(default=None, repr=False)
    """Bytes the command's Codex home resolves its saved login to, when it holds one."""


def _saved_login(home: Path) -> bytes | None:
    login = home / AUTH_FILENAME
    return login.read_bytes() if login.is_file() else None


def _materialized_state(state_root: Path) -> dict[Path, bytes]:
    return {
        path.relative_to(state_root): path.read_bytes()
        for path in state_root.rglob("*")
        if path.is_file() and {AGENTS_DIRECTORY, FIXTURE_DIRECTORY} & set(path.parts)
    }


def _record_dispatch_call(
    argv: Sequence[str], env: Mapping[str, str], input_text: str | None
) -> DispatchCall:
    del input_text
    home = Path(env[CODEX_HOME_ENV])
    return DispatchCall(
        tuple(argv),
        home,
        dict(env),
        _materialized_state(home.parent),
        _saved_login(home),
    )


def auditor_launch_runner(
    credentials: NativeCredentialRunner,
    launch_exit_code: int,
    launches: frozenset[tuple[str, ...]],
    returned: LaunchReturn = LaunchReturn.RUN_TOKEN,
) -> RecordingRunner[DispatchCall]:
    """A recording runner that completes every command and fails the dispatch launch on request."""

    def complete(argv: Sequence[str]) -> tuple[int, str]:
        if any(set(launch) <= set(argv) for launch in launches):
            return launch_exit_code, _machine_stream(argv, _returned_message(returned))
        return 0, ""

    return RecordingRunner(credentials, _record_dispatch_call, complete)


@dataclass(frozen=True)
class DispatchLaunchObservation:
    rows: tuple[RowLaunch[NativeAuditorDispatchObservation, DispatchCall], ...]
    environment: Mapping[str, str]
    """The ambient environment the run received, every strippable name planted."""
    saved_login: bytes
    """Bytes of the selected Codex authentication's saved login."""


@dataclass(frozen=True)
class DispatchFailureObservation:
    rows: tuple[NativeAuditorDispatchObservation, ...]
    calls: tuple[NativeCall, ...]
    environment: Mapping[str, str]


@contextmanager
def native_auditor_launch(
    claude_credentials: Collection[str] = CLAUDE_CREDENTIAL_VARIABLES,
    launch_exit_code: int = 0,
    returned: LaunchReturn = LaunchReturn.RUN_TOKEN,
) -> Iterator[DispatchLaunchObservation]:
    """Run every row with `claude_credentials` planted beside every other strippable name."""
    with launch_case() as case:
        runner = auditor_launch_runner(
            case.credentials.runner,
            launch_exit_code,
            frozenset(
                row.launch_command for row in native_auditor_rows(repository_root())
            ),
            returned,
        )
        environment = ambient_environment(
            case.credentials.original_environment, claude_credentials=claude_credentials
        )
        rows = run_native_auditor_dispatch(
            case.artifact_root,
            checkout=repository_root(),
            environment=environment,
            runner=runner,
        )
        yield DispatchLaunchObservation(
            row_launches(rows, runner.calls),
            environment,
            case.credentials.initial.encode("utf-8"),
        )


@contextmanager
def native_auditor_failure(fault: NativeFault) -> Iterator[DispatchFailureObservation]:
    """Expose retained evidence after the production harness removes its state."""
    with launch_case() as case:
        runner = NativeFailureRunner(fault)
        environment = ambient_environment(
            case.credentials.original_environment,
            claude_credentials=CLAUDE_CREDENTIAL_VARIABLES,
        )
        rows = run_native_auditor_dispatch(
            case.artifact_root,
            checkout=repository_root(),
            environment=environment,
            runner=runner,
        )
        yield DispatchFailureObservation(rows, tuple(runner.calls), environment)
