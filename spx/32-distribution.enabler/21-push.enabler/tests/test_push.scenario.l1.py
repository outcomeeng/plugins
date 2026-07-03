"""Level-1 scenario evidence for `spx/32-distribution.enabler/21-push.enabler/`.

Covers the scenario assertions in `push.md`:
- Tracked branch: capture upstream, run `git push`, invoke sync with the
  captured ref as `base_ref`.
- Untracked branch: run `git push`, invoke sync without a `base_ref`.
- Push failure: propagate the non-zero exit code and do not invoke sync.
- Leading flags: forward every argument to `git push` without parser
  interpretation.
- Dry-run push: run `git push` without refreshing marketplace state.

Runner calls and upstream-probe interactions are observed through the
traced doubles in `outcomeeng_testing.harnesses.push`.
"""

from __future__ import annotations

from outcomeeng.distribution.push import UPSTREAM_REF_COMMAND, parse_push_args, push
from outcomeeng_testing.harnesses.push import (
    ScriptedUpstreamProbe,
    TracedRunner,
    TracedToolProbe,
    all_required_tools_available,
    all_tool_probe_invocations,
    clustered_dry_run_push_args,
    dry_run_then_no_dry_run_push_args,
    dry_run_push_args,
    force_with_lease_push_args,
    git_help_push_args,
    sync_invocation,
    tracked_upstream_ref,
)


def test_tracked_branch_captures_upstream_and_invokes_sync_with_ref() -> None:
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

    assert exit_code == 0
    assert upstream_probe.calls == 1
    assert runner.calls == [
        ("git", "push", "origin", "main"),
        sync_invocation(tracked_upstream_ref()),
    ]
    assert runner.trace == [
        *all_tool_probe_invocations(),
        UPSTREAM_REF_COMMAND,
        ("git", "push", "origin", "main"),
        sync_invocation(tracked_upstream_ref()),
    ]


def test_untracked_branch_invokes_sync_without_ref() -> None:
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

    assert exit_code == 0
    assert upstream_probe.calls == 1
    assert runner.calls == [
        ("git", "push", "origin", "feature"),
        sync_invocation(),
    ]


def test_failed_git_push_propagates_exit_code_and_skips_sync() -> None:
    runner = TracedRunner(exit_codes=(7,))
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

    assert exit_code == 7
    assert runner.calls == [("git", "push", "origin", "main")]


def test_no_push_args_forwards_bare_git_push() -> None:
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

    assert exit_code == 0
    assert runner.calls == [
        ("git", "push"),
        sync_invocation(tracked_upstream_ref()),
    ]


def test_cli_parser_forwards_leading_git_options_verbatim() -> None:
    assert parse_push_args(force_with_lease_push_args()) == force_with_lease_push_args()


def test_cli_parser_forwards_git_help_flag_verbatim() -> None:
    assert parse_push_args(git_help_push_args()) == git_help_push_args()


def test_dry_run_push_does_not_refresh_marketplace() -> None:
    runner = TracedRunner()
    trace = runner.trace

    exit_code = push(
        dry_run_push_args(),
        runner=runner,
        tool_probe=TracedToolProbe(all_required_tools_available(), trace),
        upstream_probe=ScriptedUpstreamProbe(tracked_upstream_ref(), trace),
    )

    assert exit_code == 0
    assert runner.calls == [("git", "push", *dry_run_push_args())]


def test_clustered_short_option_dry_run_does_not_refresh_marketplace() -> None:
    runner = TracedRunner()
    trace = runner.trace

    exit_code = push(
        clustered_dry_run_push_args(),
        runner=runner,
        tool_probe=TracedToolProbe(all_required_tools_available(), trace),
        upstream_probe=ScriptedUpstreamProbe(tracked_upstream_ref(), trace),
    )

    assert exit_code == 0
    assert runner.calls == [("git", "push", *clustered_dry_run_push_args())]


def test_no_dry_run_option_restores_marketplace_refresh() -> None:
    runner = TracedRunner(exit_codes=(0, 0))
    trace = runner.trace

    exit_code = push(
        dry_run_then_no_dry_run_push_args(),
        runner=runner,
        tool_probe=TracedToolProbe(all_required_tools_available(), trace),
        upstream_probe=ScriptedUpstreamProbe(tracked_upstream_ref(), trace),
    )

    assert exit_code == 0
    assert runner.calls == [
        ("git", "push", *dry_run_then_no_dry_run_push_args()),
        sync_invocation(tracked_upstream_ref()),
    ]
