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
from typing import Protocol, cast

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


@dataclass(frozen=True)
class WaitRun:
    """Result plus controlled clock evidence from one waiter invocation."""

    module: ModuleType
    result: WaitResult
    clock: ControlledClock


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


def _run(observations: list[tuple[float, float, float]]) -> WaitRun:
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
    return WaitRun(
        module=module,
        result=cast(WaitResult, module.wait_until_ready(dependencies)),
        clock=clock,
    )


def run_immediate_ready() -> WaitRun:
    """Run one invocation whose initial observation is ready."""
    module = load_host_readiness_module()
    return _run([_ready_load(module)])


def run_ready_before_deadline() -> WaitRun:
    """Run one invocation whose second observation is ready."""
    module = load_host_readiness_module()
    return _run([_high_load(module), _ready_load(module)])


def run_deadline_not_ready() -> WaitRun:
    """Run one invocation whose load stays above capacity through its deadline."""
    module = load_host_readiness_module()
    return _run([_high_load(module)])


def terminal_result_for_status(status: object) -> WaitResult:
    """Build the terminal result the waiter emits for one source-owned status."""
    module = load_host_readiness_module()
    clock = ControlledClock(horizon=module.MAXIMUM_WAIT_SECONDS)
    dependencies = module.Dependencies(
        read_load_averages=lambda: _ready_load(module),
        read_cpu_count=lambda: CPU_COUNT,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )
    return cast(
        WaitResult,
        module.terminal_result(
            status=status,
            dependencies=dependencies,
            started_at=clock.monotonic(),
            initial=None,
            final=None,
            wait_cycles=0,
        ),
    )
