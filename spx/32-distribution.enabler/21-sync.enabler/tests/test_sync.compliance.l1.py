"""Level-1 compliance evidence for `spx/32-distribution.enabler/21-sync.enabler/`.

Covers the compliance assertions in `sync.md`:
- ALWAYS: check availability of every tool in `REQUIRED_TOOLS` before any
  orchestration step. A missing tool fails fast with a diagnostic naming
  the tool, and no runner call is made.
- ALWAYS: reconcile runtime marketplace source configuration before consulting
  the distribution-change probe.
- NEVER: skip any validation step when plugin distribution paths changed.
  Every change-driven run executes the full sequence in order, or stops at
  the first non-zero step exit code (no silent skip).
- NEVER: declare or invoke a sync step whose contract is `codex_cache_preserve`.
"""

from __future__ import annotations

import pytest

from outcomeeng.distribution.sync import REQUIRED_TOOLS, STEPS, sync
from outcomeeng_testing.harnesses.sync import (
    CHANGE_PROBE_EVENT,
    CONFIG_REPAIR_EVENT,
    RUNNER_EVENT,
    RecordingRunner,
    ScriptedChangeProbe,
    ScriptedConfigRepairer,
    ScriptedToolProbe,
    TOOL_PROBE_EVENT_PREFIX,
)

ALL_TOOLS_AVAILABLE = frozenset(REQUIRED_TOOLS)
STEP_ARGVS: tuple[tuple[str, ...], ...] = tuple(step.argv for step in STEPS)


@pytest.mark.parametrize("missing_tool", REQUIRED_TOOLS)
def test_missing_required_tool_fails_fast_with_diagnostic(
    missing_tool: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = RecordingRunner()
    config_repairer = ScriptedConfigRepairer(changed=False)
    tool_probe = ScriptedToolProbe(
        available=ALL_TOOLS_AVAILABLE - {missing_tool},
    )
    change_probe = ScriptedChangeProbe(changed=True)

    exit_code = sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
    )

    assert exit_code != 0
    assert runner.calls == []
    assert config_repairer.calls == 0
    assert change_probe.queries == []
    captured = capsys.readouterr()
    assert missing_tool in (captured.err + captured.out)


def test_tool_availability_is_checked_before_any_runner_call() -> None:
    """The first probe of any required tool must precede any runner call."""
    events: list[str] = []
    runner = RecordingRunner(events=events)
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE, events=events)
    change_probe = ScriptedChangeProbe(changed=True)
    config_repairer = ScriptedConfigRepairer(changed=False)

    sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
    )

    # Every required tool was probed.
    assert set(tool_probe.queries) >= set(REQUIRED_TOOLS)
    assert config_repairer.calls == 1
    first_runner_index = events.index(RUNNER_EVENT)
    tool_probe_events = {f"{TOOL_PROBE_EVENT_PREFIX}{tool}" for tool in REQUIRED_TOOLS}
    assert tool_probe_events.issubset(set(events[:first_runner_index]))
    # No reordering: all step calls happened (none skipped).
    assert runner.calls == list(STEP_ARGVS)


def test_source_reconciliation_precedes_distribution_change_probe() -> None:
    events: list[str] = []
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False, events=events)
    config_repairer = ScriptedConfigRepairer(changed=False, events=events)

    exit_code = sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
    )

    assert exit_code == 0
    assert runner.calls == []
    assert events == [CONFIG_REPAIR_EVENT, CHANGE_PROBE_EVENT]


def test_changes_present_runs_full_sequence_when_every_step_succeeds() -> None:
    """No silent skip when steps return 0 — every declared step is invoked."""
    runner = RecordingRunner(exit_codes=tuple(0 for _ in STEPS))
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=True)
    config_repairer = ScriptedConfigRepairer(changed=False)

    exit_code = sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
    )

    assert exit_code == 0
    assert config_repairer.calls == 1
    assert runner.calls == list(STEP_ARGVS)


@pytest.mark.parametrize("failing_index", range(len(STEPS)))
def test_changes_present_stops_at_first_failing_step_without_skipping_earlier(
    failing_index: int,
) -> None:
    """A non-zero step return halts the sequence; no step is silently skipped."""
    exit_codes = tuple(0 if i < failing_index else 7 for i in range(len(STEPS)))
    runner = RecordingRunner(exit_codes=exit_codes)
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=True)
    config_repairer = ScriptedConfigRepairer(changed=False)

    exit_code = sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
    )

    assert exit_code == 7
    # Steps before failing_index ran in order; the failing step is the last recorded call.
    expected_argvs = list(STEP_ARGVS[: failing_index + 1])
    assert runner.calls == expected_argvs


def test_sync_declares_codex_local_refresh_step() -> None:
    step_names = tuple(step.name for step in STEPS)

    assert "codex_local_refresh" in step_names
    assert "codex_cache_preserve" not in step_names
