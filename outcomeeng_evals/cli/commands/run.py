"""Click command: ``outcomeeng-evals run <eval.toml>``."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, Protocol, cast

import click

from outcomeeng_evals.case import Case
from outcomeeng_evals.cli.wiring import build_claude_runner
from outcomeeng_evals.definition import RUNS_DIRNAME, load_definition
from outcomeeng_evals.history import HISTORY_FILENAME, HistoryRow, append_history_row
from outcomeeng_evals.report import JSON_SCHEMA_VERSION, write_run_reports
from outcomeeng_evals.runner import ModelRunner, RunMetadata
from outcomeeng_evals.suite import SuiteResult, format_report, run_suite


# Worker bounds for parallel case execution. The upper bound caps concurrent
# `claude` subprocesses so a misconfigured worker count cannot fork-burst the
# Claude API (the no-fork-bomb stance the eval-harness spec inherits from the
# plugin runtime conventions).
MIN_WORKERS = 1
MAX_WORKERS = 16
RUNNER_FACTORY_KEY: Final = "runner_factory"


class RunnerFactory(Protocol):
    """Build a model runner for the run command."""

    def __call__(
        self,
        *,
        plugin_dir: Path,
        max_budget_usd: float,
        timeout_seconds: int,
    ) -> ModelRunner: ...


@click.command(name="run")
@click.argument(
    "eval_toml",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--plugin-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Path to a Claude Code plugin directory to load for the eval.",
)
@click.option(
    "--workers",
    type=click.IntRange(min=MIN_WORKERS, max=MAX_WORKERS),
    default=MIN_WORKERS,
    show_default=True,
    help=(
        "Parallel case workers (case-file order is preserved in outcomes). "
        f"Capped at {MAX_WORKERS} to prevent fork bursts against the Claude API."
    ),
)
@click.option(
    "--max-budget-usd",
    type=float,
    default=0.50,
    show_default=True,
    help="Per-invocation budget passed through to the Claude CLI.",
)
@click.option(
    "--timeout-seconds",
    type=click.IntRange(min=1),
    default=120,
    show_default=True,
    help="Per-invocation timeout for the Claude subprocess.",
)
@click.option(
    "--case-id",
    "case_ids",
    multiple=True,
    help="Run only the named case id. Repeat to select multiple cases.",
)
def run_command(
    eval_toml: Path,
    plugin_dir: Path,
    workers: int,
    max_budget_usd: float,
    timeout_seconds: int,
    case_ids: tuple[str, ...],
) -> None:
    """Replay one eval against Claude and write transcripts + history."""
    definition = load_definition(eval_toml)
    runner_factory = _runner_factory_from_context()
    runner = runner_factory(
        plugin_dir=plugin_dir,
        max_budget_usd=max_budget_usd,
        timeout_seconds=timeout_seconds,
    )
    template = definition.prompt_template_path.read_text(encoding="utf-8")
    try:
        result = run_suite(
            cases_path=definition.cases_path,
            runner=runner,
            build_prompt=lambda case: _render_prompt(template, case) + _FORMAT_SUFFIX,
            trials_per_case=definition.trials,
            suite_threshold=definition.threshold,
            workers=workers,
            case_ids=case_ids,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    eval_dir = eval_toml.parent
    timestamp_label = _timestamp_label()
    runs_dir = eval_dir / RUNS_DIRNAME
    html_path = runs_dir / f"{timestamp_label}.html"
    write_run_reports(result, html_path, title=definition.title)

    append_history_row(
        eval_dir / HISTORY_FILENAME,
        _history_row(
            timestamp=timestamp_label,
            result=result,
            transcript_relative=f"{RUNS_DIRNAME}/{timestamp_label}.json",
        ),
    )

    click.echo(format_report(result))
    click.echo(f"HTML: {html_path}")
    click.echo(f"JSON: {html_path.with_suffix('.json')}")
    ctx = click.get_current_context()
    ctx.exit(0 if result.passed else 1)


def _runner_factory_from_context() -> RunnerFactory:
    root_obj = click.get_current_context().find_root().obj
    if isinstance(root_obj, dict) and RUNNER_FACTORY_KEY in root_obj:
        candidate = root_obj[RUNNER_FACTORY_KEY]
        if not callable(candidate):
            msg = f"context object key {RUNNER_FACTORY_KEY!r} must be callable"
            raise click.UsageError(msg)
        return cast(RunnerFactory, candidate)
    return build_claude_runner


_FORMAT_SUFFIX = (
    "\n\nYour entire response must be one JSON object — no prose, no"
    " commentary. The grader tries json.loads() on the raw response; if"
    " that fails it strips a single surrounding markdown code fence and"
    " retries. Wrapping the JSON in a code fence is therefore tolerated"
    " but unnecessary; prose anywhere outside the JSON object is a parse"
    " failure."
)


# An identifier-shaped ``{token}`` — what a placeholder typo looks like
# (``{input_jsn}``). A ``{`` that opens a JSON object or arbitrary prose
# does not match this, so the warning below fires only on plausible typos,
# not on every literal brace in a template.
_PLACEHOLDER_LIKE_RE = re.compile(r"\{[a-z_][a-z0-9_]*\}")


def _render_prompt(template: str, case: Case) -> str:
    # Single-pass placeholder substitution: walk the template and replace
    # exactly the two recognized placeholders. Chained ``str.replace`` would
    # let a case id containing ``{input_json}`` collide with the second
    # substitution and inject the case's JSON payload into a position the
    # template author did not intend. Between placeholders, slice the
    # literal run up to the next ``{`` in one append rather than copying a
    # character at a time.
    substitutions = {
        "{case_id}": case.id,
        "{input_json}": json.dumps(case.input, indent=2),
    }
    parts: list[str] = []
    index = 0
    length = len(template)
    while index < length:
        next_brace = template.find("{", index)
        if next_brace == -1:
            parts.append(template[index:])
            break
        parts.append(template[index:next_brace])
        match = next(
            (
                placeholder
                for placeholder in substitutions
                if template.startswith(placeholder, next_brace)
            ),
            None,
        )
        if match is None:
            typo = _PLACEHOLDER_LIKE_RE.match(template, next_brace)
            if typo is not None:
                click.echo(
                    f"warning: prompt template references unrecognized placeholder "
                    f"{typo.group(0)} — known placeholders are "
                    f"{', '.join(sorted(substitutions))}; passing it through as "
                    f"literal text (a typo here surfaces only as a grading failure)",
                    err=True,
                )
            parts.append("{")
            index = next_brace + 1
            continue
        parts.append(substitutions[match])
        index = next_brace + len(match)
    return "".join(parts)


def _timestamp_label() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _history_row(
    *,
    timestamp: str,
    result: SuiteResult,
    transcript_relative: str,
) -> HistoryRow:
    return {
        "timestamp": timestamp,
        "schema_version": JSON_SCHEMA_VERSION,
        "git_sha": _git_sha(),
        "passed": result.passed,
        "pass_rate": result.pass_rate,
        "cases_total": len(result.outcomes),
        "cases_passed": sum(1 for o in result.outcomes if o.passed),
        "total_cost_usd": _sum_float(result, lambda m: m.total_cost_usd),
        "total_duration_ms": _sum_float(result, lambda m: m.duration_ms),
        "total_input_tokens": _sum_int(result, lambda m: m.input_tokens),
        "total_output_tokens": _sum_int(result, lambda m: m.output_tokens),
        "total_cache_read_input_tokens": _sum_int(
            result, lambda m: m.cache_read_input_tokens
        ),
        "total_cache_creation_input_tokens": _sum_int(
            result, lambda m: m.cache_creation_input_tokens
        ),
        "transcript": transcript_relative,
    }


def _git_sha() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip() or "unknown"


def _sum_float(
    result: SuiteResult, value_of: Callable[[RunMetadata], float | None]
) -> float | None:
    """Sum a float ``RunMetadata`` field across every trial.

    The accumulator stays ``None`` until a trial supplies a value, so a
    field absent from every trial surfaces as ``null`` rather than a
    fabricated ``0`` — "no run carried this metric" stays distinct from "a
    run genuinely measured zero". A real ``0.0`` from any trial initialises
    the accumulator, so a measured zero is reported as ``0``, not dropped.
    The typed ``value_of`` accessor keeps static type coverage that an
    attribute-name string would erase.
    """
    accum: float | None = None
    for outcome in result.outcomes:
        for trial in outcome.trials:
            value = value_of(trial.metadata)
            if value is None:
                continue
            accum = value if accum is None else accum + value
    return accum


def _sum_int(
    result: SuiteResult, value_of: Callable[[RunMetadata], int | None]
) -> int | None:
    """Sum an integer ``RunMetadata`` field across every trial.

    The integer analogue of ``_sum_float`` — same null-vs-zero contract
    (``None`` only when every trial omitted the field; a genuine ``0``
    initialises the accumulator) and the same typed ``value_of`` accessor.
    """
    accum: int | None = None
    for outcome in result.outcomes:
        for trial in outcome.trials:
            value = value_of(trial.metadata)
            if value is None:
                continue
            accum = value if accum is None else accum + value
    return accum
