"""Recording doubles for the push orchestrator.

`TracedRunner`, `TracedToolProbe`, and `ScriptedUpstreamProbe` share one
trace list so tests can assert invocation order across tool probes,
upstream-ref capture, git push, and marketplace sync.

Exception cases:

- Stage 5 #2 (Interaction protocols): push's correctness depends on the
  presence and ordering of git/upstream/sync calls.
- Stage 5 #4 (Safety): real push mutates origin and triggers marketplace
  refresh.
"""

from __future__ import annotations

import contextlib
import io
from collections.abc import Sequence
from dataclasses import dataclass, field

from outcomeeng.distribution.push import (
    GIT_TOOL,
    REQUIRED_TOOLS,
    SYNC_COMMAND,
    UPSTREAM_REF_COMMAND,
    StepRunner,
    ToolProbe,
    UpstreamProbe,
    parse_push_args,
    push,
)
from outcomeeng_testing.generators.push import (
    clustered_dry_run_push_args,
    clustered_git_help_push_args,
    dry_run_push_args,
    dry_run_then_no_dry_run_push_args,
    force_with_lease_push_args,
    git_help_push_args,
    long_git_help_push_args,
    push_failure_exit_code,
    push_option_with_dry_run_operand_args,
    recurse_submodules_bare_dry_run_args,
    recurse_submodules_bare_help_args,
    repo_option_with_dry_run_operand_args,
    separator_repository_named_like_dry_run_args,
    sync_failure_exit_code,
    tracked_upstream_ref,
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


def missing_required_tool_fails_fast_with_diagnostic() -> bool:
    for missing_tool in REQUIRED_TOOLS:
        runner = TracedRunner()
        tool_probe = TracedToolProbe(
            available=all_required_tools_available() - {missing_tool},
            trace=runner.trace,
        )
        upstream_probe = ScriptedUpstreamProbe(ref=tracked_upstream_ref())
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = push(
                ("origin", "main"),
                runner=runner,
                tool_probe=tool_probe,
                upstream_probe=upstream_probe,
            )

        if not (
            exit_code != 0
            and runner.calls == []
            and upstream_probe.calls == 0
            and missing_tool in (stderr.getvalue() + stdout.getvalue())
        ):
            return False
    return True


def tool_availability_is_checked_before_upstream_or_push() -> bool:
    runner = TracedRunner(exit_codes=(0, 0))
    tool_probe = TracedToolProbe(
        available=all_required_tools_available(), trace=runner.trace
    )
    upstream_probe = ScriptedUpstreamProbe(
        ref=tracked_upstream_ref(), trace=runner.trace
    )

    push(
        ("origin", "main"),
        runner=runner,
        tool_probe=tool_probe,
        upstream_probe=upstream_probe,
    )

    return (
        set(tool_probe.queries) >= set(REQUIRED_TOOLS)
        and runner.trace[: len(REQUIRED_TOOLS)] == list(all_tool_probe_invocations())
        and upstream_probe.calls == 1
        and runner.trace[len(REQUIRED_TOOLS)] == UPSTREAM_REF_COMMAND
        and runner.calls[0] == ("git", "push", "origin", "main")
    )


def upstream_probe_runs_before_git_push() -> bool:
    runner = TracedRunner(exit_codes=(0, 0))
    tool_probe = TracedToolProbe(
        available=all_required_tools_available(), trace=runner.trace
    )
    upstream_probe = ScriptedUpstreamProbe(
        ref=tracked_upstream_ref(), trace=runner.trace
    )

    push(
        ("origin", "main"),
        runner=runner,
        tool_probe=tool_probe,
        upstream_probe=upstream_probe,
    )

    return (
        upstream_probe.calls == 1
        and runner.trace[len(REQUIRED_TOOLS)] == UPSTREAM_REF_COMMAND
        and runner.calls[0][:2] == ("git", "push")
    )


def sync_not_invoked_when_push_fails() -> bool:
    runner = TracedRunner(exit_codes=(sync_failure_exit_code(),))
    tool_probe = TracedToolProbe(
        available=all_required_tools_available(), trace=runner.trace
    )
    upstream_probe = ScriptedUpstreamProbe(ref=tracked_upstream_ref())

    exit_code = push(
        ("origin", "main"),
        runner=runner,
        tool_probe=tool_probe,
        upstream_probe=upstream_probe,
    )

    return (
        exit_code == sync_failure_exit_code()
        and runner.calls == [("git", "push", "origin", "main")]
        and all(call[:3] != sync_invocation()[:3] for call in runner.calls)
    )


def tracked_branch_captures_upstream_and_invokes_sync_with_ref() -> bool:
    runner = TracedRunner(exit_codes=(0, 0))
    tool_probe = TracedToolProbe(
        available=all_required_tools_available(), trace=runner.trace
    )
    upstream_probe = ScriptedUpstreamProbe(
        ref=tracked_upstream_ref(), trace=runner.trace
    )

    exit_code = push(
        ("origin", "main"),
        runner=runner,
        tool_probe=tool_probe,
        upstream_probe=upstream_probe,
    )

    return (
        exit_code == 0
        and upstream_probe.calls == 1
        and runner.calls
        == [
            ("git", "push", "origin", "main"),
            sync_invocation(tracked_upstream_ref()),
        ]
        and runner.trace
        == [
            *all_tool_probe_invocations(),
            UPSTREAM_REF_COMMAND,
            ("git", "push", "origin", "main"),
            sync_invocation(tracked_upstream_ref()),
        ]
    )


def untracked_branch_invokes_sync_without_ref() -> bool:
    runner = TracedRunner(exit_codes=(0, 0))
    tool_probe = TracedToolProbe(
        available=all_required_tools_available(), trace=runner.trace
    )
    upstream_probe = ScriptedUpstreamProbe(ref=None, trace=runner.trace)

    exit_code = push(
        ("origin", "feature"),
        runner=runner,
        tool_probe=tool_probe,
        upstream_probe=upstream_probe,
    )

    return (
        exit_code == 0
        and upstream_probe.calls == 1
        and runner.calls == [("git", "push", "origin", "feature"), sync_invocation()]
    )


def failed_git_push_propagates_exit_code_and_skips_sync() -> bool:
    runner = TracedRunner(exit_codes=(push_failure_exit_code(),))
    tool_probe = TracedToolProbe(
        available=all_required_tools_available(), trace=runner.trace
    )
    upstream_probe = ScriptedUpstreamProbe(
        ref=tracked_upstream_ref(), trace=runner.trace
    )

    exit_code = push(
        ("origin", "main"),
        runner=runner,
        tool_probe=tool_probe,
        upstream_probe=upstream_probe,
    )

    return exit_code == push_failure_exit_code() and runner.calls == [
        ("git", "push", "origin", "main")
    ]


def no_push_args_forwards_bare_git_push() -> bool:
    runner = TracedRunner(exit_codes=(0, 0))
    tool_probe = TracedToolProbe(
        available=all_required_tools_available(), trace=runner.trace
    )
    upstream_probe = ScriptedUpstreamProbe(
        ref=tracked_upstream_ref(), trace=runner.trace
    )

    exit_code = push(
        (),
        runner=runner,
        tool_probe=tool_probe,
        upstream_probe=upstream_probe,
    )

    return exit_code == 0 and runner.calls == [
        ("git", "push"),
        sync_invocation(tracked_upstream_ref()),
    ]


def cli_parser_forwards_leading_git_options_verbatim() -> bool:
    return parse_push_args(force_with_lease_push_args()) == force_with_lease_push_args()


def cli_parser_forwards_git_help_flag_verbatim() -> bool:
    return parse_push_args(git_help_push_args()) == git_help_push_args()


def git_help_push_does_not_refresh_marketplace() -> bool:
    return _push_does_not_refresh_marketplace(git_help_push_args())


def long_git_help_push_does_not_refresh_marketplace() -> bool:
    return _push_does_not_refresh_marketplace(long_git_help_push_args())


def clustered_git_help_push_does_not_refresh_marketplace() -> bool:
    return _push_does_not_refresh_marketplace(clustered_git_help_push_args())


def git_help_push_requires_only_git_and_skips_marketplace_upstream_capture() -> bool:
    runner = TracedRunner()
    tool_probe = TracedToolProbe(available=frozenset(), trace=runner.trace)
    upstream_probe = ScriptedUpstreamProbe(tracked_upstream_ref(), runner.trace)
    stdout = io.StringIO()
    stderr = io.StringIO()

    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = push(
            git_help_push_args(),
            runner=runner,
            tool_probe=tool_probe,
            upstream_probe=upstream_probe,
        )

    return (
        exit_code != 0
        and tool_probe.queries == [GIT_TOOL]
        and runner.calls == []
        and upstream_probe.calls == 0
        and GIT_TOOL in (stderr.getvalue() + stdout.getvalue())
    )


def git_help_push_forwards_when_only_git_is_available() -> bool:
    runner = TracedRunner()
    tool_probe = TracedToolProbe(available=frozenset((GIT_TOOL,)), trace=runner.trace)
    upstream_probe = ScriptedUpstreamProbe(tracked_upstream_ref(), runner.trace)
    args = git_help_push_args()

    exit_code = push(
        args,
        runner=runner,
        tool_probe=tool_probe,
        upstream_probe=upstream_probe,
    )

    return (
        exit_code == 0
        and tool_probe.queries == [GIT_TOOL]
        and upstream_probe.calls == 0
        and runner.trace == [tool_probe_invocation(GIT_TOOL), (GIT_TOOL, "push", *args)]
    )


def recurse_submodules_bare_dry_run_does_not_refresh_marketplace() -> bool:
    return _push_does_not_refresh_marketplace(recurse_submodules_bare_dry_run_args())


def recurse_submodules_bare_help_requires_only_git_and_skips_upstream_capture() -> bool:
    runner = TracedRunner()
    tool_probe = TracedToolProbe(available=frozenset((GIT_TOOL,)), trace=runner.trace)
    upstream_probe = ScriptedUpstreamProbe(tracked_upstream_ref(), runner.trace)
    args = recurse_submodules_bare_help_args()

    exit_code = push(
        args,
        runner=runner,
        tool_probe=tool_probe,
        upstream_probe=upstream_probe,
    )

    return (
        exit_code == 0
        and tool_probe.queries == [GIT_TOOL]
        and upstream_probe.calls == 0
        and runner.trace == [tool_probe_invocation(GIT_TOOL), (GIT_TOOL, "push", *args)]
    )


def dry_run_push_does_not_refresh_marketplace() -> bool:
    return _push_does_not_refresh_marketplace(dry_run_push_args())


def clustered_short_option_dry_run_does_not_refresh_marketplace() -> bool:
    return _push_does_not_refresh_marketplace(clustered_dry_run_push_args())


def no_dry_run_option_restores_marketplace_refresh() -> bool:
    return _push_refreshes_marketplace(dry_run_then_no_dry_run_push_args())


def push_option_operand_named_like_dry_run_still_refreshes_marketplace() -> bool:
    return _push_refreshes_marketplace(push_option_with_dry_run_operand_args())


def repo_option_operand_named_like_dry_run_still_refreshes_marketplace() -> bool:
    return _push_refreshes_marketplace(repo_option_with_dry_run_operand_args())


def separator_repository_named_like_dry_run_still_refreshes_marketplace() -> bool:
    return _push_refreshes_marketplace(separator_repository_named_like_dry_run_args())


def _push_does_not_refresh_marketplace(args: tuple[str, ...]) -> bool:
    runner = TracedRunner()

    exit_code = push(
        args,
        runner=runner,
        tool_probe=TracedToolProbe(all_required_tools_available(), runner.trace),
        upstream_probe=ScriptedUpstreamProbe(tracked_upstream_ref(), runner.trace),
    )

    return exit_code == 0 and runner.calls == [("git", "push", *args)]


def _push_refreshes_marketplace(args: tuple[str, ...]) -> bool:
    runner = TracedRunner(exit_codes=(0, 0))

    exit_code = push(
        args,
        runner=runner,
        tool_probe=TracedToolProbe(all_required_tools_available(), runner.trace),
        upstream_probe=ScriptedUpstreamProbe(tracked_upstream_ref(), runner.trace),
    )

    return exit_code == 0 and runner.calls == [
        ("git", "push", *args),
        sync_invocation(tracked_upstream_ref()),
    ]


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
    "clustered_git_help_push_args",
    "clustered_git_help_push_does_not_refresh_marketplace",
    "clustered_dry_run_push_args",
    "dry_run_then_no_dry_run_push_args",
    "dry_run_push_args",
    "force_with_lease_push_args",
    "git_help_push_args",
    "git_help_push_forwards_when_only_git_is_available",
    "git_help_push_requires_only_git_and_skips_marketplace_upstream_capture",
    "push_option_with_dry_run_operand_args",
    "recurse_submodules_bare_dry_run_args",
    "recurse_submodules_bare_dry_run_does_not_refresh_marketplace",
    "recurse_submodules_bare_help_args",
    "recurse_submodules_bare_help_requires_only_git_and_skips_upstream_capture",
    "repo_option_with_dry_run_operand_args",
    "separator_repository_named_like_dry_run_args",
    "push_failure_exit_code",
    "sync_failure_exit_code",
    "sync_invocation",
    "tool_probe_invocation",
    "tracked_upstream_ref",
]


_: type[UpstreamProbe] = ScriptedUpstreamProbe
_2: type[StepRunner] = TracedRunner
_3: type[ToolProbe] = TracedToolProbe
