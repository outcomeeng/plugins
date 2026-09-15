"""Own disposable installation, authentication, and native profile evidence."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.installation import (
    CommandResult,
    InstallationCommand,
    InstallationFailure,
    build_isolated_installation_plan,
    execute_installation,
)
from outcomeeng.distribution.native_profile_execution import (
    NATIVE_PROFILE_OVERRIDE_ENVIRONMENT_VARIABLES,
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
    NativeChildLookup,
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

CLAUDE_CREDENTIAL_VARIABLES = ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN")


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
    child_reader: NativeChildLookup = read_native_child
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
        result = self.child_reader(
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


def _isolated_environment(environment: Mapping[str, str]) -> dict[str, str]:
    return {
        name: value
        for name, value in credential_free_environment(environment).items()
        if name not in CLAUDE_CREDENTIAL_VARIABLES
        and name not in NATIVE_PROFILE_OVERRIDE_ENVIRONMENT_VARIABLES
        and name != "CLAUDECODE"
    }


def _execute_row(
    row: NativeProfileRow,
    checkout: Path,
    environment: Mapping[str, str],
    interval: NativeProfileInterval,
) -> NativeProfileExecutionObservation:
    if row.target is Target.CODEX:
        interval.authentication = DiscoveryAuthentication(
            select_authentication(environment), interval.runner
        )
    plan = build_isolated_installation_plan(
        checkout, row.state_root, _isolated_environment(environment)
    )
    execute_installation(plan, interval.install)
    child_environment = dict(plan.commands[0].environment)
    runners = NativeExecutionRunners(
        interval.parent, interval.thread, interval.sanitize
    )
    if interval.authentication is not None:
        with interval.authentication.authenticated_home(
            row.state_root / "codex", cwd=checkout, env=child_environment
        ):
            return run_native_profile_row(
                row, checkout=checkout, environment=child_environment, runners=runners
            )
    selected = tuple(
        name for name in CLAUDE_CREDENTIAL_VARIABLES if environment.get(name)
    )
    if len(selected) != 1:
        raise DiscoveryAuthenticationError(
            "Claude profile execution requires exactly one selected native credential."
        )
    name = selected[0]
    interval.redactor.add(environment[name])
    child_environment[name] = environment[name]
    return run_native_profile_row(
        row, checkout=checkout, environment=child_environment, runners=runners
    )


def run_native_profile_execution(
    artifact_root: Path,
    *,
    checkout: Path,
    environment: Mapping[str, str],
    runner: ProbeRunner = run_profile_process,
    child_reader: NativeChildLookup = read_native_child,
    target: Target | None = None,
) -> tuple[NativeProfileExecutionObservation, ...]:
    """Retain every row's observations while removing its disposable state."""
    artifact_root.mkdir(parents=True, exist_ok=False)
    observations: list[NativeProfileExecutionObservation] = []
    with TemporaryDirectory() as temporary_checkout:
        mirror = Path(temporary_checkout) / "checkout"
        mirror_installation_inputs(checkout, mirror)
        for index in range(len(native_profile_rows())):
            with TemporaryDirectory() as temporary_state:
                row = native_profile_rows(artifact_root, Path(temporary_state))[index]
                if target is not None and row.target is not target:
                    continue
                interval = NativeProfileInterval(runner, child_reader)
                try:
                    materialize_native_profile(row)
                    observation = _execute_row(row, mirror, environment, interval)
                except (
                    OSError,
                    ValueError,
                    InstallationFailure,
                    DiscoveryAuthenticationError,
                    subprocess.TimeoutExpired,
                ) as error:
                    observation = record_native_profile_failure(
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
