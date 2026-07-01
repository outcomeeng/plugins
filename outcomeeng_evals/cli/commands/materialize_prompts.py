"""Click command: ``outcomeeng-evals materialize-prompts <root>``."""

from __future__ import annotations

from pathlib import Path

import click

from outcomeeng_evals.producer_prompt import (
    ProducerPromptError,
    materialize_prompts,
)


@click.command(name="materialize-prompts")
@click.argument(
    "root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Repository root for repository-relative producer paths.",
)
@click.option(
    "--check",
    is_flag=True,
    help="Fail when generated prompts are stale instead of writing them.",
)
def materialize_prompts_command(root: Path, repo_root: Path, check: bool) -> None:
    """Write or check producer-derived eval prompts under ROOT."""
    try:
        paths = materialize_prompts(root, repo_root=repo_root, check=check)
    except ProducerPromptError as exc:
        raise click.ClickException(str(exc)) from exc
    action = "checked" if check else "materialized"
    for path in paths:
        click.echo(f"{action}: {path}")
