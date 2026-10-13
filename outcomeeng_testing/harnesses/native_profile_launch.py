"""Drive every native-profile row through a completed launch at the process boundary.

The runner completes every installation and parent-session command it receives
and records each one, under the `/test` Stage 5 interaction-protocols
exception: the evidence concerns the shape and environment of the commands the
producer issues, which a real parent session would hide behind a model turn and
a credentialed account. Saved-login writes go to the credential runner the
authentication case already owns. The harness exposes observations only.
"""

from __future__ import annotations

import subprocess
import json
import os
from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.installation import CODEX_EXEC_SUBCOMMAND, CODEX_HOME_ENV
from outcomeeng.distribution.native_thread_evidence import (
    NATIVE_THREAD_STARTED,
    NativeParentEvent,
)
from outcomeeng.distribution.native_profile_execution import (
    NativeProfileExecutionObservation,
)
from outcomeeng_testing.harnesses.discovery_auth import (
    CODEX_LOGIN_SUBCOMMAND,
    CREDENTIAL_ENVIRONMENTS,
)
from outcomeeng_testing.harnesses.discovery_auth import AuthenticationMode
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    NativeCall,
    NativeCredentialRunner,
    authentication_case,
)
from outcomeeng_testing.harnesses.installation import repository_root
from outcomeeng_testing.harnesses.native_profile_execution import (
    CLAUDE_CREDENTIAL_VARIABLES,
    NATIVE_PROFILE_AMBIENT_ENVIRONMENT_VARIABLES,
    run_native_profile_execution,
)


def ambient_environment(
    original: Mapping[str, str], *, claude_credentials: Collection[str]
) -> dict[str, str]:
    """The selected authentication's environment with every strippable name also set.

    An operator's shell can carry any ambient override, the Claude Code session
    marker, the Codex credential variables, and the named Claude credentials at
    once, so each is planted with a fresh value; a name the selected
    authentication already carries keeps its value.
    """
    planted = {
        *NATIVE_PROFILE_AMBIENT_ENVIRONMENT_VARIABLES,
        *claude_credentials,
        *CREDENTIAL_ENVIRONMENTS,
    }
    return {
        **{name: uuid4().hex for name in planted},
        **original,
    }


def _silent(argv: Sequence[str]) -> str:
    """No command output: the runner's default for every completed command."""
    del argv
    return ""


@dataclass
class NativeLaunchRunner:
    """Complete and record every non-login native command; logins go to `credentials`.

    `stdout` supplies each completed command's output from its argv, so a
    caller can give the parent session the stream a real one would print.
    """

    credentials: NativeCredentialRunner
    stdout: Callable[[Sequence[str]], str] = _silent
    calls: list[NativeCall] = field(default_factory=list)

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        input_text: str | None,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        if CODEX_LOGIN_SUBCOMMAND in argv:
            return self.credentials(
                argv, cwd=cwd, env=env, input_text=input_text, timeout=timeout
            )
        self.calls.append(
            NativeCall(tuple(argv), Path(env[CODEX_HOME_ENV]), dict(env), input_text)
        )
        return subprocess.CompletedProcess(argv, 0, self.stdout(argv), "")


@dataclass(frozen=True)
class NativeRowLaunch:
    """One row's retained observation and every recorded command issued for its state."""

    observation: NativeProfileExecutionObservation
    calls: tuple[NativeCall, ...]


@dataclass(frozen=True)
class NativeLaunchObservation:
    rows: tuple[NativeRowLaunch, ...]
    environment: Mapping[str, str]
    """The ambient environment the run received, every strippable name planted."""


def _row_calls(
    observation: NativeProfileExecutionObservation, calls: Sequence[NativeCall]
) -> tuple[NativeCall, ...]:
    """The recorded commands whose Codex home lies beneath the row's state root."""
    state_root = observation.row.state_root.resolve()
    return tuple(call for call in calls if call.home.is_relative_to(state_root))


@contextmanager
def native_profile_launch(
    claude_credentials: Collection[str] = CLAUDE_CREDENTIAL_VARIABLES,
) -> Iterator[NativeLaunchObservation]:
    """Run every row with `claude_credentials` planted beside every other strippable name."""
    with (
        TemporaryDirectory() as temporary_directory,
        authentication_case() as credentials,
    ):
        runner = NativeLaunchRunner(credentials.runner)
        environment = ambient_environment(
            credentials.original_environment, claude_credentials=claude_credentials
        )
        rows = run_native_profile_execution(
            Path(temporary_directory) / "artifacts",
            checkout=repository_root(),
            environment=environment,
            runner=runner,
        )
        yield NativeLaunchObservation(
            tuple(NativeRowLaunch(row, _row_calls(row, runner.calls)) for row in rows),
            environment,
        )


def _absent_parent_stream(argv: Sequence[str]) -> str:
    """A Codex parent's exec stream naming a fresh thread no disposable state holds."""
    if CODEX_EXEC_SUBCOMMAND not in argv:
        return ""
    event = NativeParentEvent(type=NATIVE_THREAD_STARTED, thread_id=uuid4().hex)
    return json.dumps(event) + "\n"


@contextmanager
def native_profile_absent_child() -> Iterator[NativeLaunchObservation]:
    """Run every Codex row whose parent names a thread the real app-server never recorded.

    Installation, login, and the parent session complete at the recording
    runner; the child read is the producer's own, against the installed
    Codex app-server in each row's disposable state, so the row's terminal
    condition comes from the real listing. API login keeps that state free of
    a saved-login link the app-server could try to refresh.
    """
    with (
        TemporaryDirectory() as temporary_directory,
        authentication_case(AuthenticationMode.API) as credentials,
    ):
        runner = NativeLaunchRunner(credentials.runner, _absent_parent_stream)
        environment = {
            **credentials.original_environment,
            "PATH": os.environ["PATH"],
        }
        rows = run_native_profile_execution(
            Path(temporary_directory) / "artifacts",
            checkout=repository_root(),
            environment=environment,
            runner=runner,
            target=Target.CODEX,
        )
        yield NativeLaunchObservation(
            tuple(NativeRowLaunch(row, _row_calls(row, runner.calls)) for row in rows),
            environment,
        )
