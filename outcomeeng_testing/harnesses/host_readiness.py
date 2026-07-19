"""Deterministic harness for the shipped host-readiness waiter.

The waiter lives under a plugin skill directory and is loaded through
``importlib``. A controllable monotonic clock and source-derived load sequences
exercise readiness, bounded sleeping, and terminal status behavior without
wall-clock delay or framework mocking.
"""

from __future__ import annotations

import importlib.util
import math
import pathlib
import sys
from dataclasses import dataclass, field
from types import ModuleType
from typing import Final, Protocol, cast

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST_READINESS_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "wait-for-load"
    / "scripts"
    / "wait_for_load.py"
)
MODULE_NAME = "wait_for_load"
CPU_COUNT = 1


def load_host_readiness_module() -> ModuleType:
    """Load and cache the shipped host-readiness module."""
    cached = sys.modules.get(MODULE_NAME)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        MODULE_NAME, HOST_READINESS_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load host-readiness module from {HOST_READINESS_MODULE_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


class UnboundedWaiterError(AssertionError):
    """Raised when a waiter sleeps past the deadline its source declares."""


@dataclass
class ControlledClock:
    """Monotonic clock whose sleep advances deterministically within a horizon.

    The horizon is the waiter's own source-declared maximum wait. Advancing
    past it means the waiter under exercise never reaches a terminal result,
    and because this clock costs no wall-clock time such a waiter would spin
    until it exhausts host memory. Failing on the first sleep beyond the
    horizon converts that exhaustion into an immediate, readable failure.
    """

    horizon: float
    current: float = 0.0
    sleeps: list[float] = field(default_factory=list)

    def monotonic(self) -> float:
        """Return the controlled monotonic time."""
        return self.current

    def sleep(self, seconds: float) -> None:
        """Record and advance by one requested sleep interval."""
        if self.current + seconds > self.horizon:
            raise UnboundedWaiterError(
                f"waiter slept to {self.current + seconds}s past its "
                f"{self.horizon}s deadline after {len(self.sleeps)} intervals"
            )
        self.sleeps.append(seconds)
        self.current += seconds


@dataclass
class LoadSequence:
    """Load reader that advances through observations and repeats the last."""

    observations: list[tuple[float, float, float]]
    index: int = 0

    def read(self) -> tuple[float, float, float]:
        """Return the next observation or repeat the final observation."""
        position = min(self.index, len(self.observations) - 1)
        self.index += 1
        return self.observations[position]


class WaitResult(Protocol):
    """Observable terminal result contract consumed by assertion files."""

    status: object
    ready: bool
    final: object | None
    wait_cycles: int
    waited_seconds: float

    @property
    def exit_code(self) -> int:
        """Return the result's terminal exit code as an int-valued enum member."""
        ...


class StatusValue(Protocol):
    """Observable enum-member contract used by the mapping evidence."""

    name: str
    value: str


READY_STATUS: Final = "ready"
NOT_READY_STATUS: Final = "not_ready"

DECLARED_TERMINAL_CONTRACT: Final[dict[str, tuple[bool, int]]] = {
    READY_STATUS: (True, 0),
    "error": (False, 1),
    "unsupported": (False, 2),
    NOT_READY_STATUS: (False, 3),
    "interrupted": (False, 130),
}
"""Readiness and process exit code the node spec declares for each status.

This table restates the declaration rather than importing the waiter's own
enums, so it is an oracle independent of the module under test. Comparing a
result against the module's own `ExitCode` members cannot fail when those
members are renumbered; comparing against this table can. The exit code is a
process-level contract read by callers that never import the module, so a
renumbering is a breaking change these values exist to catch.
"""


@dataclass(frozen=True)
class WaitRun:
    """Result plus controlled clock evidence from one waiter invocation."""

    module: ModuleType
    result: WaitResult
    clock: ControlledClock
    declared_ready: bool
    declared_exit_code: int


def _load_at_ratio(ratio: float) -> tuple[float, float, float]:
    """Build one three-horizon load observation at a normalized ratio."""
    load = ratio * CPU_COUNT
    return (load, load, load)


def _ready_load(module: ModuleType) -> tuple[float, float, float]:
    """Build an observation exactly at the source-owned readiness boundary."""
    return _load_at_ratio(module.CAPACITY_RATIO)


def _high_load(module: ModuleType) -> tuple[float, float, float]:
    """Build the smallest observation above the readiness boundary."""
    return _load_at_ratio(math.nextafter(module.CAPACITY_RATIO, math.inf))


def _run(
    observations: list[tuple[float, float, float]], declared_status: str
) -> WaitRun:
    """Run the waiter against controlled observations and monotonic time."""
    module = load_host_readiness_module()
    clock = ControlledClock(horizon=module.MAXIMUM_WAIT_SECONDS)
    sequence = LoadSequence(observations)
    dependencies = module.Dependencies(
        read_load_averages=sequence.read,
        read_cpu_count=lambda: CPU_COUNT,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )
    declared_ready, declared_exit_code = DECLARED_TERMINAL_CONTRACT[declared_status]
    return WaitRun(
        module=module,
        result=cast(WaitResult, module.wait_until_ready(dependencies)),
        clock=clock,
        declared_ready=declared_ready,
        declared_exit_code=declared_exit_code,
    )


def run_immediate_ready() -> WaitRun:
    """Run one invocation whose initial observation is ready."""
    module = load_host_readiness_module()
    return _run([_ready_load(module)], READY_STATUS)


def run_ready_before_deadline() -> WaitRun:
    """Run one invocation whose second observation is ready."""
    module = load_host_readiness_module()
    return _run([_high_load(module), _ready_load(module)], READY_STATUS)


def run_deadline_not_ready() -> WaitRun:
    """Run one invocation whose load stays above capacity through its deadline."""
    module = load_host_readiness_module()
    return _run([_high_load(module)], NOT_READY_STATUS)


def terminal_result_for(status: StatusValue) -> WaitRun:
    """Build a terminal result for one source-owned status."""
    module = load_host_readiness_module()
    clock = ControlledClock(horizon=module.MAXIMUM_WAIT_SECONDS)
    declared_ready, declared_exit_code = DECLARED_TERMINAL_CONTRACT[str(status.value)]
    dependencies = module.Dependencies(
        read_load_averages=lambda: _ready_load(module),
        read_cpu_count=lambda: CPU_COUNT,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )
    return WaitRun(
        module=module,
        result=cast(
            WaitResult,
            module.terminal_result(
                status=status,
                dependencies=dependencies,
                started_at=clock.monotonic(),
                initial=None,
                final=None,
                wait_cycles=0,
            ),
        ),
        clock=clock,
        declared_ready=declared_ready,
        declared_exit_code=declared_exit_code,
    )


def terminal_status_mapping_holds() -> bool:
    """Verify every status carries the readiness and exit code the spec declares."""
    module = load_host_readiness_module()
    statuses = set(module.Status)
    if statuses != set(module.STATUS_EXIT_CODES) or statuses != set(
        module.STATUS_READINESS
    ):
        return False
    if {str(status.value) for status in statuses} != set(DECLARED_TERMINAL_CONTRACT):
        return False
    for status in statuses:
        run = terminal_result_for(cast(StatusValue, status))
        if run.result.ready is not run.declared_ready:
            return False
        if int(run.result.exit_code) != run.declared_exit_code:
            return False
    return True
