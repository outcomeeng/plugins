"""Recording doubles for the sync orchestrator.

Implements the `StepRunner`, `ToolProbe`, and `ChangeProbe` Protocols
declared in `outcomeeng.distribution.sync`. The doubles are spies
(recording calls) and stubs (returning scripted results), used by `l1`
tests to verify sync's orchestration without invoking real subprocesses
or mutating marketplace state.

Exception cases per `plugins/spec-tree/skills/test/references/methodology.md`:
- Stage 5 #2 (Interaction protocols): sync's correctness depends on the
  sequence and presence of step calls.
- Stage 5 #4 (Safety): real sync mutates the marketplace cache and shells
  out to network-bound tooling.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from outcomeeng.distribution.sync import (
    ChangeProbe,
    ConfigRepairer,
    REQUIRED_TOOLS,
    SingleFlight,
    SingleFlightClaim,
    StepRunner,
    sync,
    TopologyHealthProbe,
    ToolProbe,
)

CHANGE_PROBE_EVENT = "change_probe"
CONFIG_REPAIR_EVENT = "config_repair"
RUNNER_EVENT = "runner"
TOOL_PROBE_EVENT_PREFIX = "tool_probe:"
SCRIPTED_BASE_REF = "abc123"
DEFAULT_TOPOLOGY_ERRORS = ("missing target",)


@dataclass
class RecordingRunner:
    """StepRunner that returns scripted exit codes in order of call.

    `exit_codes` drives the i-th call's return value (default 0 once exhausted).
    `calls` records the argv tuple of each call in order.
    """

    exit_codes: Sequence[int] = ()
    calls: list[tuple[str, ...]] = field(default_factory=list)
    events: list[str] | None = None

    def __call__(self, argv: Sequence[str]) -> int:
        if self.events is not None:
            self.events.append(RUNNER_EVENT)
        index = len(self.calls)
        self.calls.append(tuple(argv))
        if index < len(self.exit_codes):
            return self.exit_codes[index]
        return 0


@dataclass
class ScriptedToolProbe:
    """ToolProbe that returns True only for tools in `available`."""

    available: frozenset[str]
    queries: list[str] = field(default_factory=list)
    events: list[str] | None = None

    def __call__(self, name: str) -> bool:
        if self.events is not None:
            self.events.append(f"{TOOL_PROBE_EVENT_PREFIX}{name}")
        self.queries.append(name)
        return name in self.available


@dataclass
class ScriptedChangeProbe:
    """ChangeProbe that returns `changed` for every query."""

    changed: bool
    queries: list[str] = field(default_factory=list)
    events: list[str] | None = None

    def __call__(self, base_ref: str) -> bool:
        if self.events is not None:
            self.events.append(CHANGE_PROBE_EVENT)
        self.queries.append(base_ref)
        return self.changed


@dataclass
class ScriptedConfigRepairer:
    """ConfigRepairer that reports whether runtime source config changed."""

    changed: bool
    calls: int = 0
    events: list[str] | None = None

    def __call__(self) -> bool:
        if self.events is not None:
            self.events.append(CONFIG_REPAIR_EVENT)
        self.calls += 1
        return self.changed


@dataclass
class ScriptedTopologyProbe:
    """TopologyHealthProbe returning scripted topology errors or raising."""

    errors: tuple[str, ...] = ()
    error: Exception | None = None
    calls: int = 0

    def __call__(self) -> tuple[str, ...]:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.errors


@dataclass
class ScriptedSingleFlight:
    """SingleFlight double that records acquisition and release calls."""

    claim: SingleFlightClaim = SingleFlightClaim(acquired=True)
    release_error: OSError | None = None
    acquisitions: int = 0
    releases: int = 0

    def acquire(self) -> SingleFlightClaim:
        self.acquisitions += 1
        return self.claim

    def release(self) -> None:
        self.releases += 1
        if self.release_error is not None:
            raise self.release_error


@dataclass(frozen=True)
class ScriptedSyncRun:
    """Captured result and collaborators from one scripted sync invocation."""

    exit_code: int
    runner: RecordingRunner
    tool_probe: ScriptedToolProbe
    change_probe: ScriptedChangeProbe
    config_repairer: ScriptedConfigRepairer
    topology_probe: ScriptedTopologyProbe

    @property
    def observed_no_change_invalid_topology_probe(self) -> bool:
        return (
            self.config_repairer.calls == 1
            and self.change_probe.queries == [SCRIPTED_BASE_REF]
            and self.topology_probe.calls == 1
        )


def run_invalid_topology_refresh(
    single_flight: SingleFlight,
    *,
    topology_errors: tuple[str, ...] = DEFAULT_TOPOLOGY_ERRORS,
) -> ScriptedSyncRun:
    """Run sync through the no-change invalid-topology refresh path."""

    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=frozenset(REQUIRED_TOOLS))
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)
    topology_probe = ScriptedTopologyProbe(errors=topology_errors)
    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        topology_probe=topology_probe,
        single_flight=single_flight,
    )
    return ScriptedSyncRun(
        exit_code=exit_code,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        topology_probe=topology_probe,
    )


__all__ = [
    "CHANGE_PROBE_EVENT",
    "CONFIG_REPAIR_EVENT",
    "RUNNER_EVENT",
    "DEFAULT_TOPOLOGY_ERRORS",
    "RecordingRunner",
    "ScriptedChangeProbe",
    "ScriptedConfigRepairer",
    "ScriptedSingleFlight",
    "ScriptedSyncRun",
    "ScriptedTopologyProbe",
    "ScriptedToolProbe",
    "TOOL_PROBE_EVENT_PREFIX",
    "run_invalid_topology_refresh",
]


_: type[StepRunner] = RecordingRunner
_2: type[ToolProbe] = ScriptedToolProbe
_3: type[ChangeProbe] = ScriptedChangeProbe
_4: type[ConfigRepairer] = ScriptedConfigRepairer
_5: type[TopologyHealthProbe] = ScriptedTopologyProbe
_6: type[SingleFlight] = ScriptedSingleFlight
