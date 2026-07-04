"""Compliance evidence for the eval CI CLI command."""

from __future__ import annotations

import os
from pathlib import Path

from click.testing import CliRunner

from outcomeeng_evals.cli import main
from outcomeeng_evals.testing.factories import (
    DEFAULT_PLAN_CASE_IDS,
    DEFAULT_CI_OWNED_PATH,
    expected_default_ci_command,
    make_eval_dir,
    write_default_ci_changed_paths_file,
)
from outcomeeng_evals.testing.fakes import make_recording_uv_executable


def test_main_group_exposes_ci_subcommand() -> None:
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == os.EX_OK
    assert "ci" in result.output


def test_ci_subcommand_builds_plan_and_executes_with_default_ceilings(
    tmp_path: Path,
) -> None:
    eval_root = tmp_path / "evals"
    eval_toml = make_eval_dir(
        eval_root / "rule",
        plugin_dir="dist/claude/spec-tree",
        owned_paths=(DEFAULT_CI_OWNED_PATH,),
        smoke_case_ids=DEFAULT_PLAN_CASE_IDS,
    )
    changed_paths_file = write_default_ci_changed_paths_file(tmp_path)
    fake_uv = make_recording_uv_executable(tmp_path)

    result = CliRunner().invoke(
        main,
        [
            "ci",
            str(eval_root),
            "--mode",
            "pr",
            "--changed-paths-file",
            str(changed_paths_file),
        ],
        env=fake_uv.env,
    )

    assert result.exit_code == os.EX_OK
    assert fake_uv.commands() == (expected_default_ci_command(eval_toml),)
