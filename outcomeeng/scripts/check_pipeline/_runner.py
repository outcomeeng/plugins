"""Orchestration loop and signal-forwarding handler for the check pipeline.

`run()` is the entry point: it iterates the declared steps, prints labeled
headers and a final timing summary, and forwards SIGTERM/SIGINT/SIGHUP to
the currently-running child's process group via a top-level signal handler
that closes over a module-level reference.

The signal handler uses a single `time.monotonic()` deadline to bound the
SIGKILL grace window — the only polling wait in the package, carved out by
the ADR's bounded-deadline exception.
"""

from __future__ import annotations

import signal
import time
from collections.abc import Sequence
from types import FrameType
from typing import Final, TextIO

from outcomeeng.scripts.check_pipeline._model import ProcessHandle, ProcessSpawner, Step

_FORWARDED_SIGNALS: Final = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
_GRACE_SECONDS: Final = 2.0
_POLL_INTERVAL: Final = 0.05

_current_handle_ref: list[ProcessHandle | None] = [None]


def _forwarding_signal_handler(signum: int, _frame: FrameType | None) -> None:
    """Forward the received signal to the current child's process group.

    Sends SIGTERM first, polls up to `_GRACE_SECONDS` against a single
    monotonic deadline, then escalates to SIGKILL if the child is still
    alive. Exits the orchestrator with `128 + signum` in every case.
    """
    handle = _current_handle_ref[0]
    if handle is None:
        raise SystemExit(128 + signum)
    if handle.poll() is not None:
        raise SystemExit(128 + signum)
    handle.send_signal_to_group(signal.SIGTERM)
    deadline = time.monotonic() + _GRACE_SECONDS
    while time.monotonic() < deadline:
        if handle.poll() is not None:
            raise SystemExit(128 + signum)
        time.sleep(_POLL_INTERVAL)
    handle.send_signal_to_group(signal.SIGKILL)
    raise SystemExit(128 + signum)


def _write_summary(
    sink: TextIO,
    timings: Sequence[tuple[str, int]],
    *,
    total: int | None = None,
    failed_label: str | None = None,
) -> None:
    sink.write("\n━━━ Timing Summary ━━━\n")
    for label, elapsed in timings:
        sink.write(f"  {label:<20} {elapsed:>3}s\n")
    sink.write("  ────────────────────────\n")
    if total is not None:
        sink.write(f"  {'TOTAL':<20} {total:>3}s\n")
    if failed_label is not None:
        sink.write(f"  {'FAILED':<20} {failed_label}\n")
    sink.flush()


def run(
    spawner: ProcessSpawner,
    sink: TextIO,
    steps: Sequence[Step],
) -> int:
    """Run each step in order; stop at the first failure; print summary.

    Returns 0 on full pass, or the failing step's exit code on first failure.
    Signal delivery during a step raises SystemExit(128 + signum) from the
    handler — this propagates through the caller's `sys.exit(run(...))`.
    """
    old_handlers: dict[int, signal._HANDLER] = {}
    for sig in _FORWARDED_SIGNALS:
        old_handlers[sig] = signal.signal(sig, _forwarding_signal_handler)

    timings: list[tuple[str, int]] = []
    failed_step: Step | None = None
    failed_status = 0
    total_start = time.monotonic()
    try:
        for step in steps:
            sink.write(f"━━━ {step.label} ━━━\n")
            sink.flush()
            step_start = time.monotonic()
            handle = spawner.spawn(step.argv)
            _current_handle_ref[0] = handle
            try:
                status = handle.wait()
            finally:
                _current_handle_ref[0] = None
            elapsed = round(time.monotonic() - step_start)
            timings.append((step.label, elapsed))
            if status != 0:
                failed_step = step
                failed_status = status
                break
        if failed_step is None:
            total = round(time.monotonic() - total_start)
            _write_summary(sink, timings, total=total)
            return 0
        _write_summary(sink, timings, failed_label=failed_step.label)
        return failed_status
    finally:
        for sig, old in old_handlers.items():
            signal.signal(sig, old)
