"""Compliance evidence for the eval CI CLI command."""

from __future__ import annotations

import os
from pathlib import Path

from click.testing import CliRunner

from outcomeeng_evals.ci_execution import (
    DEFAULT_CI_MAX_BUDGET_USD,
    DEFAULT_CI_TIMEOUT_SECONDS,
    DEFAULT_CI_WORKERS,
    UV_RUN_EVALS_ARGV_PREFIX,
)
from outcomeeng_evals.cli import main
from outcomeeng_evals.cli.commands.ci import ci_command
from outcomeeng_evals.cli.commands.run import (
    CASE_ID_OPTION,
    MAX_BUDGET_USD_OPTION,
    PLUGIN_DIR_OPTION,
    TIMEOUT_SECONDS_OPTION,
    WORKERS_OPTION,
)
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
    assert run.commands == (
        (
            *UV_RUN_EVALS_ARGV_PREFIX,
            str(run.eval_toml),
            PLUGIN_DIR_OPTION,
            str(run.plugin_dir),
            WORKERS_OPTION,
            DEFAULT_CI_WORKERS,
            MAX_BUDGET_USD_OPTION,
            DEFAULT_CI_MAX_BUDGET_USD,
            TIMEOUT_SECONDS_OPTION,
            DEFAULT_CI_TIMEOUT_SECONDS,
            *(
                token
                for case_id in run.smoke_case_ids
                for token in (CASE_ID_OPTION, case_id)
            ),
        ),
    )
