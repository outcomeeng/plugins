"""Recording collaborators and observations for direct marketplace push."""

from __future__ import annotations

import contextlib
import io
from collections.abc import Sequence
from dataclasses import dataclass, field

from outcomeeng.distribution.push import (
    GIT_TOOL,
    StepRunner,
    ToolProbe,
    parse_push_args,
    push,
)


@dataclass(frozen=True)
class PushObservation:
    """Exit, command, probe, and diagnostic observations from one push."""

    supplied_args: tuple[str, ...]
    parsed_args: tuple[str, ...]
    runner_exit_code: int
    exit_code: int
    calls: tuple[tuple[str, ...], ...]
    queries: tuple[str, ...]
    stdout: str
    stderr: str


@dataclass
class RecordingRunner:
    """Record one direct-push command and return a scripted process exit."""

    exit_code: int
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(self, argv: Sequence[str]) -> int:
        self.calls.append(tuple(argv))
        return self.exit_code


@dataclass
class RecordingToolProbe:
    """Record executable queries and expose a scripted git availability."""

    git_available: bool
    queries: list[str] = field(default_factory=list)

    def __call__(self, name: str) -> bool:
        self.queries.append(name)
        return self.git_available and name == GIT_TOOL


def observe_explicit_ref_push() -> PushObservation:
    """Observe leading flags and an explicit refspec crossing the push boundary."""
    return _observe_push(("--force-with-lease", "origin", "HEAD:refs/heads/feature"))


def observe_failed_push() -> PushObservation:
    """Observe process-exit propagation from one failed git push."""
    return _observe_push(("origin", "main"), runner_exit_code=7)


def observe_help_push() -> PushObservation:
    """Observe a git-help request through the same direct boundary."""
    return _observe_push(("--help",))


def observe_missing_git() -> PushObservation:
    """Observe the fail-fast diagnostic when git is unavailable."""
    return _observe_push(("origin", "main"), git_available=False)


def observe_bare_push() -> PushObservation:
    """Observe the no-argument direct push command."""
    return _observe_push(())


def _observe_push(
    supplied_args: tuple[str, ...],
    *,
    runner_exit_code: int = 0,
    git_available: bool = True,
) -> PushObservation:
    runner = RecordingRunner(exit_code=runner_exit_code)
    runner_contract: StepRunner = runner
    tool_probe = RecordingToolProbe(git_available=git_available)
    tool_probe_contract: ToolProbe = tool_probe
    stdout = io.StringIO()
    stderr = io.StringIO()
    parsed_args = parse_push_args(supplied_args)
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = push(
            parsed_args,
            runner=runner_contract,
            tool_probe=tool_probe_contract,
        )
    return PushObservation(
        supplied_args=supplied_args,
        parsed_args=parsed_args,
        runner_exit_code=runner_exit_code,
        exit_code=exit_code,
        calls=tuple(runner.calls),
        queries=tuple(tool_probe.queries),
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
    )


__all__ = [
    "PushObservation",
    "RecordingRunner",
    "RecordingToolProbe",
    "observe_bare_push",
    "observe_explicit_ref_push",
    "observe_failed_push",
    "observe_help_push",
    "observe_missing_git",
]
