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

import subprocess
from collections.abc import Collection, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.installation import CODEX_HOME_ENV
from outcomeeng.distribution.native_auditor_dispatch import (
    AGENTS_DIRECTORY,
    FIXTURE_DIRECTORY,
    NativeAuditorDispatchObservation,
    native_auditor_rows,
)
from outcomeeng_testing.harnesses.discovery_auth import CODEX_LOGIN_SUBCOMMAND
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    NativeCall,
    NativeCredentialRunner,
    NativeFault,
    authentication_case,
)
from outcomeeng_testing.harnesses.installation import repository_root
from outcomeeng_testing.harnesses.native_auditor_dispatch import (
    run_native_auditor_dispatch,
)
from outcomeeng_testing.harnesses.native_profile_execution import (
    CLAUDE_CREDENTIAL_VARIABLES,
)
from outcomeeng_testing.harnesses.native_profile_failures import NativeFailureRunner
from outcomeeng_testing.harnesses.native_profile_launch import ambient_environment


@dataclass(frozen=True)
class DispatchCall:
    """One recorded command and the materialized state present when it ran."""

    argv: tuple[str, ...]
    home: Path
    environment: Mapping[str, str]
    state_files: Mapping[Path, bytes] = field(repr=False)
    """Bytes of every file under an `agents` or `fixture` directory of the row's state, keyed relative to it."""


def _materialized_state(state_root: Path) -> dict[Path, bytes]:
    return {
        path.relative_to(state_root): path.read_bytes()
        for path in state_root.rglob("*")
        if path.is_file() and {AGENTS_DIRECTORY, FIXTURE_DIRECTORY} & set(path.parts)
    }


@dataclass
class AuditorLaunchRunner:
    """Complete and record every non-login command; fail the dispatch launch on request."""

    credentials: NativeCredentialRunner
    launch_exit_code: int
    launches: frozenset[tuple[str, ...]]
    calls: list[DispatchCall] = field(default_factory=list)

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
        home = Path(env[CODEX_HOME_ENV])
        self.calls.append(
            DispatchCall(tuple(argv), home, dict(env), _materialized_state(home.parent))
        )
        is_launch = any(set(launch) <= set(argv) for launch in self.launches)
        return subprocess.CompletedProcess(
            argv, self.launch_exit_code if is_launch else 0, "", ""
        )


@dataclass(frozen=True)
class DispatchRowLaunch:
    """One row's retained observation and every command issued for its state."""

    observation: NativeAuditorDispatchObservation
    calls: tuple[DispatchCall, ...]


@dataclass(frozen=True)
class DispatchLaunchObservation:
    rows: tuple[DispatchRowLaunch, ...]
    environment: Mapping[str, str]
    """The ambient environment the run received, every strippable name planted."""


@dataclass(frozen=True)
class DispatchFailureObservation:
    rows: tuple[NativeAuditorDispatchObservation, ...]
    calls: tuple[NativeCall, ...]
    environment: Mapping[str, str]


def _row_calls(
    observation: NativeAuditorDispatchObservation, calls: Sequence[DispatchCall]
) -> tuple[DispatchCall, ...]:
    state_root = observation.row.state_root.resolve()
    return tuple(call for call in calls if call.home.is_relative_to(state_root))


@contextmanager
def native_auditor_launch(
    claude_credentials: Collection[str] = CLAUDE_CREDENTIAL_VARIABLES,
    launch_exit_code: int = 0,
) -> Iterator[DispatchLaunchObservation]:
    """Run every row with `claude_credentials` planted beside every other strippable name."""
    with (
        TemporaryDirectory() as temporary_directory,
        authentication_case() as credentials,
    ):
        runner = AuditorLaunchRunner(
            credentials.runner,
            launch_exit_code,
            frozenset(
                row.launch_command for row in native_auditor_rows(repository_root())
            ),
        )
        environment = ambient_environment(
            credentials.original_environment, claude_credentials=claude_credentials
        )
        rows = run_native_auditor_dispatch(
            Path(temporary_directory) / "artifacts",
            checkout=repository_root(),
            environment=environment,
            runner=runner,
        )
        yield DispatchLaunchObservation(
            tuple(
                DispatchRowLaunch(row, _row_calls(row, runner.calls)) for row in rows
            ),
            environment,
        )


@contextmanager
def native_auditor_failure(fault: NativeFault) -> Iterator[DispatchFailureObservation]:
    """Expose retained evidence after the production harness removes its state."""
    with (
        TemporaryDirectory() as temporary_directory,
        authentication_case() as credentials,
    ):
        runner = NativeFailureRunner(fault)
        environment = ambient_environment(
            credentials.original_environment,
            claude_credentials=CLAUDE_CREDENTIAL_VARIABLES,
        )
        rows = run_native_auditor_dispatch(
            Path(temporary_directory) / "artifacts",
            checkout=repository_root(),
            environment=environment,
            runner=runner,
        )
        yield DispatchFailureObservation(rows, tuple(runner.calls), environment)
