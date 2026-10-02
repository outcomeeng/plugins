"""Record terminal native failures with real disposable filesystems."""

from __future__ import annotations

import subprocess
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from outcomeeng.distribution.native_profile_execution import (
    NATIVE_PROFILE_AMBIENT_ENVIRONMENT_VARIABLES,
    NativeProfileExecutionObservation,
)
from outcomeeng_testing.harnesses.discovery_auth import CREDENTIAL_ENVIRONMENTS
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    NATIVE_FAILURE_EXIT_CODE,
    NativeCall,
    NativeFault,
    authentication_case,
)
from outcomeeng.distribution.installation import CODEX_HOME_ENV
from outcomeeng_testing.harnesses.native_profile_execution import (
    CLAUDE_CREDENTIAL_VARIABLES,
    run_native_profile_execution,
)
from outcomeeng_testing.harnesses.installation import repository_root


@dataclass
class NativeFailureRunner:
    """Stage 5 failure simulation at the process boundary, without predicates."""

    fault: NativeFault
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
        self.calls.append(
            NativeCall(tuple(argv), Path(env[CODEX_HOME_ENV]), dict(env), input_text)
        )
        if self.fault is NativeFault.TIMEOUT:
            raise subprocess.TimeoutExpired(argv, timeout)
        return subprocess.CompletedProcess(
            argv, NATIVE_FAILURE_EXIT_CODE, "", "installation failed"
        )


@dataclass(frozen=True)
class NativeFailureObservation:
    rows: tuple[NativeProfileExecutionObservation, ...]
    calls: tuple[NativeCall, ...]
    environment: Mapping[str, str]
    """The ambient environment the run received, every strippable name planted."""


def _ambient_environment(original: Mapping[str, str]) -> dict[str, str]:
    """The selected credentials' environment with every strippable name also set.

    An operator's shell can carry any ambient override, the Claude Code session
    marker, and every credential variable at once, so each name the isolation
    filter owns is planted with a fresh value; a name the selected
    authentication already carries keeps its value.
    """
    planted = {
        *NATIVE_PROFILE_AMBIENT_ENVIRONMENT_VARIABLES,
        *CLAUDE_CREDENTIAL_VARIABLES,
        *CREDENTIAL_ENVIRONMENTS,
    }
    return {
        **{name: uuid4().hex for name in planted},
        **original,
    }


@contextmanager
def native_profile_failure(fault: NativeFault) -> Iterator[NativeFailureObservation]:
    """Expose retained evidence after the production harness removes its state."""
    with (
        TemporaryDirectory() as temporary_directory,
        authentication_case() as credentials,
    ):
        runner = NativeFailureRunner(fault)
        environment = _ambient_environment(credentials.original_environment)
        rows = run_native_profile_execution(
            Path(temporary_directory) / "artifacts",
            checkout=repository_root(),
            environment=environment,
            runner=runner,
        )
        yield NativeFailureObservation(rows, tuple(runner.calls), environment)
