#!/usr/bin/env python3
"""Wait silently until all normalized host load averages are at or below capacity.

One invocation owns the whole readiness attempt: it observes, sleeps, rechecks,
confirms readiness after a settle delay, and writes exactly one terminal JSON
document to standard error so a command chained after it with ``&&`` starts
only on a zero exit.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum, IntEnum, StrEnum
from typing import Final, TextIO

LoadAverages = tuple[float, float, float]

CAPACITY_RATIO: Final = 1.0
MINIMUM_WAIT_SECONDS: Final = 60
MAXIMUM_WAIT_SECONDS: Final = 14400
SETTLE_WINDOW_SECONDS: Final = 180
TREND_TOLERANCE_LOAD: Final = 0.5
LOAD_HORIZONS_SECONDS: Final[LoadAverages] = (60.0, 300.0, 900.0)


class Status(str, Enum):
    """Terminal waiter states exposed in the JSON result."""

    READY = "ready"
    NOT_READY = "not_ready"
    UNSUPPORTED = "unsupported"
    INTERRUPTED = "interrupted"
    ERROR = "error"


class ExitCode(IntEnum):
    """Process exit codes for each terminal waiter state."""

    READY = 0
    ERROR = 1
    UNSUPPORTED = 2
    NOT_READY = 3
    INTERRUPTED = 130


STATUS_EXIT_CODES: Final = {
    Status.READY: ExitCode.READY,
    Status.ERROR: ExitCode.ERROR,
    Status.UNSUPPORTED: ExitCode.UNSUPPORTED,
    Status.NOT_READY: ExitCode.NOT_READY,
    Status.INTERRUPTED: ExitCode.INTERRUPTED,
}
STATUS_READINESS: Final = {status: status is Status.READY for status in Status}


class ObservationField(StrEnum):
    """Field names of one observation inside the terminal document."""

    LOAD = "load"
    CPU_COUNT = "cpu_count"
    NORMALIZED = "normalized"


class ErrorField(StrEnum):
    """Field names of the error object inside the terminal document."""

    TYPE = "type"
    MESSAGE = "message"


class ResultField(StrEnum):
    """Top-level field names of the terminal document."""

    STATUS = "status"
    READY = "ready"
    INITIAL = "initial"
    FINAL = "final"
    WAIT_CYCLES = "wait_cycles"
    WAITED_SECONDS = "waited_seconds"
    ERROR = "error"


class UnsupportedPlatformError(RuntimeError):
    """Raised when the host cannot provide a valid load observation."""


@dataclass(frozen=True)
class Observation:
    """One host-load observation normalized by logical CPU count."""

    load: LoadAverages
    cpu_count: int
    normalized: LoadAverages

    def as_dict(self) -> dict[str, object]:
        """Return the stable JSON representation of this observation."""
        return {
            ObservationField.LOAD: list(self.load),
            ObservationField.CPU_COUNT: self.cpu_count,
            ObservationField.NORMALIZED: list(self.normalized),
        }


@dataclass(frozen=True)
class Dependencies:
    """Boundaries that make load and time behavior deterministic to exercise."""

    read_load_averages: Callable[[], LoadAverages]
    read_cpu_count: Callable[[], int | None]
    monotonic: Callable[[], float]
    sleep: Callable[[float], None]


@dataclass(frozen=True)
class Result:
    """The terminal machine-readable waiter result."""

    status: Status
    ready: bool
    initial: Observation | None
    final: Observation | None
    wait_cycles: int
    waited_seconds: float
    error_type: str | None = None
    error_message: str | None = None

    @property
    def exit_code(self) -> ExitCode:
        """Map the terminal status to its process exit code."""
        return STATUS_EXIT_CODES[self.status]

    def as_dict(self) -> dict[str, object]:
        """Return the stable terminal JSON document."""
        payload: dict[str, object] = {
            ResultField.STATUS: self.status,
            ResultField.READY: self.ready,
            ResultField.INITIAL: (
                self.initial.as_dict() if self.initial is not None else None
            ),
            ResultField.FINAL: self.final.as_dict() if self.final is not None else None,
            ResultField.WAIT_CYCLES: self.wait_cycles,
            ResultField.WAITED_SECONDS: self.waited_seconds,
        }
        if self.error_type is not None:
            payload[ResultField.ERROR] = {
                ErrorField.TYPE: self.error_type,
                ErrorField.MESSAGE: self.error_message,
            }
        return payload


def read_system_load_averages() -> LoadAverages:
    """Read load averages or report that the platform lacks the API."""
    try:
        load = os.getloadavg()
    except (AttributeError, OSError) as error:
        raise UnsupportedPlatformError("os.getloadavg() is unavailable") from error
    return (float(load[0]), float(load[1]), float(load[2]))


def observe(dependencies: Dependencies) -> Observation:
    """Read and validate one normalized host-load observation."""
    cpu_count = dependencies.read_cpu_count()
    if cpu_count is None or cpu_count <= 0:
        raise UnsupportedPlatformError("os.cpu_count() returned no positive CPU count")

    load = dependencies.read_load_averages()
    if len(load) != len(LOAD_HORIZONS_SECONDS):
        raise UnsupportedPlatformError(
            "load average observation must contain three values"
        )
    if any(value < 0 or not math.isfinite(value) for value in load):
        raise UnsupportedPlatformError(
            "load averages must be finite non-negative values"
        )

    normalized = tuple(value / cpu_count for value in load)
    return Observation(
        load=load,
        cpu_count=cpu_count,
        normalized=(normalized[0], normalized[1], normalized[2]),
    )


def is_ready(observation: Observation) -> bool:
    """Return whether every normalized average is at or below capacity."""
    return all(value <= CAPACITY_RATIO for value in observation.normalized)


def is_rising(observation: Observation) -> bool:
    """Return whether the one-minute load exceeds the five-minute load by more than the tolerance."""
    one_minute, five_minute, _ = observation.load
    return one_minute > five_minute + TREND_TOLERANCE_LOAD


def settle_seconds(elapsed: float) -> float:
    """Return the settle delay the elapsed wait selects: elapsed modulo the settle window."""
    return elapsed % SETTLE_WINDOW_SECONDS


def wait_seconds(observation: Observation) -> int:
    """Calculate the next load-aware wait from all over-capacity averages."""
    estimates = tuple(
        horizon * math.log(value / CAPACITY_RATIO)
        for value, horizon in zip(
            observation.normalized,
            LOAD_HORIZONS_SECONDS,
        )
        if value > CAPACITY_RATIO
    )
    if not estimates:
        return MINIMUM_WAIT_SECONDS
    return max(MINIMUM_WAIT_SECONDS, math.ceil(max(estimates)))


def elapsed_seconds(dependencies: Dependencies, started_at: float) -> float:
    """Return non-negative elapsed monotonic time with millisecond precision."""
    return round(max(0.0, dependencies.monotonic() - started_at), 3)


def terminal_result(
    *,
    status: Status,
    dependencies: Dependencies,
    started_at: float,
    initial: Observation | None,
    final: Observation | None,
    wait_cycles: int,
    error: BaseException | None = None,
) -> Result:
    """Build one terminal result without retaining intermediate observations."""
    return Result(
        status=status,
        ready=STATUS_READINESS[status],
        initial=initial,
        final=final,
        wait_cycles=wait_cycles,
        waited_seconds=elapsed_seconds(dependencies, started_at),
        error_type=type(error).__name__ if error is not None else None,
        error_message=str(error) if error is not None else None,
    )


def confirm_after_settling(
    dependencies: Dependencies,
    started_at: float,
) -> tuple[Observation, bool]:
    """Settle, observe once more, and report whether that observation confirms readiness.

    The settle delay is the elapsed wait modulo the settle window, clamped to
    the time remaining, so waiters that arrived at different moments start at
    different moments. The confirming observation must sit at or below capacity
    with a one-minute load that has not risen past the five-minute load by more
    than the trend tolerance; a rising trend means other work just started, and
    the caller returns to its wait loop.
    """
    elapsed = elapsed_seconds(dependencies, started_at)
    delay = min(settle_seconds(elapsed), MAXIMUM_WAIT_SECONDS - elapsed)
    if delay > 0:
        dependencies.sleep(delay)
    observation = observe(dependencies)
    return observation, is_ready(observation) and not is_rising(observation)


def wait_until_ready(dependencies: Dependencies) -> Result:
    """Own observation, sleeping, settling, and confirming until a terminal result exists."""
    started_at = dependencies.monotonic()
    initial: Observation | None = None
    final: Observation | None = None
    wait_cycles = 0

    try:
        final = observe(dependencies)
        initial = final
        while True:
            if is_ready(final):
                if wait_cycles == 0:
                    break
                final, confirmed = confirm_after_settling(dependencies, started_at)
                if confirmed:
                    break
            remaining = MAXIMUM_WAIT_SECONDS - elapsed_seconds(dependencies, started_at)
            if remaining <= 0:
                return terminal_result(
                    status=Status.NOT_READY,
                    dependencies=dependencies,
                    started_at=started_at,
                    initial=initial,
                    final=final,
                    wait_cycles=wait_cycles,
                )
            wait_cycles += 1
            dependencies.sleep(min(wait_seconds(final), remaining))
            final = observe(dependencies)
    except UnsupportedPlatformError as error:
        return terminal_result(
            status=Status.UNSUPPORTED,
            dependencies=dependencies,
            started_at=started_at,
            initial=initial,
            final=final,
            wait_cycles=wait_cycles,
            error=error,
        )
    except KeyboardInterrupt as error:
        return terminal_result(
            status=Status.INTERRUPTED,
            dependencies=dependencies,
            started_at=started_at,
            initial=initial,
            final=final,
            wait_cycles=wait_cycles,
            error=error,
        )
    except Exception as error:  # noqa: BLE001 - terminal CLI contract reports failures as JSON
        return terminal_result(
            status=Status.ERROR,
            dependencies=dependencies,
            started_at=started_at,
            initial=initial,
            final=final,
            wait_cycles=wait_cycles,
            error=error,
        )

    return terminal_result(
        status=Status.READY,
        dependencies=dependencies,
        started_at=started_at,
        initial=initial,
        final=final,
        wait_cycles=wait_cycles,
    )


def encode_result(result: Result) -> str:
    """Encode exactly one compact standards-compliant JSON document."""
    return json.dumps(
        result.as_dict(),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def run(
    arguments: Sequence[str],
    dependencies: Dependencies,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Run one readiness attempt and write its sole terminal document to stderr."""
    if arguments:
        started_at = dependencies.monotonic()
        error = ValueError(
            "wait_for_load.py accepts no arguments; received "
            f"{json.dumps(list(arguments))}"
        )
        result = terminal_result(
            status=Status.ERROR,
            dependencies=dependencies,
            started_at=started_at,
            initial=None,
            final=None,
            wait_cycles=0,
            error=error,
        )
    else:
        result = wait_until_ready(dependencies)
    stderr.write(f"{encode_result(result)}\n")
    stderr.flush()
    stdout.flush()
    return int(result.exit_code)


def main() -> int:
    """Bind the real host, clock, and streams and run the waiter."""
    dependencies = Dependencies(
        read_load_averages=read_system_load_averages,
        read_cpu_count=os.cpu_count,
        monotonic=time.monotonic,
        sleep=time.sleep,
    )
    return run(sys.argv[1:], dependencies, sys.stdout, sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
