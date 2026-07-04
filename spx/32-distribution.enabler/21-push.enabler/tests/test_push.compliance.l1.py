"""Level-1 compliance evidence for `spx/32-distribution.enabler/21-push.enabler/`."""

from __future__ import annotations

from outcomeeng_testing.harnesses.push import (
    missing_required_tool_fails_fast_with_diagnostic,
    sync_not_invoked_when_push_fails,
    tool_availability_is_checked_before_upstream_or_push,
    upstream_probe_runs_before_git_push,
)


def test_missing_required_tool_fails_fast_with_diagnostic() -> None:
    assert missing_required_tool_fails_fast_with_diagnostic()


def test_tool_availability_is_checked_before_upstream_or_push() -> None:
    assert tool_availability_is_checked_before_upstream_or_push()


def test_upstream_probe_runs_before_git_push() -> None:
    assert upstream_probe_runs_before_git_push()


def test_sync_not_invoked_when_push_fails() -> None:
    assert sync_not_invoked_when_push_fails()
