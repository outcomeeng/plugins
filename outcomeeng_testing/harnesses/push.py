"""Recording doubles for the push orchestrator.

`TracedRunner`, `TracedToolProbe`, and `ScriptedUpstreamProbe` share one
trace list so tests can assert invocation order across tool probes,
upstream-ref capture, git push, and marketplace sync.

Exception case per `plugins/spec-tree/skills/test/references/methodology.md`:
- Stage 5 #2 (Interaction protocols): push's correctness depends on the
  presence and ordering of git/upstream/sync calls.
- Stage 5 #4 (Safety): real push mutates origin and triggers marketplace
  refresh.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from outcomeeng.distribution.push import (
    DRY_RUN_PUSH_FLAGS,
    REQUIRED_TOOLS,
    SYNC_COMMAND,
    UPSTREAM_REF_COMMAND,
    StepRunner,
    ToolProbe,
    UpstreamProbe,
)


def all_required_tools_available() -> frozenset[str]:
    """Return the complete tool set for push orchestration tests."""
    return frozenset(REQUIRED_TOOLS)


def tool_probe_invocation(tool: str) -> tuple[str, str]:
    """Return the trace entry for a required-tool probe."""
    return ("tool-probe", tool)


def all_tool_probe_invocations() -> tuple[tuple[str, str], ...]:
    """Return the trace entries for probing every required tool."""
    return tuple(tool_probe_invocation(tool) for tool in REQUIRED_TOOLS)


def sync_invocation(*args: str) -> tuple[str, ...]:
    """Return the sync command shape the push orchestrator invokes."""
    return (*SYNC_COMMAND, *args)


def tracked_upstream_ref() -> str:
    """Return a representative upstream ref captured before push."""
    return "abc123"


def force_with_lease_push_args() -> tuple[str, ...]:
    """Return a representative post-rebase git-push argument vector."""
    return (
        "--force-with-lease",
        "origin",
        "HEAD:refs/heads/feature",
    )


def git_help_push_args() -> tuple[str, ...]:
    """Return the git-push help flag that must pass through the wrapper."""
    return ("-h",)


def dry_run_push_args() -> tuple[str, ...]:
    """Return representative git-push dry-run arguments."""
    return (
        next(iter(sorted(DRY_RUN_PUSH_FLAGS))),
        "origin",
        "HEAD:refs/heads/feature",
    )


def clustered_dry_run_push_args() -> tuple[str, ...]:
    """Return representative clustered short-option dry-run arguments."""
    return (
        "-vn",
        "origin",
        "HEAD:refs/heads/feature",
    )


@dataclass
class ScriptedUpstreamProbe:
    """UpstreamProbe that returns a scripted ref (or None) on each call."""

    ref: str | None
    trace: list[tuple[str, ...]] | None = None
    calls: int = 0

    def __call__(self) -> str | None:
        self.calls += 1
        if self.trace is not None:
            self.trace.append(UPSTREAM_REF_COMMAND)
        return self.ref


@dataclass
class TracedRunner:
    """StepRunner that records call order into a shared trace."""

    exit_codes: Sequence[int] = ()
    trace: list[tuple[str, ...]] = field(default_factory=list)
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(self, argv: Sequence[str]) -> int:
        index = len(self.calls)
        call = tuple(argv)
        self.calls.append(call)
        self.trace.append(call)
        if index < len(self.exit_codes):
            return self.exit_codes[index]
        return 0


@dataclass
class TracedToolProbe:
    """ToolProbe that records availability checks into a shared trace."""

    available: frozenset[str]
    trace: list[tuple[str, ...]]
    queries: list[str] = field(default_factory=list)

    def __call__(self, name: str) -> bool:
        self.queries.append(name)
        self.trace.append(tool_probe_invocation(name))
        return name in self.available


__all__ = [
    "ScriptedUpstreamProbe",
    "TracedRunner",
    "TracedToolProbe",
    "all_required_tools_available",
    "all_tool_probe_invocations",
    "clustered_dry_run_push_args",
    "dry_run_push_args",
    "force_with_lease_push_args",
    "git_help_push_args",
    "sync_invocation",
    "tool_probe_invocation",
    "tracked_upstream_ref",
]


_: type[UpstreamProbe] = ScriptedUpstreamProbe
_2: type[StepRunner] = TracedRunner
_3: type[ToolProbe] = TracedToolProbe
