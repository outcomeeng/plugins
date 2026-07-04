"""Compliance evidence for selected gate execution."""

from __future__ import annotations

import io
import os
from pathlib import Path

import pytest

from outcomeeng.validation import CHECK_RECIPES, PREFLIGHT_STEPS
from outcomeeng.validation.selected_gate import (
    DEFAULT_BASE_REF,
    FULL_GATE_PATTERNS,
    GIT_DISCOVERY_ERROR_PREFIX,
    GIT_DISCOVERY_FAILURE_EXIT_CODE,
    GIT_DIFF_BRANCH_ARGV_PREFIX,
    GIT_DIFF_STAGED_ARGV,
    GIT_DIFF_UNSTAGED_ARGV,
    GIT_LS_UNTRACKED_ARGV,
    PYTHON_REASON,
    PYTHON_PATTERNS,
    build_selected_gate_plan,
    collect_changed_paths,
    run_selected_check,
)
from outcomeeng.validation._git import GitCommandResult
from outcomeeng_testing.harnesses.gate import (
    RecordingGitRunner,
    RecordingSpawner,
    selected_check_plan_block,
)


def test_empty_selected_plan_has_no_recipe_steps() -> None:
    plan = build_selected_gate_plan(())

    assert plan.steps == ()
    assert plan.full_gate is False


def test_selected_check_prints_plan_before_orchestrator_output(tmp_path: Path) -> None:
    spawner = RecordingSpawner(exit_codes=[os.EX_OK])
    runner = RecordingGitRunner(
        outputs={
            (
                *GIT_DIFF_BRANCH_ARGV_PREFIX,
                f"{DEFAULT_BASE_REF}...HEAD",
            ): GitCommandResult(
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
    expected_plan = build_selected_gate_plan((PYTHON_PATTERNS[0],))
    selected_block = selected_check_plan_block(
        labels=tuple(item.step.label for item in expected_plan.selected_steps),
        reason=PYTHON_REASON,
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
            (
                *GIT_DIFF_BRANCH_ARGV_PREFIX,
                f"{DEFAULT_BASE_REF}...HEAD",
            ): GitCommandResult(
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
    expected_spawn_calls = tuple(
        step.argv
        for recipe in CHECK_RECIPES
        for step in (*PREFLIGHT_STEPS, *recipe.steps)
    )
    assert exit_code == os.EX_OK
    assert tuple(spawner.spawn_calls) == expected_spawn_calls
    assert "full gate surface changed" in output
    assert "Recipe validation" in output
    assert "Recipe test" in output


def test_selected_check_fails_when_git_discovery_fails(tmp_path: Path) -> None:
    failed_branch_command = (
        *GIT_DIFF_BRANCH_ARGV_PREFIX,
        f"{DEFAULT_BASE_REF}...HEAD",
    )
    spawner = RecordingSpawner(exit_codes=[os.EX_OK])
    runner = RecordingGitRunner(
        outputs={
            failed_branch_command: GitCommandResult(
                returncode=GIT_DISCOVERY_FAILURE_EXIT_CODE,
                stdout="fatal: bad revision\n",
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
    assert exit_code == GIT_DISCOVERY_FAILURE_EXIT_CODE
    assert spawner.spawn_calls == []
    assert runner.calls == [failed_branch_command]
    assert GIT_DISCOVERY_ERROR_PREFIX in output
    assert "fatal: bad revision" in output


def test_changed_path_collection_rejects_failed_git_discovery(tmp_path: Path) -> None:
    failed_branch_command = (
        *GIT_DIFF_BRANCH_ARGV_PREFIX,
        f"{DEFAULT_BASE_REF}...HEAD",
    )
    runner = RecordingGitRunner(
        outputs={
            failed_branch_command: GitCommandResult(
                returncode=GIT_DISCOVERY_FAILURE_EXIT_CODE,
                stdout="fatal: bad revision\n",
            ),
            GIT_DIFF_STAGED_ARGV: GitCommandResult(returncode=0, stdout=""),
            GIT_DIFF_UNSTAGED_ARGV: GitCommandResult(returncode=0, stdout=""),
            GIT_LS_UNTRACKED_ARGV: GitCommandResult(returncode=0, stdout=""),
        }
    )

    with pytest.raises(RuntimeError, match=GIT_DISCOVERY_ERROR_PREFIX):
        collect_changed_paths(tmp_path, runner=runner)

    assert runner.calls == [failed_branch_command]
