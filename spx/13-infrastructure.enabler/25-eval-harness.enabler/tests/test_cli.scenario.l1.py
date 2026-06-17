"""Scenario tests for the outcomeeng-evals Click CLI.

The CLI dispatches documented subcommands through one Click group and exposes
them in the group's help surface.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

import pytest
from click.testing import CliRunner

from outcomeeng_evals.cli import main
from outcomeeng_evals.cli.commands import run as run_module
from outcomeeng_evals.cli.commands.run import MAX_WORKERS, _FORMAT_SUFFIX
from outcomeeng_evals.definition import CiPolicy
from outcomeeng_evals.testing.fakes import RecordingRunner, StubModelRunner


EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_INVOCATION_ERROR = 2
REPO_ROOT: Final = Path(__file__).resolve().parents[4]
SPEC_TREE_EVALS_WORKFLOW: Final = (
    REPO_ROOT / ".github" / "workflows" / "spec-tree-evals.yml"
)


def test_main_group_exposes_documented_subcommands() -> None:
    runner = CliRunner()

    result = runner.invoke(main, ["--help"])

    assert result.exit_code == EXIT_SUCCESS
    for subcommand in ("run", "history", "view", "discover", "plan"):
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


def test_run_subcommand_rejects_workers_above_cap(tmp_path: Path) -> None:
    runner = CliRunner()
    eval_toml = tmp_path / "eval.toml"
    eval_toml.write_text("", encoding="utf-8")
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()

    result = runner.invoke(
        main,
        [
            "run",
            str(eval_toml),
            "--plugin-dir",
            str(plugin_dir),
            "--workers",
            str(MAX_WORKERS + 1),
        ],
    )

    assert result.exit_code == EXIT_INVOCATION_ERROR
    assert "workers" in result.output.lower()


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


def test_run_command_appends_format_suffix_to_every_prompt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    eval_dir = tmp_path / "evals" / "rule"
    eval_dir.mkdir(parents=True)
    (eval_dir / "eval.toml").write_text(
        'title = "rule"\ncases = "cases.jsonl"\nprompt = "prompt.md"\n',
        encoding="utf-8",
    )
    (eval_dir / "cases.jsonl").write_text(
        '{"id":"alpha","input":{"x":1},"expected_verdict":{"must_contain":[{"ok":true}]}}\n',
        encoding="utf-8",
    )
    (eval_dir / "prompt.md").write_text(
        "Case {case_id}: {input_json}",
        encoding="utf-8",
    )
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()

    recorder = RecordingRunner(inner=StubModelRunner(response='{"ok": true}'))
    monkeypatch.setattr(run_module, "build_claude_runner", lambda **_: recorder)

    cli_runner = CliRunner()
    cli_runner.invoke(
        main,
        ["run", str(eval_dir / "eval.toml"), "--plugin-dir", str(plugin_dir)],
    )

    assert len(recorder.transcripts) == 1
    captured_prompt, _ = recorder.transcripts[0]
    assert captured_prompt.endswith(_FORMAT_SUFFIX)
    assert "Case alpha" in captured_prompt


def test_run_command_filters_cases_by_case_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    eval_dir = tmp_path / "evals" / "rule"
    eval_dir.mkdir(parents=True)
    (eval_dir / "eval.toml").write_text(
        'title = "rule"\ncases = "cases.jsonl"\nprompt = "prompt.md"\n',
        encoding="utf-8",
    )
    (eval_dir / "cases.jsonl").write_text(
        "\n".join(
            (
                '{"id":"alpha","input":{"x":1},"expected_verdict":{"must_contain":[{"ok":true}]}}',
                '{"id":"beta","input":{"x":2},"expected_verdict":{"must_contain":[{"ok":true}]}}',
            )
        ),
        encoding="utf-8",
    )
    (eval_dir / "prompt.md").write_text(
        "Case {case_id}: {input_json}",
        encoding="utf-8",
    )
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()

    recorder = RecordingRunner(inner=StubModelRunner(response='{"ok": true}'))
    monkeypatch.setattr(run_module, "build_claude_runner", lambda **_: recorder)

    cli_runner = CliRunner()
    result = cli_runner.invoke(
        main,
        [
            "run",
            str(eval_dir / "eval.toml"),
            "--plugin-dir",
            str(plugin_dir),
            "--case-id",
            "beta",
        ],
    )

    assert result.exit_code == EXIT_SUCCESS
    assert len(recorder.transcripts) == 1
    captured_prompt, _ = recorder.transcripts[0]
    assert "Case beta" in captured_prompt
    assert "Case alpha" not in captured_prompt


def test_plan_subcommand_selects_smoke_cases_for_owned_path_change(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    eval_toml = _write_planned_eval(
        tmp_path,
        owned_paths=("src/plugins/spec-tree/skills/manage-pr/**",),
        smoke_cases=("happy-path",),
    )
    changed_paths = tmp_path / "changed.txt"
    changed_paths.write_text(
        "src/plugins/spec-tree/skills/manage-pr/SKILL.md\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "plan",
            str(tmp_path),
            "--mode",
            "pr",
            "--changed-paths-file",
            str(changed_paths),
        ],
    )

    assert result.exit_code == EXIT_SUCCESS
    plan = json.loads(result.output)
    assert plan == [
        {
            "eval_toml": str(eval_toml),
            "plugin_dir": "dist/claude/spec-tree",
            "case_ids": ["happy-path"],
        }
    ]


def test_plan_subcommand_selects_full_suite_when_harness_change_follows_owned_path(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    eval_toml = _write_planned_eval(
        tmp_path,
        owned_paths=("src/plugins/spec-tree/skills/manage-pr/**",),
        smoke_cases=("happy-path",),
    )
    changed_paths = tmp_path / "changed.txt"
    changed_paths.write_text(
        (
            "src/plugins/spec-tree/skills/manage-pr/SKILL.md\n"
            "outcomeeng_evals/suite.py\n"
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "plan",
            str(tmp_path),
            "--mode",
            "pr",
            "--changed-paths-file",
            str(changed_paths),
        ],
    )

    assert result.exit_code == EXIT_SUCCESS
    plan = json.loads(result.output)
    assert plan == [
        {
            "eval_toml": str(eval_toml),
            "plugin_dir": "dist/claude/spec-tree",
            "case_ids": [],
        }
    ]


def test_eval_workflow_collects_deleted_paths_for_planning() -> None:
    workflow_text = SPEC_TREE_EVALS_WORKFLOW.read_text(encoding="utf-8")

    assert "--diff-filter=ACDMRT" in workflow_text


def test_plan_subcommand_selects_full_suite_for_harness_change(tmp_path: Path) -> None:
    runner = CliRunner()
    eval_toml = _write_planned_eval(
        tmp_path,
        owned_paths=("src/plugins/spec-tree/skills/manage-pr/**",),
        smoke_cases=("happy-path",),
    )
    changed_paths = tmp_path / "changed.txt"
    changed_paths.write_text("outcomeeng_evals/suite.py\n", encoding="utf-8")

    result = runner.invoke(
        main,
        [
            "plan",
            str(tmp_path),
            "--mode",
            "pr",
            "--changed-paths-file",
            str(changed_paths),
        ],
    )

    assert result.exit_code == EXIT_SUCCESS
    plan = json.loads(result.output)
    assert plan == [
        {
            "eval_toml": str(eval_toml),
            "plugin_dir": "dist/claude/spec-tree",
            "case_ids": [],
        }
    ]


def test_plan_subcommand_selects_full_suite_for_absolute_eval_definition_change(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    eval_toml = _write_planned_eval(
        tmp_path,
        owned_paths=("src/plugins/spec-tree/skills/manage-pr/**",),
        smoke_cases=("happy-path",),
    )
    changed_paths = tmp_path / "changed.txt"
    changed_paths.write_text(
        f"{eval_toml.parent / 'cases.jsonl'}\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "plan",
            str(tmp_path),
            "--mode",
            "pr",
            "--changed-paths-file",
            str(changed_paths),
        ],
    )

    assert result.exit_code == EXIT_SUCCESS
    plan = json.loads(result.output)
    assert plan == [
        {
            "eval_toml": str(eval_toml),
            "plugin_dir": "dist/claude/spec-tree",
            "case_ids": [],
        }
    ]


def test_plan_subcommand_selects_full_suite_for_eval_definition_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    eval_root = Path("spx")
    eval_toml = _write_planned_eval(
        eval_root,
        owned_paths=("src/plugins/spec-tree/skills/manage-pr/**",),
        smoke_cases=("happy-path",),
    )
    changed_paths = Path("changed.txt")
    changed_paths.write_text(
        f"{eval_toml.parent.as_posix()}/cases.jsonl\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "plan",
            str(eval_root),
            "--mode",
            "pr",
            "--changed-paths-file",
            str(changed_paths),
        ],
    )

    assert result.exit_code == EXIT_SUCCESS
    plan = json.loads(result.output)
    assert plan == [
        {
            "eval_toml": str(eval_toml),
            "plugin_dir": "dist/claude/spec-tree",
            "case_ids": [],
        }
    ]


def test_plan_subcommand_full_mode_excludes_manual_evals(tmp_path: Path) -> None:
    runner = CliRunner()
    automatic_eval = _write_planned_eval(
        tmp_path,
        rule="automatic",
        owned_paths=("src/plugins/spec-tree/skills/manage-pr/**",),
        smoke_cases=("happy-path",),
    )
    _write_planned_eval(
        tmp_path,
        rule="manual",
        owned_paths=("src/plugins/spec-tree/skills/review-changes/**",),
        smoke_cases=("manual-smoke",),
        ci_policy=CiPolicy.MANUAL,
    )

    result = runner.invoke(
        main,
        [
            "plan",
            str(tmp_path),
            "--mode",
            "full",
        ],
    )

    assert result.exit_code == EXIT_SUCCESS
    plan = json.loads(result.output)
    assert plan == [
        {
            "eval_toml": str(automatic_eval),
            "plugin_dir": "dist/claude/spec-tree",
            "case_ids": [],
        }
    ]


def test_plan_subcommand_skips_unrelated_pr_change(tmp_path: Path) -> None:
    runner = CliRunner()
    _write_planned_eval(
        tmp_path,
        owned_paths=("src/plugins/spec-tree/skills/manage-pr/**",),
        smoke_cases=("happy-path",),
    )
    changed_paths = tmp_path / "changed.txt"
    changed_paths.write_text("README.md\n", encoding="utf-8")

    result = runner.invoke(
        main,
        [
            "plan",
            str(tmp_path),
            "--mode",
            "pr",
            "--changed-paths-file",
            str(changed_paths),
        ],
    )

    assert result.exit_code == EXIT_SUCCESS
    assert json.loads(result.output) == []


def _write_planned_eval(
    root: Path,
    *,
    rule: str = "rule",
    owned_paths: tuple[str, ...],
    smoke_cases: tuple[str, ...],
    ci_policy: CiPolicy | None = None,
) -> Path:
    eval_dir = root / "evals" / rule
    eval_dir.mkdir(parents=True)
    owned_paths_toml = ", ".join(f'"{path}"' for path in owned_paths)
    smoke_cases_toml = ", ".join(f'"{case_id}"' for case_id in smoke_cases)
    eval_toml = eval_dir / "eval.toml"
    lines = [
        f'title = "{rule}"',
        'cases = "cases.jsonl"',
        'prompt = "prompt.md"',
        'plugin_dir = "dist/claude/spec-tree"',
        f"owned_paths = [{owned_paths_toml}]",
        f"smoke_cases = [{smoke_cases_toml}]",
    ]
    if ci_policy is not None:
        lines.append(f'ci_policy = "{ci_policy.value}"')
    eval_toml.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    (eval_dir / "cases.jsonl").write_text("", encoding="utf-8")
    (eval_dir / "prompt.md").write_text("", encoding="utf-8")
    return eval_toml
