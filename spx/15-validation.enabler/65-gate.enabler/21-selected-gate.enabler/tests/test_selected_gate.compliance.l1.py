"""Compliance evidence for selected gate execution."""

from __future__ import annotations

import io
import os
from pathlib import Path

from outcomeeng.validation.selected_gate import (
    FULL_GATE_PATTERNS,
    GIT_DIFF_BRANCH_ARGV_PREFIX,
    GIT_DIFF_STAGED_ARGV,
    GIT_DIFF_UNSTAGED_ARGV,
    GIT_LS_UNTRACKED_ARGV,
    PYTHON_REASON,
    PYTHON_PATTERNS,
    build_selected_gate_plan,
    run_selected_check,
)
from outcomeeng.validation._git import GitCommandResult
from outcomeeng_testing.harnesses.gate import RecordingGitRunner, RecordingSpawner


def test_empty_selected_plan_has_no_recipe_steps() -> None:
    plan = build_selected_gate_plan(())

    assert plan.steps == ()
    assert plan.full_gate is False


def test_selected_check_prints_plan_before_orchestrator_output(tmp_path: Path) -> None:
    spawner = RecordingSpawner(exit_codes=[os.EX_OK])
    runner = RecordingGitRunner(
        outputs={
            (*GIT_DIFF_BRANCH_ARGV_PREFIX, "origin/main...HEAD"): GitCommandResult(
                returncode=0,
                stdout=f"{PYTHON_PATTERNS[0]}\n",
            ),
            GIT_DIFF_STAGED_ARGV: GitCommandResult(returncode=0, stdout=""),
            GIT_DIFF_UNSTAGED_ARGV: GitCommandResult(returncode=0, stdout=""),
            GIT_LS_UNTRACKED_ARGV: GitCommandResult(returncode=0, stdout=""),
        }
    )
    sink = io.StringIO()

    exit_code = run_selected_check(
        spawner=spawner,
        sink=sink,
        repo=tmp_path,
        runner=runner,
    )

    output = sink.getvalue()
    selected_block = (
        "━━━ Selected check plan ━━━\n"
        f"  ruff-format: {PYTHON_REASON}\n"
        f"  ruff: {PYTHON_REASON}\n"
        f"  mypy: {PYTHON_REASON}\n"
        f"  pyright: {PYTHON_REASON}\n"
    )
    assert exit_code == os.EX_OK
    assert output.startswith(selected_block)
    assert output.index(selected_block) < output.index("Recipe check")
    assert "Summary: " in output


def test_selected_check_uses_full_wrapper_for_full_gate_surface(
    tmp_path: Path,
) -> None:
    spawner = RecordingSpawner(exit_codes=[os.EX_OK])
    runner = RecordingGitRunner(
        outputs={
            (*GIT_DIFF_BRANCH_ARGV_PREFIX, "origin/main...HEAD"): GitCommandResult(
                returncode=0,
                stdout=f"{FULL_GATE_PATTERNS[0]}\n",
            ),
            GIT_DIFF_STAGED_ARGV: GitCommandResult(returncode=0, stdout=""),
            GIT_DIFF_UNSTAGED_ARGV: GitCommandResult(returncode=0, stdout=""),
            GIT_LS_UNTRACKED_ARGV: GitCommandResult(returncode=0, stdout=""),
        }
    )
    sink = io.StringIO()

    exit_code = run_selected_check(
        spawner=spawner,
        sink=sink,
        repo=tmp_path,
        runner=runner,
    )

    output = sink.getvalue()
    assert exit_code == os.EX_OK
    assert "full gate surface changed" in output
    assert "Recipe validation" in output
