"""Click command: ``outcomeeng-evals view <run.html>`` or ``--latest <eval-dir>``."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click

from outcomeeng_evals.definition import RUNS_DIRNAME


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
    if target is not None:
        if not target.is_file():
            msg = f"no HTML viewer found at {target}"
            raise click.UsageError(msg)
        _open_in_browser(target)
        return
    if latest is None:  # unreachable: the UsageError above proves one of the two is set
        msg = "internal error: neither TARGET nor --latest resolved after the guard"
        raise AssertionError(msg)
    html_path = _latest_html(latest)
    if html_path is None:
        msg = (
            f"no runs found under {latest / RUNS_DIRNAME}; "
            f"run `outcomeeng-evals run` against the eval first"
        )
        raise click.UsageError(msg)
    if not html_path.is_file():
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
        _launch_opener(["open", str(html_path)], html_path)
    elif sys.platform.startswith("linux"):
        _launch_opener(["xdg-open", str(html_path)], html_path)
    else:
        # No portable opener wired for this platform (Windows, BSD, …):
        # print the path so the caller knows nothing launched and can open
        # it manually.
        click.echo(f"open the report manually: {html_path}")


def _launch_opener(argv: list[str], html_path: Path) -> None:
    """Run the OS file-opener; warn on stderr if it fails (e.g. headless CI).

    A non-zero exit from ``open``/``xdg-open`` (no ``$DISPLAY``, no
    associated handler) would otherwise be invisible — the developer sees
    nothing happen and no error. Print the path so they can open it
    manually.
    """
    completed = subprocess.run(argv, check=False)
    if completed.returncode != 0:
        click.echo(
            f"warning: `{argv[0]}` exited {completed.returncode}; "
            f"open the report manually: {html_path}",
            err=True,
        )
