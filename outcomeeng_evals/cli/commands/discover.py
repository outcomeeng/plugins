"""Click command: ``outcomeeng-evals discover <root>``."""

from __future__ import annotations

from pathlib import Path

import click


EVAL_TOML_FILENAME = "eval.toml"


@click.command(name="discover")
@click.argument(
    "root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
def discover_command(root: Path) -> None:
    """Walk ROOT and list every eval.toml found beneath it."""
    discovered = sorted(root.rglob(EVAL_TOML_FILENAME))
    for path in discovered:
        click.echo(str(path))
