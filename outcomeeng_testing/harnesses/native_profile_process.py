"""Observe native profile timeout cleanup against a real lingering descendant."""

from __future__ import annotations

import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from outcomeeng_testing.harnesses.capturing_runner import (
    TEST_TIMEOUT_SECONDS,
    ControlledChild,
    child_exiting_with_lingering_descendant,
    never_returning_executable,
)
from outcomeeng_testing.harnesses.native_profile_execution import run_profile_process


@dataclass(frozen=True)
class NativeProfileProcessObservation:
    """Expose process outcome and timing before the harness's fallback cleanup."""

    child: ControlledChild
    result: subprocess.CompletedProcess[str] | subprocess.TimeoutExpired
    elapsed_seconds: float


@contextmanager
def lingering_native_profile_process(
    *, output: bytes = b"done"
) -> Iterator[NativeProfileProcessObservation]:
    """Run a real child and keep its process-state handle live for assertions."""
    with child_exiting_with_lingering_descendant(output=output) as child:
        yield _observe(child)


@contextmanager
def waiting_native_profile_process() -> Iterator[NativeProfileProcessObservation]:
    """Run a parent and descendant that both outlast the execution timeout."""
    with never_returning_executable(Path(sys.executable).name) as child:
        yield _observe(
            ControlledChild(
                command=(str(child.pid_path.parent / child.command[0]),),
                pid_path=child.pid_path,
            )
        )


def _observe(child: ControlledChild) -> NativeProfileProcessObservation:
    started = time.monotonic()
    outcome: subprocess.CompletedProcess[str] | subprocess.TimeoutExpired
    try:
        outcome = run_profile_process(
            child.command,
            cwd=child.pid_path.parent,
            env={},
            input_text=None,
            timeout=TEST_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        outcome = error
    return NativeProfileProcessObservation(
        child=child,
        result=outcome,
        elapsed_seconds=time.monotonic() - started,
    )
