"""Click CLI entry point for the eval runner.

``outcomeeng-evals`` is wired by ``[project.scripts]`` in pyproject.toml.
The ``main`` group exposes four subcommands:

- ``run`` — load an eval.toml, replay cases through claude, write results.
- ``history`` — read a per-eval history.jsonl and print a trend summary.
- ``view`` — open a run's HTML report (or the latest one).
- ``discover`` — walk a directory tree and list every eval.toml found.
- ``plan`` — select eval suites and cases for CI.
"""

from __future__ import annotations

import click

from outcomeeng_evals.cli.commands.discover import discover_command
from outcomeeng_evals.cli.commands.history import history_command
from outcomeeng_evals.cli.commands.plan import plan_command
from outcomeeng_evals.cli.commands.run import run_command
from outcomeeng_evals.cli.commands.view import view_command


@click.group()
def main() -> None:
    """Replay curated cases through Claude and grade structured verdicts."""


main.add_command(run_command)
main.add_command(history_command)
main.add_command(view_command)
main.add_command(discover_command)
main.add_command(plan_command)
