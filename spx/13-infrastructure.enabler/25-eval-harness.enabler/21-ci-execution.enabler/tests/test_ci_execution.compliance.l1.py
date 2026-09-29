"""Compliance evidence for the eval CI CLI command."""

from __future__ import annotations

import os
from pathlib import Path

from click.testing import CliRunner

from outcomeeng_evals.cli import main
from outcomeeng_evals.cli.commands.ci import ci_command
from outcomeeng_testing.evals.factories import run_default_ci_subcommand


def test_main_group_exposes_ci_subcommand() -> None:
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == os.EX_OK
    assert str(ci_command.name) in result.output


def test_ci_subcommand_builds_plan_and_executes_with_default_ceilings(
    tmp_path: Path,
) -> None:
    run = run_default_ci_subcommand(tmp_path)

    assert run.result.exit_code == os.EX_OK
    assert run.commands == (run.expected_command,)
