"""Orchestration loop and signal-forwarding handler for verification recipes.

`run_recipe()` and `run_check()` are the primary entry points: they iterate
declared recipe steps, print labeled headers and timing summaries, write a
structured JSON run summary, and forward SIGTERM/SIGINT/SIGHUP to the
currently-running child's process group via a top-level signal handler that
closes over a module-level reference.

The signal handler uses a single `time.monotonic()` deadline to bound the
SIGKILL grace window — the only polling wait in the package, carved out by
the ADR's bounded-deadline exception.
"""

from __future__ import annotations

import json
import signal
import tempfile
import time
from collections import deque
from collections.abc import Callable, Sequence
from pathlib import Path
from types import FrameType
from typing import Final, TextIO

from outcomeeng.validation._model import ProcessHandle, ProcessSpawner, Recipe, Step
from outcomeeng.validation._steps import RECIPE_AD_HOC, RECIPE_CHECK

FORWARDED_SIGNALS: Final = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
SIGNAL_GRACE_SECONDS: Final = 2.0
SIGNAL_POLL_INTERVAL_SECONDS: Final = 0.05
POST_KILL_REAP_ATTEMPTS: Final = 20
LOG_FILE_PREFIX: Final = "outcomeeng-validation-"
LOG_FILE_SUFFIX: Final = ".log"
SUMMARY_FILE_PREFIX: Final = "outcomeeng-validation-summary-"
SUMMARY_FILE_SUFFIX: Final = ".json"
LOG_SLUG_MAX_LENGTH: Final = 64
STEP_PASS_STATUS: Final = "PASS"
STEP_FAIL_STATUS: Final = "FAIL"
RUN_PASS_STATUS: Final = "pass"
RUN_FAIL_STATUS: Final = "fail"
SPAWN_FAILURE_EXIT_CODE: Final = 1
PHASE_PREFLIGHT: Final = "preflight"
PHASE_RECIPE: Final = "recipe"
PHASE_COMPLETE: Final = "complete"
FULL_LOG_LABEL: Final = "Full log:"
SUMMARY_PATH_LABEL: Final = "Summary:"
FAILURE_EXCERPT_LINE_LIMIT: Final = 80
FAILURE_EXCERPT_CHAR_LIMIT: Final = 12_000
SUMMARY_KEY_RECIPE: Final = "recipe"
SUMMARY_KEY_VERIFICATION_TYPE: Final = "verification_type"
SUMMARY_KEY_PURPOSE: Final = "purpose"
SUMMARY_KEY_PHASE: Final = "phase"
SUMMARY_KEY_STATUS: Final = "status"
SUMMARY_KEY_EXIT_CODE: Final = "exit_code"
SUMMARY_KEY_DURATION_SECONDS: Final = "duration_seconds"
SUMMARY_KEY_SUMMARY_PATH: Final = "summary_path"
SUMMARY_KEY_RECIPES: Final = "recipes"
SUMMARY_KEY_STEPS: Final = "steps"
SUMMARY_KEY_LABEL: Final = "label"
SUMMARY_KEY_ARGV: Final = "argv"
SUMMARY_KEY_LOG_PATH: Final = "log_path"
SUMMARY_KEY_EXCERPT: Final = "excerpt"

_current_handle_ref: list[ProcessHandle | None] = [None]


class _ForwardedSignal(RuntimeError):
    """A handled process signal interrupted the running recipe step."""

    def __init__(self, signum: int, *, child_handle_available: bool) -> None:
        super().__init__(f"received signal {signum}")
        self.signum = signum
        self.exit_code = 128 + signum
        self.child_handle_available = child_handle_available


def _forwarding_signal_handler(signum: int, _frame: FrameType | None) -> None:
    """Forward the received signal to the current child's process group.

    Sends SIGTERM first, polls up to `_GRACE_SECONDS` against a single
    monotonic deadline, then escalates to SIGKILL if the child is still
    alive. Raises `_ForwardedSignal` so the orchestrator can write the
    structured summary before returning `128 + signum`.
    """
    handle = _current_handle_ref[0]
    if handle is None:
        raise _ForwardedSignal(signum, child_handle_available=False)
    if handle.poll() is not None:
        raise _ForwardedSignal(signum, child_handle_available=True)
    terminate_process_group(handle)
    raise _ForwardedSignal(signum, child_handle_available=True)


def terminate_process_group(
    handle: ProcessHandle,
    *,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """Terminate a child process group with bounded grace and reap waits."""
    handle.send_signal_to_group(signal.SIGTERM)
    deadline = monotonic() + SIGNAL_GRACE_SECONDS
    while monotonic() < deadline:
        if handle.poll() is not None:
            return
        sleep(SIGNAL_POLL_INTERVAL_SECONDS)
    handle.send_signal_to_group(signal.SIGKILL)
    for _ in range(POST_KILL_REAP_ATTEMPTS):
        if handle.poll() is not None:
            break
        sleep(SIGNAL_POLL_INTERVAL_SECONDS)


def _write_timing_summary(
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


def _create_summary_path(recipe_name: str) -> Path:
    slug = _safe_log_slug(recipe_name)
    with tempfile.NamedTemporaryFile(
        prefix=f"{SUMMARY_FILE_PREFIX}{slug}-",
        suffix=SUMMARY_FILE_SUFFIX,
        delete=False,
    ) as output:
        return Path(output.name)


def _safe_log_slug(label: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in label)
    normalized = "-".join(part for part in slug.split("-") if part) or "step"
    bounded = normalized[:LOG_SLUG_MAX_LENGTH].rstrip("-")
    return bounded or "step"


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


def _write_summary_file(summary_path: Path, summary: dict[str, object]) -> None:
    summary[SUMMARY_KEY_SUMMARY_PATH] = str(summary_path)
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_summary_path(sink: TextIO, summary_path: Path) -> None:
    sink.write(f"{SUMMARY_PATH_LABEL} {summary_path}\n")
    sink.flush()


def _step_record(
    *,
    recipe: Recipe,
    phase: str,
    step: Step,
    status: str,
    elapsed: int,
    exit_code: int,
    log_path: Path | None = None,
    excerpt: str | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        SUMMARY_KEY_RECIPE: recipe.name,
        SUMMARY_KEY_PHASE: phase,
        SUMMARY_KEY_LABEL: step.label,
        SUMMARY_KEY_ARGV: list(step.argv),
        SUMMARY_KEY_STATUS: status,
        SUMMARY_KEY_DURATION_SECONDS: elapsed,
        SUMMARY_KEY_EXIT_CODE: exit_code,
    }
    if log_path is not None:
        record[SUMMARY_KEY_LOG_PATH] = str(log_path)
    if excerpt is not None:
        record[SUMMARY_KEY_EXCERPT] = excerpt
    return record


def _recipe_summary(
    *,
    recipe: Recipe,
    phase: str,
    status: str,
    exit_code: int,
    elapsed: int,
    steps: Sequence[dict[str, object]],
) -> dict[str, object]:
    return {
        SUMMARY_KEY_RECIPE: recipe.name,
        SUMMARY_KEY_VERIFICATION_TYPE: recipe.verification_type,
        SUMMARY_KEY_PURPOSE: recipe.purpose,
        SUMMARY_KEY_PHASE: phase,
        SUMMARY_KEY_STATUS: status,
        SUMMARY_KEY_EXIT_CODE: exit_code,
        SUMMARY_KEY_DURATION_SECONDS: elapsed,
        SUMMARY_KEY_STEPS: list(steps),
    }


def _consume_pending_forwarded_signal() -> int | None:
    pending = signal.sigpending()
    for sig in FORWARDED_SIGNALS:
        if sig in pending:
            return int(signal.sigwait((sig,)))
    return None


def _spawn_with_deferred_signal_forwarding(
    spawner: ProcessSpawner,
    step: Step,
    log_path: Path,
) -> ProcessHandle:
    previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, FORWARDED_SIGNALS)
    pending_signal: int | None = None
    try:
        handle = spawner.spawn(step.argv, log_path)
        _current_handle_ref[0] = handle
    except Exception:
        pending_signal = _consume_pending_forwarded_signal()
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
        if pending_signal is not None:
            raise _ForwardedSignal(
                pending_signal,
                child_handle_available=False,
            ) from None
        raise
    pending_signal = _consume_pending_forwarded_signal()
    signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    if pending_signal is not None:
        _forwarding_signal_handler(pending_signal, None)
    return handle


def _write_spawn_failure_log(log_path: Path, exc: Exception) -> None:
    log_path.write_text(f"<failed to spawn process: {exc}>\n", encoding="utf-8")


def _execute_recipe(
    spawner: ProcessSpawner,
    sink: TextIO,
    recipe: Recipe,
) -> tuple[int, dict[str, object]]:
    timings: list[tuple[str, int]] = []
    step_records: list[dict[str, object]] = []
    failed_step: Step | None = None
    failed_phase: str | None = None
    retained_log_path: Path | None = None
    created_log_paths: list[Path] = []
    failed_status = 0
    total_start = time.monotonic()
    step_index = 0
    sink.write(f"━━━ Recipe {recipe.name} ━━━\n")
    sink.flush()
    try:
        for phase, steps in (
            (PHASE_PREFLIGHT, recipe.preflight_steps),
            (PHASE_RECIPE, recipe.steps),
        ):
            for step in steps:
                step_index += 1
                sink.write(f"━━━ {step.label} ━━━\n")
                sink.flush()
                step_start = time.monotonic()
                log_path = _create_log_path(step_index, step.label)
                created_log_paths.append(log_path)
                try:
                    handle = _spawn_with_deferred_signal_forwarding(
                        spawner,
                        step,
                        log_path,
                    )
                    exit_code = handle.wait()
                except _ForwardedSignal as interrupt:
                    if not interrupt.child_handle_available:
                        raise
                    exit_code = interrupt.exit_code
                except Exception as exc:
                    _write_spawn_failure_log(log_path, exc)
                    exit_code = SPAWN_FAILURE_EXIT_CODE
                finally:
                    _current_handle_ref[0] = None
                elapsed = round(time.monotonic() - step_start)
                timings.append((step.label, elapsed))
                if exit_code != 0:
                    excerpt = _read_failure_excerpt(log_path)
                    retained_log_path = log_path
                    failed_step = step
                    failed_phase = phase
                    failed_status = exit_code
                    step_records.append(
                        _step_record(
                            recipe=recipe,
                            phase=phase,
                            step=step,
                            status=RUN_FAIL_STATUS,
                            elapsed=elapsed,
                            exit_code=exit_code,
                            log_path=log_path,
                            excerpt=excerpt,
                        )
                    )
                    _write_failure_details(
                        sink,
                        step=step,
                        status=exit_code,
                        elapsed=elapsed,
                        log_path=log_path,
                    )
                    break
                _discard_log(log_path)
                step_records.append(
                    _step_record(
                        recipe=recipe,
                        phase=phase,
                        step=step,
                        status=RUN_PASS_STATUS,
                        elapsed=elapsed,
                        exit_code=exit_code,
                    )
                )
                sink.write(f"{STEP_PASS_STATUS}  {step.label}  {elapsed}s\n")
                sink.flush()
            if failed_step is not None:
                break
        total = round(time.monotonic() - total_start)
        if failed_step is None:
            _write_timing_summary(sink, timings, total=total)
            return 0, _recipe_summary(
                recipe=recipe,
                phase=PHASE_COMPLETE,
                status=RUN_PASS_STATUS,
                exit_code=0,
                elapsed=total,
                steps=step_records,
            )
        _write_timing_summary(sink, timings, failed_label=failed_step.label)
        return failed_status, _recipe_summary(
            recipe=recipe,
            phase=failed_phase or PHASE_RECIPE,
            status=RUN_FAIL_STATUS,
            exit_code=failed_status,
            elapsed=total,
            steps=step_records,
        )
    finally:
        for log_path in created_log_paths:
            if log_path != retained_log_path:
                _discard_log(log_path)


def _install_signal_handlers() -> dict[signal.Signals, signal._HANDLER]:
    old_handlers: dict[signal.Signals, signal._HANDLER] = {}
    for sig in FORWARDED_SIGNALS:
        old_handlers[sig] = signal.signal(sig, _forwarding_signal_handler)
    return old_handlers


def _restore_signal_handlers(
    old_handlers: dict[signal.Signals, signal._HANDLER],
) -> None:
    for sig, old in old_handlers.items():
        signal.signal(sig, old)


def run_recipe(
    spawner: ProcessSpawner,
    sink: TextIO,
    recipe: Recipe,
    *,
    summary_path: Path | None = None,
) -> int:
    """Run one primitive recipe and write its structured summary."""

    resolved_summary_path = summary_path or _create_summary_path(recipe.name)
    old_handlers = _install_signal_handlers()
    total_start = time.monotonic()
    try:
        try:
            exit_code, summary = _execute_recipe(spawner, sink, recipe)
        except _ForwardedSignal as interrupt:
            exit_code = interrupt.exit_code
            elapsed = round(time.monotonic() - total_start)
            summary = _recipe_summary(
                recipe=recipe,
                phase=PHASE_RECIPE,
                status=RUN_FAIL_STATUS,
                exit_code=exit_code,
                elapsed=elapsed,
                steps=(),
            )
        _write_summary_file(resolved_summary_path, summary)
        _write_summary_path(sink, resolved_summary_path)
        return exit_code
    finally:
        _restore_signal_handlers(old_handlers)


def run_check(
    spawner: ProcessSpawner,
    sink: TextIO,
    recipes: Sequence[Recipe],
    *,
    summary_path: Path | None = None,
) -> int:
    """Run primitive recipes in order and stop at the first failed recipe."""

    resolved_summary_path = summary_path or _create_summary_path(RECIPE_CHECK)
    old_handlers = _install_signal_handlers()
    recipe_summaries: list[dict[str, object]] = []
    total_start = time.monotonic()
    exit_code = 0
    try:
        try:
            for recipe in recipes:
                exit_code, summary = _execute_recipe(spawner, sink, recipe)
                recipe_summaries.append(summary)
                if exit_code != 0:
                    break
            status = RUN_PASS_STATUS if exit_code == 0 else RUN_FAIL_STATUS
            failed_phase = (
                recipe_summaries[-1][SUMMARY_KEY_PHASE]
                if recipe_summaries and exit_code != 0
                else PHASE_COMPLETE
            )
            phase = PHASE_COMPLETE if exit_code == 0 else str(failed_phase)
        except _ForwardedSignal as interrupt:
            exit_code = interrupt.exit_code
            status = RUN_FAIL_STATUS
            phase = PHASE_RECIPE
        elapsed = round(time.monotonic() - total_start)
        wrapper_steps: list[object] = []
        for summary in recipe_summaries:
            steps = summary[SUMMARY_KEY_STEPS]
            if isinstance(steps, list):
                wrapper_steps.extend(steps)
        wrapper_summary: dict[str, object] = {
            SUMMARY_KEY_RECIPE: RECIPE_CHECK,
            SUMMARY_KEY_VERIFICATION_TYPE: None,
            SUMMARY_KEY_PURPOSE: None,
            SUMMARY_KEY_PHASE: phase,
            SUMMARY_KEY_STATUS: status,
            SUMMARY_KEY_EXIT_CODE: exit_code,
            SUMMARY_KEY_DURATION_SECONDS: elapsed,
            SUMMARY_KEY_RECIPES: recipe_summaries,
            SUMMARY_KEY_STEPS: wrapper_steps,
        }
        _write_summary_file(resolved_summary_path, wrapper_summary)
        _write_summary_path(sink, resolved_summary_path)
        return exit_code
    finally:
        _restore_signal_handlers(old_handlers)


def run(
    spawner: ProcessSpawner,
    sink: TextIO,
    steps: Sequence[Step],
) -> int:
    """Run an ad hoc step list through the recipe engine.

    Returns 0 on full pass, or the failing step's exit code on first failure.
    Signal delivery during a step is summarized as a failed step and returns
    `128 + signum`.
    """
    return run_recipe(
        spawner=spawner,
        sink=sink,
        recipe=Recipe(
            name=RECIPE_AD_HOC,
            verification_type=None,
            purpose=None,
            preflight_steps=(),
            steps=tuple(steps),
        ),
    )
