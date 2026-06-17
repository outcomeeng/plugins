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
import tempfile
import time
from collections import deque
from collections.abc import Sequence
from pathlib import Path
from types import FrameType
from typing import Final, TextIO

from outcomeeng.validation._model import ProcessHandle, ProcessSpawner, Step

_FORWARDED_SIGNALS: Final = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
_GRACE_SECONDS: Final = 2.0
_POLL_INTERVAL: Final = 0.05
_POST_KILL_REAP_ATTEMPTS: Final = 20
LOG_FILE_PREFIX: Final = "outcomeeng-validation-"
LOG_FILE_SUFFIX: Final = ".log"
STEP_PASS_STATUS: Final = "PASS"
STEP_FAIL_STATUS: Final = "FAIL"
FULL_LOG_LABEL: Final = "Full log:"
FAILURE_EXCERPT_LINE_LIMIT: Final = 80
FAILURE_EXCERPT_CHAR_LIMIT: Final = 12_000

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
    for _ in range(_POST_KILL_REAP_ATTEMPTS):
        if handle.poll() is not None:
            break
        time.sleep(_POLL_INTERVAL)
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


def _safe_log_slug(label: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in label)
    return "-".join(part for part in slug.split("-") if part) or "step"


def _create_log_path(step_index: int, label: str) -> Path:
    slug = _safe_log_slug(label)
    with tempfile.NamedTemporaryFile(
        prefix=f"{LOG_FILE_PREFIX}{step_index:02d}-{slug}-",
        suffix=LOG_FILE_SUFFIX,
        delete=False,
    ) as output:
        return Path(output.name)


def _discard_log(log_path: Path) -> None:
    try:
        log_path.unlink()
    except FileNotFoundError:
        return


def _read_failure_excerpt(log_path: Path) -> str:
    lines: deque[str] = deque(maxlen=FAILURE_EXCERPT_LINE_LIMIT)
    line_count = 0
    try:
        with log_path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line_count += 1
                lines.append(line.rstrip("\n"))
    except OSError as exc:
        return f"<failed to read log: {exc}>"

    visible = list(lines)
    omitted = line_count - len(visible)
    if omitted > 0:
        visible.insert(0, f"... {omitted} earlier log lines omitted ...")
    excerpt = "\n".join(visible)
    if len(excerpt) <= FAILURE_EXCERPT_CHAR_LIMIT:
        return excerpt
    hidden_chars = len(excerpt) - FAILURE_EXCERPT_CHAR_LIMIT
    return (
        f"... {hidden_chars} earlier log characters omitted ...\n"
        f"{excerpt[-FAILURE_EXCERPT_CHAR_LIMIT:]}"
    )


def _write_failure_details(
    sink: TextIO,
    *,
    step: Step,
    status: int,
    elapsed: int,
    log_path: Path,
) -> None:
    sink.write(f"{STEP_FAIL_STATUS}  {step.label}  {elapsed}s  exit {status}\n")
    excerpt = _read_failure_excerpt(log_path)
    if excerpt:
        sink.write(f"━━━ {step.label} failure excerpt ━━━\n")
        sink.write(f"{excerpt}\n")
    sink.write(f"{FULL_LOG_LABEL} {log_path}\n")
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
    old_handlers: dict[signal.Signals, signal._HANDLER] = {}
    for sig in _FORWARDED_SIGNALS:
        old_handlers[sig] = signal.signal(sig, _forwarding_signal_handler)

    timings: list[tuple[str, int]] = []
    failed_step: Step | None = None
    failed_log_path: Path | None = None
    retained_log_path: Path | None = None
    created_log_paths: list[Path] = []
    failed_status = 0
    total_start = time.monotonic()
    try:
        for index, step in enumerate(steps, start=1):
            sink.write(f"━━━ {step.label} ━━━\n")
            sink.flush()
            step_start = time.monotonic()
            log_path = _create_log_path(index, step.label)
            created_log_paths.append(log_path)
            handle = spawner.spawn(step.argv, log_path)
            _current_handle_ref[0] = handle
            try:
                status = handle.wait()
            finally:
                _current_handle_ref[0] = None
            elapsed = round(time.monotonic() - step_start)
            timings.append((step.label, elapsed))
            if status != 0:
                failed_step = step
                failed_log_path = log_path
                failed_status = status
                break
            _discard_log(log_path)
            sink.write(f"{STEP_PASS_STATUS}  {step.label}  {elapsed}s\n")
            sink.flush()
        if failed_step is None:
            total = round(time.monotonic() - total_start)
            _write_summary(sink, timings, total=total)
            return 0
        if failed_log_path is not None:
            retained_log_path = failed_log_path
            _write_failure_details(
                sink,
                step=failed_step,
                status=failed_status,
                elapsed=timings[-1][1],
                log_path=failed_log_path,
            )
        _write_summary(sink, timings, failed_label=failed_step.label)
        return failed_status
    finally:
        for log_path in created_log_paths:
            if log_path != retained_log_path:
                _discard_log(log_path)
        for sig, old in old_handlers.items():
            signal.signal(sig, old)
