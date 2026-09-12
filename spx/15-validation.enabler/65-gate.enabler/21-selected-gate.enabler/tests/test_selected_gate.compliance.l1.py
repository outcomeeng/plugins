"""Compliance evidence for selected gate execution."""

from __future__ import annotations

import pytest

from outcomeeng.validation import (
    CHECK_RECIPES,
    PYTEST_ARGV,
    RECIPE_CHECK,
    RECIPE_TEST,
    RECIPE_VALIDATION,
)
from outcomeeng.validation.infrastructure_index import (
    InfrastructureReach,
    index_test_infrastructure,
)
from outcomeeng.validation.selected_gate import (
    FULL_GATE_REASON,
    GIT_DISCOVERY_ERROR_PREFIX,
    GIT_DISCOVERY_FAILURE_EXIT_CODE,
    GIT_DISCOVERY_STDERR_LABEL,
    GIT_DISCOVERY_STDOUT_LABEL,
    GitDiscoveryError,
    InfrastructureIndexRequired,
    INSTRUCTION_BLOCK_SOURCE_PATH,
    LIVE_DISCOVERY_EXCLUSION,
    LIVE_DISCOVERY_EXCLUDED_REASON,
    LIVE_DISCOVERY_INCLUDED_REASON,
    LIVE_DISCOVERY_TEST,
    PYTHON_REASON,
    TEST_REASON,
    build_selected_gate_plan,
)
from outcomeeng_testing.generators.gate import (
    SELECTED_GATE_FULL_GATE_PATH,
    SELECTED_GATE_PYTHON_SOURCE_PATH,
    SELECTED_GATE_PYTHON_TEST_PATH,
)
from outcomeeng_testing.harnesses.gate import (
    GIT_DISCOVERY_FAILURE_STDERR,
    GIT_DISCOVERY_FAILURE_STDOUT,
    HIGH_VOLUME_CHILD_OUTPUT,
    collect_selected_gate_paths,
    expected_full_check_spawn_calls,
    failing_discovery_runner,
    missing_origin_observation,
    run_check_observation,
    selected_check_plan_block,
    selected_gate_branch_discovery_argv,
    unrelated_validation_source_path,
)
from outcomeeng_testing.harnesses.infrastructure_index import (
    reach_layout,
    synthetic_repository,
)


def test_an_empty_changeset_selects_no_steps() -> None:
    plan = build_selected_gate_plan(())

    assert plan.steps == ()
    assert plan.full_gate is False


def test_the_plan_prints_before_the_recipes_run() -> None:
    run = run_check_observation(branch_path=SELECTED_GATE_PYTHON_SOURCE_PATH)

    expected_plan = build_selected_gate_plan((SELECTED_GATE_PYTHON_SOURCE_PATH,))
    selected_block = selected_check_plan_block(
        labels=tuple(item.step.label for item in expected_plan.selected_steps),
        reason=PYTHON_REASON,
    )
    assert run.exit_code == 0
    assert run.output.startswith(selected_block)
    assert run.output.index(selected_block) < run.output.index(f"Recipe {RECIPE_CHECK}")
    assert "Summary: " in run.output


def test_child_output_never_streams_to_the_live_sink() -> None:
    run = run_check_observation(
        branch_path=SELECTED_GATE_PYTHON_SOURCE_PATH,
        child_output=HIGH_VOLUME_CHILD_OUTPUT,
    )

    assert run.exit_code == 0
    assert HIGH_VOLUME_CHILD_OUTPUT not in run.output
    assert len(run.output.splitlines()) < len(HIGH_VOLUME_CHILD_OUTPUT.splitlines())


def test_a_full_gate_path_runs_the_complete_wrapper() -> None:
    run = run_check_observation(branch_path=SELECTED_GATE_FULL_GATE_PATH)

    assert run.exit_code == 0
    assert run.spawn_calls == expected_full_check_spawn_calls()
    assert FULL_GATE_REASON in run.output
    assert f"Recipe {RECIPE_VALIDATION}" in run.output
    assert f"Recipe {RECIPE_TEST}" in run.output


def test_a_deleted_test_path_selects_no_pytest_run() -> None:
    run = run_check_observation(
        branch_path=SELECTED_GATE_PYTHON_TEST_PATH,
        branch_status="D",
    )

    assert run.exit_code == 0
    assert all(PYTEST_ARGV != call[: len(PYTEST_ARGV)] for call in run.spawn_calls)
    assert TEST_REASON not in run.output


def test_git_discovery_failure_stops_before_any_spawn() -> None:
    run = run_check_observation(
        branch_path=GIT_DISCOVERY_FAILURE_STDOUT,
        branch_returncode=GIT_DISCOVERY_FAILURE_EXIT_CODE,
        branch_stderr=GIT_DISCOVERY_FAILURE_STDERR,
    )

    assert run.exit_code == GIT_DISCOVERY_FAILURE_EXIT_CODE
    assert run.spawn_calls == ()
    assert run.runner_calls == (selected_gate_branch_discovery_argv(),)
    assert GIT_DISCOVERY_ERROR_PREFIX in run.output
    assert GIT_DISCOVERY_STDOUT_LABEL in run.output
    assert GIT_DISCOVERY_STDERR_LABEL in run.output
    assert GIT_DISCOVERY_FAILURE_STDOUT in run.output
    assert GIT_DISCOVERY_FAILURE_STDERR in run.output


def test_a_repo_without_origin_reports_the_unset_head() -> None:
    run = missing_origin_observation()

    assert run.exit_code == GIT_DISCOVERY_FAILURE_EXIT_CODE
    assert run.spawn_calls == ()
    assert GIT_DISCOVERY_ERROR_PREFIX in run.output
    assert "refs/remotes/origin/HEAD unset" in run.output


def test_collection_propagates_git_failure_as_a_typed_error() -> None:
    runner = failing_discovery_runner()

    with pytest.raises(GitDiscoveryError) as caught:
        with synthetic_repository() as repo:
            collect_selected_gate_paths(repo.root, runner=runner)

    assert GIT_DISCOVERY_ERROR_PREFIX in str(caught.value)
    assert GIT_DISCOVERY_FAILURE_STDERR in str(caught.value)
    assert runner.calls == [selected_gate_branch_discovery_argv()]


def test_infrastructure_path_without_an_index_is_rejected_by_name() -> None:
    with synthetic_repository() as repo:
        layout = reach_layout(InfrastructureReach.NODE_LOCAL, repo)

    with pytest.raises(InfrastructureIndexRequired) as caught:
        build_selected_gate_plan((layout.changed_path,))

    assert caught.value.paths == (layout.changed_path,)
    assert layout.changed_path in str(caught.value)


def test_definition_guidance_changes_require_the_live_check() -> None:
    plan = build_selected_gate_plan((INSTRUCTION_BLOCK_SOURCE_PATH,))

    assert plan.live_discovery
    assert any(LIVE_DISCOVERY_TEST in step.argv for step in plan.steps)
    assert plan.live_discovery_reason == LIVE_DISCOVERY_INCLUDED_REASON


def test_unrelated_automatic_full_gate_excludes_only_the_live_check() -> None:
    with synthetic_repository() as repo:
        layout = reach_layout(InfrastructureReach.SHARED, repo)
        plan = build_selected_gate_plan(
            (layout.changed_path,),
            test_infrastructure=index_test_infrastructure(repo.root),
        )

    assert plan.full_gate
    assert not plan.live_discovery
    assert tuple(
        step.argv[: -len(LIVE_DISCOVERY_EXCLUSION)]
        if step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
        else step.argv
        for step in plan.steps
    ) == tuple(step.argv for recipe in CHECK_RECIPES for step in recipe.steps)
    assert all(
        step.argv[-len(LIVE_DISCOVERY_EXCLUSION) :] == LIVE_DISCOVERY_EXCLUSION
        for step in plan.steps
        if step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
    )


def test_unrelated_full_gate_execution_honors_its_exclusion() -> None:
    run = run_check_observation(branch_path=unrelated_validation_source_path())

    assert run.exit_code == 0
    assert any(
        call[: len(PYTEST_ARGV)] == PYTEST_ARGV
        and call[-len(LIVE_DISCOVERY_EXCLUSION) :] == LIVE_DISCOVERY_EXCLUSION
        for call in run.spawn_calls
    )
    assert run.output.index(LIVE_DISCOVERY_EXCLUDED_REASON) < run.output.index(
        f"Recipe {RECIPE_VALIDATION}"
    )


def test_relevant_full_gate_keeps_live_discovery_enabled() -> None:
    plan = build_selected_gate_plan((SELECTED_GATE_FULL_GATE_PATH,))

    assert plan.full_gate
    assert plan.live_discovery
    assert plan.steps == tuple(
        step for recipe in CHECK_RECIPES for step in recipe.steps
    )
