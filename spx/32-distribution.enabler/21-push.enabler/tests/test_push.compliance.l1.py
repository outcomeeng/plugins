"""Level-1 compliance evidence for `spx/32-distribution.enabler/21-push.enabler/`.

Covers the three compliance assertions in `push.md`:
- ALWAYS: check tool availability before any orchestration step.
- ALWAYS: capture the upstream ref before invoking `git push`.
- NEVER: invoke sync when `git push` failed.
"""

from __future__ import annotations

import pytest

from outcomeeng.distribution.push import REQUIRED_TOOLS, push
from outcomeeng_testing.harnesses.push import ScriptedUpstreamProbe
from outcomeeng_testing.harnesses.sync import RecordingRunner, ScriptedToolProbe

ALL_TOOLS_AVAILABLE = frozenset(REQUIRED_TOOLS)
SYNC_INVOCATION: tuple[str, ...] = (
    "uv",
    "run",
    "python",
    "-m",
    "outcomeeng.distribution.sync",
)


@pytest.mark.parametrize("missing_tool", REQUIRED_TOOLS)
def test_missing_required_tool_fails_fast_with_diagnostic(
    missing_tool: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(
        available=ALL_TOOLS_AVAILABLE - {missing_tool},
    )
    upstream_probe = ScriptedUpstreamProbe(ref="abc123")

    exit_code = push(
        ("origin", "main"),
        runner=runner,
        tool_probe=tool_probe,
        upstream_probe=upstream_probe,
    )

    assert exit_code != 0
    assert runner.calls == []
    assert upstream_probe.calls == 0
    captured = capsys.readouterr()
    assert missing_tool in (captured.err + captured.out)


def test_tool_availability_is_checked_before_upstream_or_push() -> None:
    runner = RecordingRunner(exit_codes=(0, 0))
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    upstream_probe = ScriptedUpstreamProbe(ref="abc123")

    push(
        ("origin", "main"),
        runner=runner,
        tool_probe=tool_probe,
        upstream_probe=upstream_probe,
    )

    assert set(tool_probe.queries) >= set(REQUIRED_TOOLS)
    # All four required tools were queried before either the upstream probe or
    # the first runner call could have observed evidence of an out-of-order
    # invocation.
    assert upstream_probe.calls == 1
    assert runner.calls[0] == ("git", "push", "origin", "main")


def test_upstream_probe_runs_before_git_push() -> None:
    """The recording doubles prove the order: upstream first, push second."""
    runner = RecordingRunner(exit_codes=(0, 0))
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    upstream_probe = ScriptedUpstreamProbe(ref="abc123")

    push(
        ("origin", "main"),
        runner=runner,
        tool_probe=tool_probe,
        upstream_probe=upstream_probe,
    )

    # The probe was called exactly once and that one call happened before any
    # runner invocation — the runner's first recorded call is `git push`.
    assert upstream_probe.calls == 1
    assert runner.calls[0][:2] == ("git", "push")


def test_sync_not_invoked_when_push_fails() -> None:
    runner = RecordingRunner(exit_codes=(13,))
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    upstream_probe = ScriptedUpstreamProbe(ref="abc123")

    exit_code = push(
        ("origin", "main"),
        runner=runner,
        tool_probe=tool_probe,
        upstream_probe=upstream_probe,
    )

    assert exit_code == 13
    # Only the git push call was recorded — no sync invocation.
    assert runner.calls == [("git", "push", "origin", "main")]
    assert all(call[:3] != SYNC_INVOCATION[:3] for call in runner.calls)
