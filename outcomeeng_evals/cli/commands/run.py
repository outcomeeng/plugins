"""Click command: ``outcomeeng-evals run <eval.toml>``."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import click

from outcomeeng_evals.case import Case
from outcomeeng_evals.cli.wiring import build_claude_runner
from outcomeeng_evals.definition import RUNS_DIRNAME, load_definition
from outcomeeng_evals.history import HISTORY_FILENAME, append_history_row
from outcomeeng_evals.report import JSON_SCHEMA_VERSION, write_html_report
from outcomeeng_evals.suite import SuiteResult, format_report, run_suite


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
    type=click.IntRange(min=1, max=16),
    default=1,
    show_default=True,
    help=(
        "Parallel case workers (case-file order is preserved in outcomes). "
        "Capped at 16 to prevent fork bursts against the Claude API."
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
def run_command(
    eval_toml: Path,
    plugin_dir: Path,
    workers: int,
    max_budget_usd: float,
    timeout_seconds: int,
) -> None:
    """Replay one eval against Claude and write transcripts + history."""
    definition = load_definition(eval_toml)
    runner = build_claude_runner(
        plugin_dir=plugin_dir,
        max_budget_usd=max_budget_usd,
        timeout_seconds=timeout_seconds,
    )
    template = definition.prompt_template_path.read_text(encoding="utf-8")
    result = run_suite(
        cases_path=definition.cases_path,
        runner=runner,
        build_prompt=lambda case: _render_prompt(template, case),
        trials_per_case=definition.trials,
        suite_threshold=definition.threshold,
        workers=workers,
    )

    eval_dir = eval_toml.parent
    timestamp_label = _timestamp_label()
    runs_dir = eval_dir / RUNS_DIRNAME
    html_path = runs_dir / f"{timestamp_label}.html"
    write_html_report(result, html_path, title=definition.title)

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
) -> dict[str, object]:
    return {
        "timestamp": timestamp,
        "schema_version": JSON_SCHEMA_VERSION,
        "git_sha": _git_sha(),
        "passed": result.passed,
        "pass_rate": result.pass_rate,
        "cases_total": len(result.outcomes),
        "cases_passed": sum(1 for o in result.outcomes if o.passed),
        "total_cost_usd": _sum_cost(result),
        "total_duration_ms": _sum_duration(result),
        "transcript": transcript_relative,
    }


def _git_sha() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
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


def _sum_cost(result: SuiteResult) -> float | None:
    accum: float | None = None
    for outcome in result.outcomes:
        for trial in outcome.trials:
            value = trial.metadata.total_cost_usd
            if value is None:
                continue
            accum = value if accum is None else accum + value
    return accum


def _sum_duration(result: SuiteResult) -> float | None:
    accum: float | None = None
    for outcome in result.outcomes:
        for trial in outcome.trials:
            value = trial.metadata.duration_ms
            if value is None:
                continue
            accum = value if accum is None else accum + value
    return accum
