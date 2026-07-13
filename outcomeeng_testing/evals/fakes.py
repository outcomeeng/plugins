"""Stub and recording runners for l1 meta-tests of the eval harness."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from outcomeeng_evals.runner import ModelRunner, RunMetadata, RunResult


@dataclass(frozen=True)
class SubprocessCall:
    """Observed arguments for one injected subprocess invocation."""

    argv: tuple[str, ...]
    input: str
    capture_output: bool
    text: bool
    timeout: float
    check: bool
    env: dict[str, str]


@dataclass
class RecordingSubprocessRunner:
    """Record a subprocess boundary and return a controlled process result."""

    stdout: str
    returncode: int = os.EX_OK
    stderr: str = ""
    calls: list[SubprocessCall] = field(default_factory=list)

    def __call__(
        self,
        argv: list[str],
        *,
        input: str,
        capture_output: bool,
        text: bool,
        timeout: float,
        check: bool,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append(
            SubprocessCall(
                argv=tuple(argv),
                input=input,
                capture_output=capture_output,
                text=text,
                timeout=timeout,
                check=check,
                env=dict(env),
            )
        )
        return subprocess.CompletedProcess(
            argv,
            self.returncode,
            stdout=self.stdout,
            stderr=self.stderr,
        )


RECORDING_UV_COMMANDS_ENV: Final = "OUTCOMEENG_EVALS_RECORDING_UV_COMMANDS"
RECORDING_UV_EXIT_CODE_ENV: Final = "OUTCOMEENG_EVALS_RECORDING_UV_EXIT_CODE"
RECORDING_UV_SCRIPT = """#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

record_path = Path(os.environ["OUTCOMEENG_EVALS_RECORDING_UV_COMMANDS"])
with record_path.open("a", encoding="utf-8") as output:
    output.write(json.dumps(sys.argv[1:]) + "\\n")
raise SystemExit(int(os.environ.get("OUTCOMEENG_EVALS_RECORDING_UV_EXIT_CODE", "0")))
"""


@dataclass(frozen=True)
class StubModelRunner:
    """Return a canned ``RunResult`` for any prompt.

    Supply either ``response`` (a single canned text) or ``responder`` (a
    callable mapping prompt -> response text). Metadata is empty unless
    ``metadata`` is supplied.
    """

    response: str = ""
    responder: Callable[[str], str] | None = field(default=None)
    metadata: RunMetadata = field(default_factory=RunMetadata)

    def run(self, prompt: str) -> RunResult:
        text = self.responder(prompt) if self.responder is not None else self.response
        return RunResult(text=text, metadata=self.metadata)


@dataclass(frozen=True)
class RaisingModelRunner:
    """A ``ModelRunner`` whose ``run`` always raises ``error``.

    For meta-tests of suite-level fault isolation: a real ``claude``
    non-zero exit or timeout surfaces as an exception out of ``run`` (a
    ``RuntimeError`` or ``subprocess.TimeoutExpired``), and ``run_suite``
    must convert it to a failing outcome rather than crash the whole run.
    """

    error: BaseException

    def run(self, prompt: str) -> RunResult:  # noqa: ARG002 — prompt is unused; this runner always raises before reading it
        raise self.error


@dataclass
class RecordingRunner:
    """Wrap another runner and record every prompt and response.

    Not ``frozen=True`` — the runner is inherently stateful: ``run`` appends
    each (prompt, result) pair to ``transcripts``. The dataclass is mutable
    so the list can grow across invocations.

    Not safe for parallel use: ``transcripts.append`` is GIL-atomic in
    CPython but offers no ordering or isolation guarantee across threads or
    processes. Recording under ``run_suite(workers > 1)`` (or a
    ``ProcessPoolExecutor``) needs an external lock; the meta-tests that
    use this runner are single-threaded.
    """

    inner: ModelRunner
    transcripts: list[tuple[str, RunResult]] = field(default_factory=list)

    def run(self, prompt: str) -> RunResult:
        result = self.inner.run(prompt)
        self.transcripts.append((prompt, result))
        return result


@dataclass
class RecordingCommandRunner:
    """Callable command runner that records argv tuples and returns scripted exits."""

    exit_codes: Sequence[int] = ()
    default_exit_code: int = os.EX_OK
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(self, command: Sequence[str]) -> int:
        index = len(self.calls)
        self.calls.append(tuple(command))
        return (
            self.exit_codes[index]
            if index < len(self.exit_codes)
            else self.default_exit_code
        )


@dataclass(frozen=True)
class RecordingUvExecutable:
    """Temporary ``uv`` executable that records argv and exits with a fixed code."""

    bin_dir: Path
    record_path: Path
    env: dict[str, str]

    def commands(self) -> tuple[tuple[str, ...], ...]:
        if not self.record_path.exists():
            return ()
        return tuple(
            tuple(json.loads(line))
            for line in self.record_path.read_text(encoding="utf-8").splitlines()
        )


def make_recording_uv_executable(
    tmp_path: Path,
    *,
    exit_code: int = os.EX_OK,
) -> RecordingUvExecutable:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    uv_path = bin_dir / "uv"
    uv_path.write_text(RECORDING_UV_SCRIPT, encoding="utf-8")
    uv_path.chmod(0o755)
    record_path = tmp_path / "uv-commands.jsonl"
    env = {
        "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        RECORDING_UV_COMMANDS_ENV: str(record_path),
        RECORDING_UV_EXIT_CODE_ENV: str(exit_code),
    }
    return RecordingUvExecutable(
        bin_dir=bin_dir,
        record_path=record_path,
        env=env,
    )
