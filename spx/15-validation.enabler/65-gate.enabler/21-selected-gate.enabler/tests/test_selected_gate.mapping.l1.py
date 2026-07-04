"""Mapping evidence for selected local gate planning."""

from __future__ import annotations

from pathlib import Path

from outcomeeng.validation import (
    ACTIONLINT_ARGV,
    FMT_CHECK_ARGV,
    MYPY_ARGV,
    PYRIGHT_ARGV,
    PYTEST_ARGV,
    RUFF_CHECK_ARGV,
    RUFF_FORMAT_ARGV,
    SPX_MARKDOWN_ARGV,
    TEST_STEPS,
    SHELLCHECK_ARGV,
    VALIDATION_STEPS,
)
from outcomeeng.validation._git import GitCommandResult
from outcomeeng.validation.selected_gate import (
    DEFAULT_BASE_REF,
    FULL_GATE_REASON,
    FULL_GATE_PATTERNS,
    GIT_DIFF_BRANCH_ARGV_PREFIX,
    GIT_DIFF_STAGED_ARGV,
    GIT_DIFF_UNSTAGED_ARGV,
    GIT_LS_UNTRACKED_ARGV,
    PYTHON_ASSERTION_TEST_PATTERNS,
    PYTHON_PATTERNS,
    PYTHON_REASON,
    MARKDOWN_PATTERNS,
    MARKDOWN_REASON,
    SKILL_REASON,
    SKILL_PATTERNS,
    SKILL_STEP_LABELS,
    TEST_REASON,
    WORKFLOW_REASON,
    WORKFLOW_PATTERNS,
    build_selected_gate_plan,
    collect_changed_paths,
)
from outcomeeng_testing.harnesses.gate import RecordingGitRunner


def test_python_source_change_selects_python_validation_steps() -> None:
    plan = build_selected_gate_plan((PYTHON_PATTERNS[2],))

    assert tuple(item.step.argv for item in plan.selected_steps) == (
        RUFF_FORMAT_ARGV,
        RUFF_CHECK_ARGV,
        MYPY_ARGV,
        PYRIGHT_ARGV,
    )
    assert all(item.reason == PYTHON_REASON for item in plan.selected_steps)


def test_workflow_change_selects_workflow_validation_steps() -> None:
    plan = build_selected_gate_plan((WORKFLOW_PATTERNS[0],))

    assert tuple(item.step.argv for item in plan.selected_steps) == (
        ACTIONLINT_ARGV,
        SHELLCHECK_ARGV,
    )
    assert all(item.reason == WORKFLOW_REASON for item in plan.selected_steps)


def test_mixed_non_full_gate_paths_select_ordered_step_union() -> None:
    plan = build_selected_gate_plan(
        (
            PYTHON_PATTERNS[0],
            MARKDOWN_PATTERNS[0],
            WORKFLOW_PATTERNS[0],
        )
    )

    assert tuple(item.step.argv for item in plan.selected_steps) == (
        FMT_CHECK_ARGV,
        ACTIONLINT_ARGV,
        SHELLCHECK_ARGV,
        RUFF_FORMAT_ARGV,
        RUFF_CHECK_ARGV,
        MYPY_ARGV,
        PYRIGHT_ARGV,
        SPX_MARKDOWN_ARGV,
    )
    assert tuple(item.reason for item in plan.selected_steps) == (
        MARKDOWN_REASON,
        WORKFLOW_REASON,
        WORKFLOW_REASON,
        PYTHON_REASON,
        PYTHON_REASON,
        PYTHON_REASON,
        PYTHON_REASON,
        MARKDOWN_REASON,
    )


def test_changed_python_assertion_test_targets_pytest() -> None:
    test_path = PYTHON_ASSERTION_TEST_PATTERNS[0]
    plan = build_selected_gate_plan((test_path,))

    assert plan.selected_steps[-1].reason == TEST_REASON
    assert plan.selected_steps[-1].step.argv == (*PYTEST_ARGV, test_path)


def test_full_gate_surface_selects_all_declared_steps() -> None:
    plans = [build_selected_gate_plan((pattern,)) for pattern in FULL_GATE_PATTERNS]

    for plan in plans:
        assert plan.full_gate is True
        assert tuple(item.step for item in plan.selected_steps) == tuple(
            (*VALIDATION_STEPS, *TEST_STEPS)
        )
        assert all(item.reason == FULL_GATE_REASON for item in plan.selected_steps)


def test_skill_surface_selects_source_owned_skill_steps() -> None:
    plan = build_selected_gate_plan((SKILL_PATTERNS[0],))

    assert tuple(item.step.label for item in plan.selected_steps) == SKILL_STEP_LABELS
    assert all(item.reason == SKILL_REASON for item in plan.selected_steps)


def test_changed_path_collection_merges_branch_staged_unstaged_and_untracked(
    tmp_path: Path,
) -> None:
    branch_path = PYTHON_PATTERNS[0]
    staged_path = WORKFLOW_PATTERNS[0]
    unstaged_path = SKILL_PATTERNS[0]
    untracked_path = PYTHON_ASSERTION_TEST_PATTERNS[0]
    outputs = {
        (*GIT_DIFF_BRANCH_ARGV_PREFIX, f"{DEFAULT_BASE_REF}...HEAD"): branch_path,
        GIT_DIFF_STAGED_ARGV: staged_path,
        GIT_DIFF_UNSTAGED_ARGV: unstaged_path,
        GIT_LS_UNTRACKED_ARGV: untracked_path,
    }

    runner = RecordingGitRunner(
        outputs={
            command: GitCommandResult(returncode=0, stdout=f"{path}\n")
            for command, path in outputs.items()
        }
    )

    assert collect_changed_paths(tmp_path, runner=runner) == tuple(
        sorted((branch_path, staged_path, unstaged_path, untracked_path))
    )
    assert runner.repos == [tmp_path] * len(outputs)
