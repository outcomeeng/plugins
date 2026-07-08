"""Click command: ``outcomeeng-evals ci <root>``."""

from __future__ import annotations

from pathlib import Path

import click

from outcomeeng_evals.ci_execution import (
    CiRunSettings,
    DEFAULT_CI_MAX_BUDGET_USD,
    DEFAULT_CI_TIMEOUT_SECONDS,
    DEFAULT_CI_WORKERS,
    command_for_plan_item,
    execute_ci_plan,
)
from outcomeeng_evals.ci_plan import (
    CHANGED_PATHS_FILE_HELP,
    CiMode,
    build_ci_plan,
    read_changed_paths_file,
)


@click.command(name="ci")
@click.argument(
    "root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--mode",
    type=click.Choice([mode.value for mode in CiMode]),
    default=CiMode.FULL.value,
    show_default=True,
    help="CI selection mode.",
)
@click.option(
    "--changed-paths-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help=CHANGED_PATHS_FILE_HELP,
)
@click.option(
    "--default-plugin-dir",
    type=click.Path(file_okay=False, path_type=Path),
    help="Plugin directory used when an eval.toml omits plugin_dir.",
)
@click.option("--workers", default=DEFAULT_CI_WORKERS, show_default=True)
@click.option("--max-budget-usd", default=DEFAULT_CI_MAX_BUDGET_USD, show_default=True)
@click.option(
    "--timeout-seconds", default=DEFAULT_CI_TIMEOUT_SECONDS, show_default=True
)
def ci_command(
    root: Path,
    mode: str,
    changed_paths_file: Path | None,
    default_plugin_dir: Path | None,
    workers: str,
    max_budget_usd: str,
    timeout_seconds: str,
) -> None:
    """Plan and run CI eval suites."""
    plan = build_ci_plan(
        root,
        mode=CiMode(mode),
        changed_paths=read_changed_paths_file(changed_paths_file),
        default_plugin_dir=default_plugin_dir,
    )
    if not plan:
        click.echo("No eval suites selected for this change.")
        return

    settings = CiRunSettings(
        workers=workers,
        max_budget_usd=max_budget_usd,
        timeout_seconds=timeout_seconds,
    )
    click.echo(f"Selected {len(plan)} eval suite invocation(s):")
    for item in plan:
        click.echo(f"  {' '.join(command_for_plan_item(item, settings=settings))}")
    result = execute_ci_plan(plan, settings=settings)
    for item in result.failed:
        click.echo(f"Eval suite below threshold or errored: {item.eval_toml}", err=True)
    ctx = click.get_current_context()
    ctx.exit(result.exit_code)
