"""Scenario tests for the outcomeeng-evals Click CLI.

Four subcommands are dispatched through a single Click group: ``run``,
``history``, ``view``, and ``discover``. Each subcommand returns
documented exit codes; the group's help surface lists them.
"""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from outcomeeng_evals.cli import main


EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_INVOCATION_ERROR = 2


def test_main_group_exposes_documented_subcommands() -> None:
    runner = CliRunner()

    result = runner.invoke(main, ["--help"])

    assert result.exit_code == EXIT_SUCCESS
    for subcommand in ("run", "history", "view", "discover"):
        assert subcommand in result.output


def test_run_subcommand_requires_eval_toml_path() -> None:
    runner = CliRunner()

    result = runner.invoke(main, ["run"])

    assert result.exit_code == EXIT_INVOCATION_ERROR


def test_run_subcommand_rejects_missing_eval_toml(tmp_path: Path) -> None:
    runner = CliRunner()
    missing_path = tmp_path / "does-not-exist" / "eval.toml"

    result = runner.invoke(main, ["run", str(missing_path)])

    assert result.exit_code != EXIT_SUCCESS


def test_discover_subcommand_lists_eval_toml_files(tmp_path: Path) -> None:
    runner = CliRunner()
    nested_eval = tmp_path / "subtree" / "evals" / "rule-one" / "eval.toml"
    nested_eval.parent.mkdir(parents=True)
    nested_eval.write_text(
        'title = "rule-one"\ncases = "cases.jsonl"\nprompt = "prompt.md"\n',
        encoding="utf-8",
    )
    (nested_eval.parent / "cases.jsonl").write_text("", encoding="utf-8")
    (nested_eval.parent / "prompt.md").write_text("", encoding="utf-8")

    result = runner.invoke(main, ["discover", str(tmp_path)])

    assert result.exit_code == EXIT_SUCCESS
    assert "rule-one" in result.output or str(nested_eval) in result.output


def test_discover_subcommand_succeeds_on_empty_tree(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(main, ["discover", str(tmp_path)])

    assert result.exit_code == EXIT_SUCCESS


def test_history_subcommand_reads_history_file(tmp_path: Path) -> None:
    runner = CliRunner()
    eval_dir = tmp_path / "evals" / "rule"
    eval_dir.mkdir(parents=True)
    history_text = (
        '{"timestamp":"2026-05-11T15:48:00Z","schema_version":"1","git_sha":"abc",'
        '"passed":true,"pass_rate":1.0,"cases_total":4,"cases_passed":4,'
        '"total_cost_usd":1.04,"total_duration_ms":18960,"transcript":"runs/x.json"}\n'
    )
    (eval_dir / "history.jsonl").write_text(history_text, encoding="utf-8")

    result = runner.invoke(main, ["history", str(eval_dir / "history.jsonl")])

    assert result.exit_code == EXIT_SUCCESS
    assert "1.0" in result.output or "100" in result.output


def test_history_subcommand_handles_missing_file(tmp_path: Path) -> None:
    runner = CliRunner()
    missing_path = tmp_path / "history.jsonl"

    result = runner.invoke(main, ["history", str(missing_path)])

    assert result.exit_code != EXIT_SUCCESS


def test_view_subcommand_requires_run_path_or_latest_flag() -> None:
    runner = CliRunner()

    result = runner.invoke(main, ["view"])

    assert result.exit_code != EXIT_SUCCESS
