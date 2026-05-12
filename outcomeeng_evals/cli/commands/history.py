"""Click command: ``outcomeeng-evals history <history.jsonl>``."""

from __future__ import annotations

import json
from pathlib import Path

import click


@click.command(name="history")
@click.argument(
    "history_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--limit",
    type=int,
    default=10,
    show_default=True,
    help="Number of most-recent rows to display.",
)
def history_command(history_path: Path, limit: int) -> None:
    """Print the most recent rows of a per-eval history.jsonl."""
    rows = _load_rows(history_path)
    if not rows:
        click.echo("history is empty")
        return
    recent = rows[-limit:]
    for row in recent:
        passed = bool(row.get("passed"))
        verdict = "PASS" if passed else "FAIL"
        pass_rate = row.get("pass_rate")
        # ``bool`` is an ``int`` subclass, so the ``bool`` rejection must
        # come before the ``(int, float)`` check — otherwise a stray
        # ``true``/``false`` in the JSON row would be formatted as 100%/0%
        # instead of falling through to ``"?"``.
        pct = (
            f"{float(pass_rate):.1%}"
            if not isinstance(pass_rate, bool) and isinstance(pass_rate, (int, float))
            else "?"
        )
        click.echo(
            f"{row.get('timestamp', '?')}  {verdict}  pass_rate={pct}  "
            f"cases={row.get('cases_passed', '?')}/{row.get('cases_total', '?')}  "
            f"git={row.get('git_sha', '?')}"
        )


def _load_rows(history_path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in history_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        rows.append(json.loads(stripped))
    return rows
