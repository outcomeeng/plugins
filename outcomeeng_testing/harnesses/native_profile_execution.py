"""Own disposable installation, authentication, and native profile evidence."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile
from typing import Protocol

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.installation import (
    CommandResult,
    InstallationCommand,
    InstallationFailure,
    build_isolated_installation_plan,
    execute_installation,
)
from outcomeeng.distribution.native_profile_execution import (
    NativeExecutionRunners,
    NativeProfileExecutionObservation,
    NativeProfileRow,
    materialize_native_profile,
    native_profile_rows,
    record_native_profile_failure,
    run_native_profile_row,
)
from outcomeeng.distribution.native_thread_evidence import (
    THREAD_READ_COMMAND,
    THREAD_READ_TIMEOUT_SECONDS,
    read_native_child,
)
from outcomeeng_testing.harnesses.discovery_auth import (
    DISCOVERY_TIMEOUT_SECONDS,
    FILE_STORE_ARGS,
    CredentialRedactor,
    DiscoveryAuthentication,
    DiscoveryAuthenticationError,
    ProbeRunner,
    credential_free_environment,
    select_authentication,
)
from outcomeeng_testing.harnesses.installation import mirror_installation_inputs

CLAUDE_CREDENTIAL_VARIABLES = frozenset(
    {"ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"}
)
NATIVE_PROFILE_OVERRIDE_ENVIRONMENT_VARIABLES = frozenset(
    {
        "CLAUDE_CODE_EFFORT_LEVEL",
        "CLAUDE_CODE_SUBAGENT_MODEL",
        "ANTHROPIC_MODEL",
        "ANTHROPIC_DEFAULT_OPUS_MODEL",
        "ANTHROPIC_DEFAULT_SONNET_MODEL",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL",
        "ANTHROPIC_SMALL_FAST_MODEL",
        "CLAUDE_CODE_SUBAGENT_MODEL_FORCE",
    }
)
"""Ambient model and effort overrides a profile probe must not inherit."""
NATIVE_PROFILE_SESSION_MARKER_ENVIRONMENT_VARIABLE = "CLAUDECODE"
"""The marker a running Claude Code session exports to the processes it starts.

A probe launched from inside a session would otherwise inherit it and run as a
nested session rather than as the isolated parent the profile row describes.
"""
NATIVE_PROFILE_AMBIENT_ENVIRONMENT_VARIABLES = frozenset(
    {
        *NATIVE_PROFILE_OVERRIDE_ENVIRONMENT_VARIABLES,
        NATIVE_PROFILE_SESSION_MARKER_ENVIRONMENT_VARIABLE,
    }
)
"""Every ambient variable the isolation filter strips before a profile row runs."""


def run_profile_process(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    input_text: str | None,
    timeout: float,
) -> subprocess.CompletedProcess[str]:
    """Collect one bounded command and reap its owned process group on exit."""
    with (
        TemporaryFile() as stdout_capture,
        TemporaryFile() as stderr_capture,
        subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=stdout_capture,
            stderr=stderr_capture,
            text=True,
            start_new_session=True,
        ) as process,
    ):
        timed_out: subprocess.TimeoutExpired | None = None
        try:
            process.communicate(input_text, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            timed_out = error
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        stdout_capture.seek(0)
        stderr_capture.seek(0)
        stdout_bytes, stderr_bytes = stdout_capture.read(), stderr_capture.read()
        if timed_out is not None:
            timed_out.output = stdout_bytes
            timed_out.stderr = stderr_bytes
            raise timed_out
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)


@dataclass
class NativeProfileInterval:
    """Bind process calls to one row's deadline and selected authentication."""

    runner: ProbeRunner
    authentication: DiscoveryAuthentication | None = None
    redactor: CredentialRedactor = field(default_factory=CredentialRedactor)
    deadline: float = field(
        default_factory=lambda: time.monotonic() + DISCOVERY_TIMEOUT_SECONDS
    )

    def remaining(self) -> float:
        remaining = (
            self.authentication.deadline - self.authentication.clock()
            if self.authentication is not None
            else self.deadline - time.monotonic()
        )
        if remaining <= 0:
            raise TimeoutError("Native profile execution exceeded its timeout.")
        return remaining

    def sanitize(self, text: str) -> str:
        if self.authentication is not None:
            return self.authentication.redactor.clean(text)
        return self.redactor.clean(text)

    def run(
        self, argv: Sequence[str], cwd: Path, environment: Mapping[str, str]
    ) -> subprocess.CompletedProcess[str]:
        if self.authentication is not None:
            return self.authentication.run(argv, cwd=cwd, env=environment)
        result = self.runner(
            argv, cwd=cwd, env=environment, input_text=None, timeout=self.remaining()
        )
        return subprocess.CompletedProcess(
            argv,
            result.returncode,
            self.sanitize(result.stdout),
            self.sanitize(result.stderr),
        )

    def install(self, command: InstallationCommand) -> CommandResult:
        result = self.run(command.argv, command.cwd, dict(command.environment))
        return CommandResult(
            command.argv, result.returncode, result.stdout, result.stderr
        )

    def parent(
        self, argv: Sequence[str], cwd: Path, environment: Mapping[str, str]
    ) -> subprocess.CompletedProcess[str]:
        command = (
            (argv[0], *FILE_STORE_ARGS, *argv[1:])
            if self.authentication is not None
            else tuple(argv)
        )
        return self.run(command, cwd, environment)

    def thread(
        self, thread_id: str, cwd: Path, environment: Mapping[str, str]
    ) -> CommandResult:
        result = read_native_child(
            thread_id,
            cwd,
            environment,
            timeout=min(THREAD_READ_TIMEOUT_SECONDS, self.remaining()),
            command=(
                THREAD_READ_COMMAND[0],
                *FILE_STORE_ARGS,
                *THREAD_READ_COMMAND[1:],
            ),
        )
        if self.authentication is not None:
            for path in self.authentication.credential_files:
                self.authentication.redactor.capture(path)
        return CommandResult(
            result.argv,
            result.exit_code,
            self.sanitize(result.stdout),
            self.sanitize(result.stderr),
        )


def isolated_environment(environment: Mapping[str, str]) -> dict[str, str]:
    return {
        name: value
        for name, value in credential_free_environment(environment).items()
        if name not in CLAUDE_CREDENTIAL_VARIABLES
        and name not in NATIVE_PROFILE_AMBIENT_ENVIRONMENT_VARIABLES
    }


class NativeRow(Protocol):
    """The part of a native row the shared row drivers read."""

    @property
    def target(self) -> Target: ...

    @property
    def state_root(self) -> Path: ...


class FailureRecorder[Row, Observation](Protocol):
    """Retain a harness failure as one row's terminal condition."""

    def __call__(
        self, row: Row, condition: str, /, *, install_exit_code: int | None = None
    ) -> Observation: ...


def execute_native_row[Row: NativeRow, Observation](
    row: Row,
    checkout: Path,
    environment: Mapping[str, str],
    interval: NativeProfileInterval,
    *,
    subject: str,
    run: Callable[[Row, Mapping[str, str]], Observation],
) -> Observation:
    """Install one row's disposable state, authenticate its harness, and run it once.

    `subject` names the evidence in the diagnostic a missing or ambiguous Claude
    credential raises; `run` receives the row and the isolated child environment.
    """
    if row.target is Target.CODEX:
        interval.authentication = DiscoveryAuthentication(
            select_authentication(environment), interval.runner
        )
    plan = build_isolated_installation_plan(
        checkout, row.state_root, isolated_environment(environment)
    )
    execute_installation(plan, interval.install)
    child_environment = dict(plan.commands[0].environment)
    if interval.authentication is not None:
        with interval.authentication.authenticated_home(
            plan.roots.codex_home, cwd=checkout, env=child_environment
        ):
            return run(row, child_environment)
    selected = tuple(
        name for name in CLAUDE_CREDENTIAL_VARIABLES if environment.get(name)
    )
    if len(selected) != 1:
        raise DiscoveryAuthenticationError(
            f"Claude {subject} requires exactly one selected native credential."
        )
    name = selected[0]
    interval.redactor.add(environment[name])
    child_environment[name] = environment[name]
    return run(row, child_environment)


def run_native_rows[Row: NativeRow, Observation](
    artifact_root: Path,
    *,
    checkout: Path,
    plan: Callable[[Path], tuple[Row, ...]],
    materialize: Callable[[Row], None],
    execute: Callable[[Row, Path, NativeProfileInterval], Observation],
    record_failure: FailureRecorder[Row, Observation],
    runner: ProbeRunner,
    target: Target | None,
) -> tuple[Observation, ...]:
    """Retain every row's observations while removing its disposable state.

    A row's paths derive from its state root, so `plan` projects the rows again
    against each row's own disposable state. `execute` receives the row, the
    mirrored checkout, and the row's interval.
    """
    artifact_root.mkdir(parents=True, exist_ok=False)
    observations: list[Observation] = []
    with TemporaryDirectory() as temporary_checkout:
        mirror = Path(temporary_checkout) / "checkout"
        mirror_installation_inputs(checkout, mirror)
        for index in range(len(plan(Path()))):
            with TemporaryDirectory() as temporary_state:
                row = plan(Path(temporary_state))[index]
                if target is not None and row.target is not target:
                    continue
                interval = NativeProfileInterval(runner)
                try:
                    materialize(row)
                    observation = execute(row, mirror, interval)
                except (
                    OSError,
                    ValueError,
                    InstallationFailure,
                    DiscoveryAuthenticationError,
                    subprocess.TimeoutExpired,
                ) as error:
                    observation = record_failure(
                        row,
                        interval.sanitize(str(error)),
                        install_exit_code=(
                            error.result.exit_code
                            if isinstance(error, InstallationFailure)
                            else None
                        ),
                    )
                observations.append(observation)
    return tuple(observations)


def run_native_profile_execution(
    artifact_root: Path,
    *,
    checkout: Path,
    environment: Mapping[str, str],
    runner: ProbeRunner = run_profile_process,
    target: Target | None = None,
) -> tuple[NativeProfileExecutionObservation, ...]:
    """Retain every profile row's observations while removing its disposable state."""

    def plan(state_root: Path) -> tuple[NativeProfileRow, ...]:
        return native_profile_rows(artifact_root, state_root)

    def execute(
        row: NativeProfileRow, mirror: Path, interval: NativeProfileInterval
    ) -> NativeProfileExecutionObservation:
        runners = NativeExecutionRunners(
            interval.parent, interval.thread, interval.sanitize
        )

        def run(
            profile_row: NativeProfileRow, child_environment: Mapping[str, str]
        ) -> NativeProfileExecutionObservation:
            return run_native_profile_row(
                profile_row,
                checkout=mirror,
                environment=child_environment,
                runners=runners,
            )

        return execute_native_row(
            row, mirror, environment, interval, subject="profile execution", run=run
        )

    return run_native_rows(
        artifact_root,
        checkout=checkout,
        plan=plan,
        materialize=materialize_native_profile,
        execute=execute,
        record_failure=record_native_profile_failure,
        runner=runner,
        target=target,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the native evidence harness through its public recipe."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_directory", type=Path)
    parser.add_argument("--target", type=Target, choices=tuple(Target))
    arguments = parser.parse_args(argv)
    observations = run_native_profile_execution(
        arguments.artifact_directory.resolve(),
        checkout=Path.cwd(),
        environment=os.environ,
        target=arguments.target,
    )
    print(
        json.dumps(
            [
                {
                    "identifier": item.row.identifier,
                    "configuration": str(item.row.definition_path),
                    "loading": str(item.row.loading_path),
                    "result": str(item.row.result_path),
                    "terminal_condition": item.terminal_condition,
                }
                for item in observations
            ],
            sort_keys=True,
        )
    )
    return int(any(item.terminal_condition is not None for item in observations))


if __name__ == "__main__":
    raise SystemExit(main())
