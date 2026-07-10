"""Click command: ``outcomeeng-evals materialize-ci-triggers <root>``."""

from __future__ import annotations

from pathlib import Path

import click

from outcomeeng_evals.ci_triggers import CiTriggerError, materialize_ci_triggers


@click.command(name="materialize-ci-triggers")
@click.argument(
    "root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--workflow",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Workflow file carrying the generated eval trigger-path blocks.",
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path(),
    show_default=True,
    help="Repository root the generated trigger paths are relative to.",
)
@click.option(
    "--check",
    is_flag=True,
    help="Fail when the workflow's trigger paths are stale instead of writing them.",
)
def ci_triggers_command(
    root: Path,
    workflow: Path,
    repo_root: Path,
    check: bool,
) -> None:
    """Write or check the CI workflow's eval trigger paths derived from ROOT."""
    try:
        result = materialize_ci_triggers(
            root, workflow, repo_root=repo_root, check=check
        )
    except CiTriggerError as exc:
        raise click.ClickException(str(exc)) from exc
    action = "wrote" if result.changed else "current"
    click.echo(f"{action}: {result.workflow} ({len(result.paths)} trigger paths)")
