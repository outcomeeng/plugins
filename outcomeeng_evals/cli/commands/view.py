"""Click command: ``outcomeeng-evals view <run.html>`` or ``--latest <eval-dir>``."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click


RUNS_DIRNAME = "runs"


@click.command(name="view")
@click.argument(
    "target",
    type=click.Path(exists=True, path_type=Path),
    required=False,
)
@click.option(
    "--latest",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=False,
    help="Eval directory to open the most-recent run's HTML viewer from.",
)
def view_command(target: Path | None, latest: Path | None) -> None:
    """Open an eval run's HTML viewer in the default browser."""
    if target is None and latest is None:
        msg = "either TARGET or --latest is required"
        raise click.UsageError(msg)
    html_path = target if target is not None else _latest_html(latest)
    if html_path is None or not html_path.is_file():
        msg = f"no HTML viewer found at {html_path}"
        raise click.UsageError(msg)
    _open_in_browser(html_path)


def _latest_html(eval_dir: Path | None) -> Path | None:
    if eval_dir is None:
        return None
    runs_dir = eval_dir / RUNS_DIRNAME
    if not runs_dir.is_dir():
        return None
    candidates = sorted(runs_dir.glob("*.html"))
    return candidates[-1] if candidates else None


def _open_in_browser(html_path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", str(html_path)], check=False)
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", str(html_path)], check=False)
    else:
        click.echo(str(html_path))
