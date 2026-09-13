"""Record terminal native failures with real disposable filesystems."""

from __future__ import annotations

import subprocess
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.native_profile_execution import (
    NativeProfileExecutionObservation,
)
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    NATIVE_FAILURE_EXIT_CODE,
    NativeCall,
    NativeFault,
    authentication_case,
)
from outcomeeng.distribution.installation import CODEX_HOME_ENV
from outcomeeng_testing.harnesses.native_profile_execution import (
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


@contextmanager
def native_profile_failure(fault: NativeFault) -> Iterator[NativeFailureObservation]:
    """Expose retained evidence after the production harness removes its state."""
    with (
        TemporaryDirectory() as temporary_directory,
        authentication_case() as credentials,
    ):
        runner = NativeFailureRunner(fault)
        rows = run_native_profile_execution(
            Path(temporary_directory) / "artifacts",
            checkout=repository_root(),
            environment=credentials.original_environment,
            runner=runner,
        )
        yield NativeFailureObservation(rows, tuple(runner.calls))
