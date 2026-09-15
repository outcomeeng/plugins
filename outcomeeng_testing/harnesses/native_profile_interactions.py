"""Record real entrypoint interactions using retained native response fixtures.

Process and child-lookup collaborators use the Stage 5 interaction-protocol
exception. Installation command responses are controlled; materialization,
authentication, artifact production, and disposable-state cleanup run normally.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.installation import CODEX_HOME_ENV, CommandResult
from outcomeeng.distribution.native_profile_execution import (
    NativeProfileExecutionObservation,
    native_profile_rows,
)
from outcomeeng.validation.ci_gate import CODEX_API_KEY_ENVIRONMENT
from outcomeeng_testing.harnesses.discovery_auth import (
    AuthenticationMode,
    NativeCommand,
)
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    NativeCredentialRunner,
    authentication_case,
)
from outcomeeng_testing.harnesses.installation import repository_root
from outcomeeng_testing.harnesses.native_profile_execution import (
    run_native_profile_execution,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "fixtures" / "native_profile_execution"
)


@dataclass(frozen=True)
class ProfileProcessCall:
    argv: tuple[str, ...]
    cwd: Path
    environment: Mapping[str, str] = field(repr=False)
    input_text: str | None = field(repr=False)
    timeout: float
    native_definition: bytes | None = None


@dataclass(frozen=True)
class ProfileChildCall:
    parent_id: str
    cwd: Path
    environment: Mapping[str, str] = field(repr=False)
    command: tuple[str, ...]
    timeout: float


@dataclass
class ProfileProcessRecorder:
    credentials: NativeCredentialRunner
    calls: list[ProfileProcessCall] = field(default_factory=list)

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        input_text: str | None,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        state = Path(env[CODEX_HOME_ENV]).parent
        row = next(
            (row for row in native_profile_rows() if row.identifier == state.name), None
        )
        parent = (
            row is not None
            and argv[0] == row.launch_commands[0][0]
            and row.launch_commands[0][1] in argv
        )
        definition = (
            (
                state / row.native_definition_path.relative_to(row.state_root)
            ).read_bytes()
            if parent and row is not None
            else None
        )
        self.calls.append(
            ProfileProcessCall(
                tuple(argv), cwd, dict(env), input_text, timeout, definition
            )
        )
        if NativeCommand.LOGIN in argv:
            return self.credentials(
                argv, cwd=cwd, env=env, input_text=input_text, timeout=timeout
            )
        stdout = (
            (FIXTURE_ROOT / f"{state.name}.parent.jsonl").read_text(encoding="utf-8")
            if parent
            else ""
        )
        return subprocess.CompletedProcess(tuple(argv), 0, stdout, "")


@dataclass
class ProfileChildRecorder:
    calls: list[ProfileChildCall] = field(default_factory=list)

    def __call__(
        self,
        parent_id: str,
        cwd: Path,
        environment: Mapping[str, str],
        *,
        timeout: float,
        command: Sequence[str],
    ) -> CommandResult:
        self.calls.append(
            ProfileChildCall(parent_id, cwd, dict(environment), tuple(command), timeout)
        )
        identifier = Path(environment[CODEX_HOME_ENV]).parent.name
        stdout = (FIXTURE_ROOT / f"{identifier}.child.json").read_text(encoding="utf-8")
        return CommandResult(tuple(command), 0, stdout, "")


@dataclass(frozen=True)
class NativeProfileInteractions:
    rows: tuple[NativeProfileExecutionObservation, ...]
    processes: tuple[ProfileProcessCall, ...]
    children: tuple[ProfileChildCall, ...]
    environment: Mapping[str, str] = field(repr=False)
    original_environment: Mapping[str, str] = field(repr=False)


@contextmanager
def native_profile_interactions(
    mode: AuthenticationMode, claude_credential: str
) -> Iterator[NativeProfileInteractions]:
    """Run every registry row with inert credentials and complete captured streams."""
    with TemporaryDirectory() as temporary, authentication_case(mode) as credentials:
        environment = {
            **credentials.original_environment,
            **json.loads(
                (FIXTURE_ROOT / "ambient_environment.json").read_text(encoding="utf-8")
            ),
            claude_credential: credentials.original_environment[
                CODEX_API_KEY_ENVIRONMENT
            ],
        }
        original = dict(environment)
        processes = ProfileProcessRecorder(credentials.runner)
        children = ProfileChildRecorder()
        rows = run_native_profile_execution(
            Path(temporary) / "artifacts",
            checkout=repository_root(),
            environment=environment,
            runner=processes,
            child_reader=children,
        )
        yield NativeProfileInteractions(
            rows, tuple(processes.calls), tuple(children.calls), environment, original
        )
