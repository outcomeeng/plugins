"""Click command: ``outcomeeng-evals plan <root>``."""

from __future__ import annotations

import json
from pathlib import Path

import click

from outcomeeng_evals.ci_plan import CiMode, build_ci_plan, plan_to_jsonable


@click.command(name="plan")
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
    help="File containing one changed repository-relative path per line.",
)
@click.option(
    "--default-plugin-dir",
    type=click.Path(file_okay=False, path_type=Path),
    help="Plugin directory used when an eval.toml omits plugin_dir.",
)
def plan_command(
    root: Path,
    mode: str,
    changed_paths_file: Path | None,
    default_plugin_dir: Path | None,
) -> None:
    """Build a JSON eval execution plan for CI."""
    changed_paths = _read_changed_paths(changed_paths_file)
    plan = build_ci_plan(
        root,
        mode=CiMode(mode),
        changed_paths=changed_paths,
        default_plugin_dir=default_plugin_dir,
    )
    click.echo(json.dumps(plan_to_jsonable(plan), indent=2))


def _read_changed_paths(path: Path | None) -> tuple[str, ...]:
    if path is None:
        return ()
    return tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
