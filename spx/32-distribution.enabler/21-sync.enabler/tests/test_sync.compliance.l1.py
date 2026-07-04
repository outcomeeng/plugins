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

from collections.abc import Sequence

import pytest

import outcomeeng.distribution.sync as sync_module
from outcomeeng.distribution.sync import REQUIRED_TOOLS, STEPS, sync
from outcomeeng_testing.harnesses.sync import (
    RecordingRunner,
    ScriptedChangeProbe,
    ScriptedConfigRepairer,
    ScriptedSingleFlight,
    ScriptedToolProbe,
)

ALL_TOOLS_AVAILABLE = frozenset(REQUIRED_TOOLS)
STEP_ARGVS: tuple[tuple[str, ...], ...] = tuple(step.argv for step in STEPS)
INITIAL_CODEX_LOCAL_REFRESH_STEP = "codex_local_refresh"
FORBIDDEN_CACHE_PRESERVE_STEP = "codex_cache_preserve"
TOOL_EVENT_PREFIX = "tool:"
RUNNER_EVENT = "runner"
CONFIG_EVENT = "config"
CHANGE_EVENT = "change"
ACQUIRE_EVENT = "acquire"
RELEASE_EVENT = "release"


@pytest.mark.parametrize("missing_tool", REQUIRED_TOOLS)
def test_missing_required_tool_fails_fast_with_diagnostic(
    missing_tool: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = RecordingRunner()
    config_repairer = ScriptedConfigRepairer(changed=False)
    events: list[str] = []
    tool_probe = ScriptedToolProbe(
        available=ALL_TOOLS_AVAILABLE - {missing_tool},
    )
    change_probe = _recording_change_probe(events, changed=True)
    single_flight = ScriptedSingleFlight()

    exit_code = sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    assert exit_code != 0
    assert runner.calls == []
    assert config_repairer.calls == 0
    assert events == []
    assert single_flight.acquisitions == 0
    captured = capsys.readouterr()
    assert missing_tool in (captured.err + captured.out)


def test_tool_availability_is_checked_before_orchestration() -> None:
    """Every required tool probe must precede every orchestration boundary."""
    events: list[str] = []
    runner = _RecordingRunnerWithEvents(events)
    tool_probe = _recording_tool_probe(events)
    change_probe = _recording_change_probe(events, changed=True)
    config_repairer = _recording_config_repairer(events, changed=False)
    single_flight = _RecordingSingleFlightWithEvents(events)

    sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    required_tool_events = [f"{TOOL_EVENT_PREFIX}{tool}" for tool in REQUIRED_TOOLS]
    assert events[: len(required_tool_events)] == required_tool_events
    assert set(events[: len(required_tool_events)]) == set(required_tool_events)
    assert all(
        event not in events[: len(required_tool_events)]
        for event in (CONFIG_EVENT, CHANGE_EVENT, ACQUIRE_EVENT, RUNNER_EVENT)
    )
    assert events.index(CONFIG_EVENT) > len(required_tool_events) - 1
    assert events.index(CHANGE_EVENT) > len(required_tool_events) - 1
    assert events.index(ACQUIRE_EVENT) > len(required_tool_events) - 1
    assert events.index(RUNNER_EVENT) > len(required_tool_events) - 1
    assert runner.calls == list(STEP_ARGVS)


def test_source_reconciliation_precedes_distribution_change_probe() -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    single_flight = ScriptedSingleFlight()
    config_event = object()
    change_probe_event = object()
    events: list[object] = []

    def config_repairer() -> bool:
        events.append(config_event)
        return False

    def change_probe(_base_ref: str) -> bool:
        events.append(change_probe_event)
        return True

    sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    assert events == [config_event, change_probe_event]


def test_no_codex_cache_preserve_step_is_declared() -> None:
    step_names = tuple(step.name for step in STEPS)

    assert INITIAL_CODEX_LOCAL_REFRESH_STEP in step_names
    assert FORBIDDEN_CACHE_PRESERVE_STEP not in step_names


def test_changes_present_runs_full_sequence_when_every_step_succeeds() -> None:
    """No silent skip when steps return 0 — every declared step is invoked."""
    runner = RecordingRunner(exit_codes=tuple(0 for _ in STEPS))
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=True)
    config_repairer = ScriptedConfigRepairer(changed=False)
    single_flight = ScriptedSingleFlight()

    exit_code = sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    assert exit_code == 0
    assert config_repairer.calls == 1
    assert single_flight.acquisitions == 1
    assert single_flight.releases == 1
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
    single_flight = ScriptedSingleFlight()

    exit_code = sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    assert exit_code == 7
    assert single_flight.acquisitions == 1
    assert single_flight.releases == 1
    # Steps before failing_index ran in order; the failing step is the last recorded call.
    expected_argvs = list(STEP_ARGVS[: failing_index + 1])
    assert runner.calls == expected_argvs


class _RecordingRunnerWithEvents:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv: Sequence[str]) -> int:
        self.events.append(RUNNER_EVENT)
        self.calls.append(tuple(argv))
        return 0


class _RecordingSingleFlightWithEvents:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def acquire(self) -> sync_module.SingleFlightClaim:
        self.events.append(ACQUIRE_EVENT)
        return sync_module.SingleFlightClaim(acquired=True)

    def release(self) -> None:
        self.events.append(RELEASE_EVENT)


def _recording_tool_probe(events: list[str]) -> sync_module.ToolProbe:
    def tool_probe(name: str) -> bool:
        events.append(f"{TOOL_EVENT_PREFIX}{name}")
        return True

    return tool_probe


def _recording_config_repairer(
    events: list[str],
    *,
    changed: bool,
) -> sync_module.ConfigRepairer:
    def config_repairer() -> bool:
        events.append(CONFIG_EVENT)
        return changed

    return config_repairer


def _recording_change_probe(
    events: list[str],
    *,
    changed: bool,
) -> sync_module.ChangeProbe:
    def change_probe(_base_ref: str) -> bool:
        events.append(CHANGE_EVENT)
        return changed

    return change_probe
