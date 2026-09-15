"""Deterministic harness for the shipped host-readiness waiter.

The waiter lives under a plugin skill directory and is loaded through
``importlib``. A controllable monotonic clock and source-derived load sequences
exercise readiness, bounded sleeping, and terminal status behavior without
wall-clock delay or framework mocking. Every double is injected through the
waiter's own ``Dependencies`` seam; the module under test is never patched.

- Stage 5 #3 (Time and concurrency): `ControlledClock` replaces
  `time.monotonic` and `time.sleep`, and `LoadSequence` scripts the observation
  each recheck reads. The waiter's bounded retry loop is the behavior under
  test, and neither a real four-hour deadline nor real host load is
  controllable or cheap enough to drive it.
- Stage 5 #1 (Failure simulation): the `read_cpu_count` stub returning no
  positive count, the `sleep` callable raising `KeyboardInterrupt`, and the
  `read_load_averages` callable raising produce the `unsupported`,
  `interrupted`, and `error` terminal results. A real host offers no way to
  induce those failures on demand.

The CLI runs drive the waiter's `run` entry with in-memory streams so the
assertion files observe where the terminal document lands without a
subprocess.
"""

from __future__ import annotations

import importlib.util
import io
import math
import pathlib
import sys
from collections.abc import Callable
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

    The horizon is the waiter's own source-declared maximum wait. A waiter that
    never reaches a terminal result would spin forever here, because this clock
    costs no wall-clock time. Two distinct failures produce that spin, and each
    raises on the offending sleep so the test fails immediately and readably
    rather than hanging:

    - sleeping past the horizon, which overshoots the declared deadline; and
    - sleeping a non-positive interval, which advances nothing and so can
      repeat without ever reaching the deadline. A bounded waiter always makes
      progress, so a non-advancing sleep is always a defect.
    """

    horizon: float
    current: float = 0.0
    sleeps: list[float] = field(default_factory=list)

    def monotonic(self) -> float:
        """Return the controlled monotonic time."""
        return self.current

    def sleep(self, seconds: float) -> None:
        """Record and advance by one requested sleep interval."""
        if seconds <= 0:
            raise UnboundedWaiterError(
                f"waiter slept {seconds}s at {self.current}s, advancing nothing "
                f"after {len(self.sleeps)} intervals; it cannot reach its "
                f"{self.horizon}s deadline"
            )
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
    """Result plus controlled clock and observation evidence from one waiter invocation."""

    module: ModuleType
    result: WaitResult
    clock: ControlledClock
    sequence: LoadSequence


@dataclass(frozen=True)
class CliRun:
    """Exit code and captured streams from one waiter CLI invocation."""

    module: ModuleType
    exit_code: int
    stdout: str
    stderr: str


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


def _ready_rising_load(module: ModuleType) -> tuple[float, float, float]:
    """Build a ready observation whose one-minute load has just risen.

    The five- and fifteen-minute loads sit at zero and the one-minute load
    sits the smallest step past the source-owned trend tolerance, so every
    average stays at or below capacity while the trend reads as rising.
    """
    return (math.nextafter(module.TREND_TOLERANCE_LOAD, math.inf), 0.0, 0.0)


def _load_demanding_more_than_the_deadline(
    module: ModuleType,
) -> tuple[float, float, float]:
    """Build an observation whose computed interval exceeds the whole deadline.

    The waiter derives its interval from `horizon * log(ratio)` over the
    longest load horizon, so a ratio of `exp(MAXIMUM_WAIT_SECONDS / horizon)`
    computes exactly the deadline. Doubling that exponent computes twice the
    deadline, which is what forces the waiter to clamp its sleep to the time
    remaining. Deriving the ratio keeps it beyond the deadline if either
    source constant changes.
    """
    longest_horizon = max(module.LOAD_HORIZONS_SECONDS)
    exponent = 2 * module.MAXIMUM_WAIT_SECONDS / longest_horizon
    return _load_at_ratio(module.CAPACITY_RATIO * math.exp(exponent))


def _run(
    observations: list[tuple[float, float, float]],
    *,
    read_cpu_count: Callable[[], int | None] | None = None,
    read_load_averages: Callable[[], tuple[float, float, float]] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> WaitRun:
    """Run the waiter against controlled observations and monotonic time.

    Each keyword replaces one injected dependency so a caller can drive the
    waiter down a failure path — an unusable CPU count, an interrupt during a
    wait interval, or a load reader that raises — without patching the module.
    """
    module = load_host_readiness_module()
    clock = ControlledClock(horizon=module.MAXIMUM_WAIT_SECONDS)
    sequence = LoadSequence(observations)
    dependencies = module.Dependencies(
        read_load_averages=read_load_averages or sequence.read,
        read_cpu_count=read_cpu_count or (lambda: CPU_COUNT),
        monotonic=clock.monotonic,
        sleep=sleep or clock.sleep,
    )
    return WaitRun(
        module=module,
        result=cast(WaitResult, module.wait_until_ready(dependencies)),
        clock=clock,
        sequence=sequence,
    )


def _run_cli(
    observations: list[tuple[float, float, float]],
    *,
    read_cpu_count: Callable[[], int | None] | None = None,
    read_load_averages: Callable[[], tuple[float, float, float]] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> CliRun:
    """Run the waiter's CLI entry against controlled dependencies and streams."""
    module = load_host_readiness_module()
    clock = ControlledClock(horizon=module.MAXIMUM_WAIT_SECONDS)
    sequence = LoadSequence(observations)
    dependencies = module.Dependencies(
        read_load_averages=read_load_averages or sequence.read,
        read_cpu_count=read_cpu_count or (lambda: CPU_COUNT),
        monotonic=clock.monotonic,
        sleep=sleep or clock.sleep,
    )
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = module.run([], dependencies, stdout, stderr)
    return CliRun(
        module=module,
        exit_code=exit_code,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
    )


def run_immediate_ready() -> WaitRun:
    """Run one invocation whose initial observation is ready."""
    module = load_host_readiness_module()
    return _run([_ready_load(module)])


def run_ready_before_deadline() -> WaitRun:
    """Run one invocation whose second observation is ready."""
    module = load_host_readiness_module()
    return _run([_high_load(module), _ready_load(module)])


def run_ready_confirmed_after_wait() -> WaitRun:
    """Run one invocation that waits once, then confirms readiness after settling."""
    module = load_host_readiness_module()
    return _run([_high_load(module), _ready_load(module), _ready_load(module)])


def run_rising_confirmation_then_ready() -> WaitRun:
    """Run one invocation whose first confirmation reads a rising trend.

    The sequence waits once, observes readiness, confirms against a rising
    observation, returns to the loop, observes readiness again, and confirms
    against a level observation.
    """
    module = load_host_readiness_module()
    return _run(
        [
            _high_load(module),
            _ready_load(module),
            _ready_rising_load(module),
            _ready_load(module),
            _ready_load(module),
        ]
    )


def run_deadline_not_ready() -> WaitRun:
    """Run one invocation whose load stays above capacity through its deadline."""
    module = load_host_readiness_module()
    return _run([_high_load(module)])


def run_interval_clamped_to_remaining() -> WaitRun:
    """Run one invocation whose computed interval outruns the time remaining."""
    module = load_host_readiness_module()
    return _run([_load_demanding_more_than_the_deadline(module)])


def run_unsupported_platform() -> WaitRun:
    """Run one invocation on a host reporting no positive CPU count."""
    module = load_host_readiness_module()
    return _run([_ready_load(module)], read_cpu_count=lambda: None)


def run_interrupted_during_wait() -> WaitRun:
    """Run one invocation interrupted while sleeping between observations."""
    module = load_host_readiness_module()

    def interrupt(seconds: float) -> None:
        raise KeyboardInterrupt

    return _run([_high_load(module)], sleep=interrupt)


def run_error_reading_load() -> WaitRun:
    """Run one invocation whose load reader fails unexpectedly."""
    module = load_host_readiness_module()

    def fail() -> tuple[float, float, float]:
        raise RuntimeError("load averages unavailable")

    return _run([_ready_load(module)], read_load_averages=fail)


def run_cli_for_status(status: object) -> CliRun:
    """Run the CLI entry under the controlled dependencies that reach one terminal status.

    Each status is driven by the same dependency shape the wait runs above use
    for it, so the CLI evidence observes stream placement for every terminal
    outcome the source enumerates.
    """
    module = load_host_readiness_module()

    def interrupt(seconds: float) -> None:
        raise KeyboardInterrupt

    def fail() -> tuple[float, float, float]:
        raise RuntimeError("load averages unavailable")

    if status is module.Status.READY:
        return _run_cli([_ready_load(module)])
    if status is module.Status.NOT_READY:
        return _run_cli([_high_load(module)])
    if status is module.Status.UNSUPPORTED:
        return _run_cli([_ready_load(module)], read_cpu_count=lambda: None)
    if status is module.Status.INTERRUPTED:
        return _run_cli([_high_load(module)], sleep=interrupt)
    if status is module.Status.ERROR:
        return _run_cli([_ready_load(module)], read_load_averages=fail)
    raise ValueError(f"no controlled drive reaches status {status!r}")
