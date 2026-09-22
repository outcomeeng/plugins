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
import os
import re
import signal
import tempfile
import time
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path
from types import FrameType
from typing import Final, TextIO

from outcomeeng.validation._model import ProcessHandle, ProcessSpawner, Recipe, Step
from outcomeeng.validation.agent_disable import AGENT_SWITCHES
from outcomeeng.validation.skip_report import (
    SKIP_LINE_FORM,
    SKIP_REPORT_FILE_PREFIX,
    SKIP_REPORT_FILE_SUFFIX,
    SKIP_REPORT_OPTION,
    SKIP_REPORT_SWITCH_FIELD,
    SKIP_REPORT_TEST_FIELD,
    STEP_SKIP_STATUS,
)
from outcomeeng.validation._steps import PYTEST_ARGV, RECIPE_AD_HOC, RECIPE_CHECK

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
SUCCESS_EXIT_CODE: Final = os.EX_OK
"""The exit code this orchestrator returns when every step it ran passed.

The value comes from the platform, which owns what a successful process exit
is, and the orchestrator's contract is that it returns exactly that code. A
child's own passing exit code is the same platform value, so the step loop
reads this constant for both.
"""
SPAWN_FAILURE_EXIT_CODE: Final = 1
PHASE_PREFLIGHT: Final = "preflight"
PHASE_RECIPE: Final = "recipe"
PHASE_COMPLETE: Final = "complete"
RECIPE_HEADER_FORM: Final = "━━━ Recipe {name} ━━━"
"""The banner announcing one recipe in the live output."""
STEP_HEADER_FORM: Final = "━━━ {label} ━━━"
"""The banner announcing one step in the live output."""
TIMING_SUMMARY_BANNER: Final = "━━━ Timing Summary ━━━"
"""The banner opening the timing block."""
TIMING_ROW_FORM: Final = "  {label:<20} {value:>3}"
"""One timing row: a padded label and a right-aligned value."""
TIMING_DIVIDER: Final = "  ────────────────────────"
"""The rule separating the timing rows from the total."""
TIMING_TOTAL_LABEL: Final = "TOTAL"
"""The label of the timing block's total row."""
TIMING_FAILED_LABEL: Final = "FAILED"
"""The label of the timing block's failed row."""
STEP_STATUS_PREFIX_FORM: Final = "{status}  {label}"
"""The opening of every step line: its status and its label."""
STEP_STATUS_LINE_FORM: Final = STEP_STATUS_PREFIX_FORM + "  {elapsed}s"
"""One step's status line: the prefix followed by its elapsed seconds."""
STEP_FAILURE_LINE_FORM: Final = STEP_STATUS_LINE_FORM + "  exit {exit_code}"
"""A failing step's line: the status line followed by the child's exit code."""
"""One declared skip's line: the skipped status, the row, and its switch."""
_TIMING_ROW_VALUE: Final = re.compile(r"(\d+)s$", re.MULTILINE)
"""The engine's one reading of a row's value, applied inside the timing block.

The value is read per line of the block rather than per line of the run,
because a step's status line ends in the same elapsed seconds and only the
block's bounds tell the two apart.
"""
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
SUMMARY_KEY_SKIPPED: Final = "skipped"

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
    sink.write(f"\n{TIMING_SUMMARY_BANNER}\n")
    for label, elapsed in timings:
        sink.write(f"{TIMING_ROW_FORM.format(label=label, value=elapsed)}s\n")
    sink.write(f"{TIMING_DIVIDER}\n")
    if total is not None:
        sink.write(
            f"{TIMING_ROW_FORM.format(label=TIMING_TOTAL_LABEL, value=total)}s\n"
        )
    if failed_label is not None:
        sink.write(
            f"{TIMING_ROW_FORM.format(label=TIMING_FAILED_LABEL, value='')}"
            f"{failed_label}\n"
        )
    sink.flush()


class TimingBlockNotBounded(ValueError):
    """The text handed to the row reader carries no complete timing block."""

    def __init__(self, missing: str) -> None:
        super().__init__(f"the timing block is not bounded: {missing!r} is absent")
        self.missing = missing


def timing_row_values(output: str) -> tuple[int, ...]:
    """Return the elapsed seconds the run's per-step timing rows carry, in order.

    The rows are the lines a complete timing block holds — the text between the
    banner that opens it and the divider that closes it. Every other line the
    engine writes lies outside those bounds, so none of them is read as a row:
    a step's status line ends in the same elapsed seconds, and the total and
    failed rows follow the divider.

    Both bounds are required. Text carrying one without the other is refused
    with `TimingBlockNotBounded` naming the absent bound rather than read:
    without the banner the reader would answer the empty tuple, which reads as
    a run that had no steps, and without the divider the block would run on
    past the rows until the total's own seconds were read as a step's.

    Each bound is found at its first occurrence, so the caller supplies the
    run's own output: a captured child excerpt reproducing the banner line
    verbatim would move the opening bound, and that line is the child's rather
    than the engine's.

    Published beside `TIMING_SUMMARY_BANNER`, `TIMING_DIVIDER`, and
    `TIMING_ROW_FORM`, so no reader spells the block's bounds or the row's form
    a second time.
    """
    _, banner, after_banner = output.partition(f"{TIMING_SUMMARY_BANNER}\n")
    if not banner:
        raise TimingBlockNotBounded(TIMING_SUMMARY_BANNER)
    block, divider, _ = after_banner.partition(f"{TIMING_DIVIDER}\n")
    if not divider:
        raise TimingBlockNotBounded(TIMING_DIVIDER)
    return tuple(int(match.group(1)) for match in _TIMING_ROW_VALUE.finditer(block))


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


def _create_skip_report_path(step_index: int, label: str) -> Path:
    slug = _safe_log_slug(label)
    with tempfile.NamedTemporaryFile(
        prefix=f"{SKIP_REPORT_FILE_PREFIX}{step_index:02d}-{slug}-",
        suffix=SKIP_REPORT_FILE_SUFFIX,
        delete=False,
    ) as output:
        return Path(output.name)


def _is_pytest_step(step: Step) -> bool:
    return step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV


def _step_reporting_skips(step: Step, report_path: Path) -> Step:
    return replace(step, argv=(*step.argv, f"{SKIP_REPORT_OPTION}={report_path}"))


def _read_skip_records(report_path: Path | None) -> tuple[dict[str, object], ...]:
    """Read the records the child left, keeping only declared skips.

    The producer is a separate process, so a truncated or malformed line is a
    child-side condition rather than an orchestrator failure: it is skipped and
    the well-formed records still reach the step's summary.

    A line is rejected on four counts: it does not parse as JSON, it parses as
    something other than an object, either field is absent or is not a string,
    or the switch it names is not one this package declares. The last is the
    reader's own domain rather than the line's shape — `AGENT_SWITCHES` is the
    same declaration the summary schema's switch enum reads, so a switch
    outside it names no skip this package can have declared, and copying it
    into the summary would emit a run summary the schema refuses.
    """
    if report_path is None:
        return ()
    try:
        payload = report_path.read_text(encoding="utf-8")
    except OSError:
        return ()
    records: list[dict[str, object]] = []
    for line in payload.splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue
        test = entry.get(SKIP_REPORT_TEST_FIELD)
        switch = entry.get(SKIP_REPORT_SWITCH_FIELD)
        if not isinstance(test, str) or not isinstance(switch, str):
            continue
        if switch not in AGENT_SWITCHES:
            continue
        records.append({SKIP_REPORT_TEST_FIELD: test, SKIP_REPORT_SWITCH_FIELD: switch})
    return tuple(records)


def _write_skip_lines(sink: TextIO, records: Sequence[dict[str, object]]) -> None:
    for record in records:
        sink.write(
            SKIP_LINE_FORM.format(
                status=STEP_SKIP_STATUS,
                test=record[SKIP_REPORT_TEST_FIELD],
                switch=record[SKIP_REPORT_SWITCH_FIELD],
            )
            + "\n"
        )
    if records:
        sink.flush()


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
    sink.write(
        STEP_FAILURE_LINE_FORM.format(
            status=STEP_FAIL_STATUS, label=step.label, elapsed=elapsed, exit_code=status
        )
        + "\n"
    )
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
    skipped: Sequence[dict[str, object]] = (),
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
    if skipped:
        record[SUMMARY_KEY_SKIPPED] = list(skipped)
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
    sink.write(f"{RECIPE_HEADER_FORM.format(name=recipe.name)}\n")
    sink.flush()
    try:
        for phase, steps in (
            (PHASE_PREFLIGHT, recipe.preflight_steps),
            (PHASE_RECIPE, recipe.steps),
        ):
            for step in steps:
                step_index += 1
                sink.write(f"{STEP_HEADER_FORM.format(label=step.label)}\n")
                sink.flush()
                step_start = time.monotonic()
                log_path = _create_log_path(step_index, step.label)
                created_log_paths.append(log_path)
                skip_report_path = (
                    _create_skip_report_path(step_index, step.label)
                    if _is_pytest_step(step)
                    else None
                )
                spawn_step = step
                if skip_report_path is not None:
                    created_log_paths.append(skip_report_path)
                    spawn_step = _step_reporting_skips(step, skip_report_path)
                try:
                    handle = _spawn_with_deferred_signal_forwarding(
                        spawner,
                        spawn_step,
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
                skipped = _read_skip_records(skip_report_path)
                elapsed = round(time.monotonic() - step_start)
                timings.append((step.label, elapsed))
                if exit_code != SUCCESS_EXIT_CODE:
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
                            skipped=skipped,
                        )
                    )
                    _write_failure_details(
                        sink,
                        step=step,
                        status=exit_code,
                        elapsed=elapsed,
                        log_path=log_path,
                    )
                    _write_skip_lines(sink, skipped)
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
                        skipped=skipped,
                    )
                )
                sink.write(
                    STEP_STATUS_LINE_FORM.format(
                        status=STEP_PASS_STATUS, label=step.label, elapsed=elapsed
                    )
                    + "\n"
                )
                sink.flush()
                _write_skip_lines(sink, skipped)
            if failed_step is not None:
                break
        total = round(time.monotonic() - total_start)
        if failed_step is None:
            _write_timing_summary(sink, timings, total=total)
            return SUCCESS_EXIT_CODE, _recipe_summary(
                recipe=recipe,
                phase=PHASE_COMPLETE,
                status=RUN_PASS_STATUS,
                exit_code=SUCCESS_EXIT_CODE,
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
    exit_code = SUCCESS_EXIT_CODE
    try:
        try:
            for recipe in recipes:
                exit_code, summary = _execute_recipe(spawner, sink, recipe)
                recipe_summaries.append(summary)
                if exit_code != SUCCESS_EXIT_CODE:
                    break
            status = (
                RUN_PASS_STATUS if exit_code == SUCCESS_EXIT_CODE else RUN_FAIL_STATUS
            )
            failed_phase = (
                recipe_summaries[-1][SUMMARY_KEY_PHASE]
                if recipe_summaries and exit_code != SUCCESS_EXIT_CODE
                else PHASE_COMPLETE
            )
            phase = (
                PHASE_COMPLETE if exit_code == SUCCESS_EXIT_CODE else str(failed_phase)
            )
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
