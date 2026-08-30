"""Mapping evidence for selected local gate planning."""

from __future__ import annotations

import pytest

from outcomeeng.distribution.contracts import INSTRUCTION_BLOCK_ARGV
from outcomeeng.validation import (
    ACTIONLINT_ARGV,
    EVAL_PROMPTS_ARGV,
    EVAL_TRIGGERS_ARGV,
    FMT_CHECK_ARGV,
    MYPY_ARGV,
    PYRIGHT_ARGV,
    PYTEST_ARGV,
    RUFF_CHECK_ARGV,
    RUFF_FORMAT_ARGV,
    SHELLCHECK_ARGV,
    SPX_MARKDOWN_ARGV,
    TEST_STEPS,
    VALIDATION_STEPS,
)
from outcomeeng.validation.infrastructure_index import InfrastructureReach
from outcomeeng.validation.selected_gate import (
    ChangedPath,
    EVAL_REASON,
    FULL_GATE_REASON,
    INSTRUCTION_BLOCK_REASON,
    MARKDOWN_REASON,
    PYTHON_REASON,
    REACHED_TESTS_REASON,
    SHARED_TEST_INFRASTRUCTURE_REASON,
    SKILL_REASON,
    SKILL_STEP_LABELS,
    SelectedGatePlan,
    TEST_REASON,
    UNTRACEABLE_TEST_INFRASTRUCTURE_REASON,
    WORKFLOW_REASON,
    build_selected_gate_plan,
    deleted_paths_after_status_resolution,
)
from outcomeeng_testing.generators.gate import (
    SELECTED_GATE_CHECK_WORKFLOW_PATH,
    SELECTED_GATE_EVAL_DEFINITION_PATH,
    SELECTED_GATE_EVAL_WORKFLOW_PATH,
    SELECTED_GATE_FULL_GATE_PATH,
    SELECTED_GATE_INSTRUCTION_BLOCK_SOURCE_PATH,
    SELECTED_GATE_MARKDOWN_PATH,
    SELECTED_GATE_PLUGIN_SCRIPT_PATH,
    SELECTED_GATE_PYTHON_SOURCE_PATH,
    SELECTED_GATE_PYTHON_TEST_PATH,
    SELECTED_GATE_README_PATH,
    SELECTED_GATE_SHARED_SOURCE_PATH,
    SELECTED_GATE_SKILL_PATH,
    SELECTED_GATE_SPX_CONFIG_PATH,
    SELECTED_GATE_TEMPLATE_SCRIPT_PATH,
    SELECTED_GATE_WORKFLOW_PATH,
)
from outcomeeng_testing.harnesses import gate as gate_harness
from outcomeeng_testing.harnesses.gate import (
    PYTEST_TARGET_ARG,
    SELECTED_GATE_RENAMED_TARGET_ARG,
    SELECTED_GATE_WHITESPACE_PATH,
    collected_paths_observation,
    resolved_base_observation,
    run_check_observation,
    selected_gate_branch_discovery_argv,
    selected_gate_changed_path_domain,
)
from outcomeeng_testing.harnesses.infrastructure_index import (
    conftest_reach_layout,
    mixed_reach_layout,
    reach_layout,
    repository_reach,
    synthetic_repository,
)


def _argvs(plan: SelectedGatePlan) -> tuple[tuple[str, ...], ...]:
    return tuple(item.step.argv for item in plan.selected_steps)


def _reasons(plan: SelectedGatePlan) -> tuple[str, ...]:
    return tuple(item.reason for item in plan.selected_steps)


def test_a_python_source_path_selects_lint_and_type_steps() -> None:
    plan = build_selected_gate_plan((SELECTED_GATE_PYTHON_SOURCE_PATH,))

    assert plan.full_gate is False
    assert _argvs(plan) == (RUFF_FORMAT_ARGV, RUFF_CHECK_ARGV, MYPY_ARGV, PYRIGHT_ARGV)
    assert set(_reasons(plan)) == {PYTHON_REASON}


def test_a_workflow_path_selects_the_workflow_linters() -> None:
    plan = build_selected_gate_plan((SELECTED_GATE_WORKFLOW_PATH,))

    assert plan.full_gate is False
    assert _argvs(plan) == (ACTIONLINT_ARGV, SHELLCHECK_ARGV)
    assert set(_reasons(plan)) == {WORKFLOW_REASON}


def test_the_eval_workflow_selects_the_trigger_currency_check() -> None:
    # The eval workflow carries the generated trigger blocks, so editing it
    # selects the trigger currency check alongside the workflow linters. It
    # carries no producer, so the prompt check stays unselected.
    plan = build_selected_gate_plan((SELECTED_GATE_EVAL_WORKFLOW_PATH,))

    assert plan.full_gate is False
    assert _argvs(plan) == (ACTIONLINT_ARGV, SHELLCHECK_ARGV, EVAL_TRIGGERS_ARGV)
    assert _reasons(plan) == (WORKFLOW_REASON, WORKFLOW_REASON, EVAL_REASON)


def test_an_eval_definition_selects_both_currency_checks() -> None:
    # An eval definition generates both the CI trigger list and, for a
    # producer-coupled suite, the materialized prompt — so it selects both
    # currency checks, alongside the markdown lane its `spx/**` path matches.
    plan = build_selected_gate_plan((SELECTED_GATE_EVAL_DEFINITION_PATH,))

    assert plan.full_gate is False
    assert _argvs(plan) == (
        FMT_CHECK_ARGV,
        EVAL_TRIGGERS_ARGV,
        EVAL_PROMPTS_ARGV,
        SPX_MARKDOWN_ARGV,
    )
    assert _reasons(plan) == (
        MARKDOWN_REASON,
        EVAL_REASON,
        EVAL_REASON,
        MARKDOWN_REASON,
    )


def test_combined_paths_merge_lanes_in_validation_step_order() -> None:
    plan = build_selected_gate_plan(
        (
            SELECTED_GATE_PYTHON_SOURCE_PATH,
            SELECTED_GATE_MARKDOWN_PATH,
            SELECTED_GATE_WORKFLOW_PATH,
        )
    )

    assert plan.full_gate is False
    assert _argvs(plan) == (
        FMT_CHECK_ARGV,
        ACTIONLINT_ARGV,
        SHELLCHECK_ARGV,
        RUFF_FORMAT_ARGV,
        RUFF_CHECK_ARGV,
        MYPY_ARGV,
        PYRIGHT_ARGV,
        SPX_MARKDOWN_ARGV,
    )
    assert _reasons(plan) == (
        MARKDOWN_REASON,
        WORKFLOW_REASON,
        WORKFLOW_REASON,
        PYTHON_REASON,
        PYTHON_REASON,
        PYTHON_REASON,
        PYTHON_REASON,
        MARKDOWN_REASON,
    )


def test_deleted_assertion_tests_never_select_pytest() -> None:
    test_path = SELECTED_GATE_PYTHON_TEST_PATH

    plan = build_selected_gate_plan((test_path,), deleted_paths=(test_path,))
    assert all(item.reason != TEST_REASON for item in plan.selected_steps)

    deleted_paths = deleted_paths_after_status_resolution(
        (
            ChangedPath(path=test_path, status="M"),
            ChangedPath(path=test_path, status="D"),
        )
    )
    plan = build_selected_gate_plan((test_path,), deleted_paths=deleted_paths)
    assert all(item.reason != TEST_REASON for item in plan.selected_steps)

    plan = build_selected_gate_plan(
        (test_path, PYTEST_TARGET_ARG),
        deleted_paths=(test_path,),
    )
    assert plan.selected_steps[-1].reason == TEST_REASON
    assert plan.selected_steps[-1].step.argv == (*PYTEST_ARGV, PYTEST_TARGET_ARG)


@pytest.mark.parametrize(
    "path",
    (
        SELECTED_GATE_FULL_GATE_PATH,
        SELECTED_GATE_CHECK_WORKFLOW_PATH,
        "outcomeeng/validation/selected_gate.py",
    ),
)
def test_full_gate_paths_select_the_complete_recipe_set(path: str) -> None:
    plan = build_selected_gate_plan((path,))

    assert plan.full_gate is True
    assert plan.steps == (*VALIDATION_STEPS, *TEST_STEPS)
    assert set(_reasons(plan)) == {FULL_GATE_REASON}


@pytest.mark.parametrize(
    "path", (SELECTED_GATE_README_PATH, SELECTED_GATE_SPX_CONFIG_PATH)
)
def test_markdown_only_paths_select_the_markdown_lane(path: str) -> None:
    plan = build_selected_gate_plan((path,))

    assert plan.full_gate is False
    assert _argvs(plan) == (FMT_CHECK_ARGV, SPX_MARKDOWN_ARGV)
    assert set(_reasons(plan)) == {MARKDOWN_REASON}


def test_a_skill_path_selects_skill_steps_with_the_prompt_check() -> None:
    # An authored plugin file may be a producer for a producer-coupled eval
    # prompt, so the prompt currency check joins the skill and markdown steps.
    plan = build_selected_gate_plan((SELECTED_GATE_SKILL_PATH,))

    expected = tuple(
        step
        for step in VALIDATION_STEPS
        if step.label in SKILL_STEP_LABELS
        or step.argv in {FMT_CHECK_ARGV, SPX_MARKDOWN_ARGV, EVAL_PROMPTS_ARGV}
    )
    assert plan.steps == expected
    assert _reasons(plan) == tuple(
        expected_skill_reason(step.argv) for step in expected
    )


def test_a_plugin_script_selects_skill_and_python_lint_steps() -> None:
    plan = build_selected_gate_plan((SELECTED_GATE_PLUGIN_SCRIPT_PATH,))

    expected = tuple(
        step
        for step in VALIDATION_STEPS
        if step.label in SKILL_STEP_LABELS
        or step.argv in {RUFF_FORMAT_ARGV, RUFF_CHECK_ARGV, EVAL_PROMPTS_ARGV}
    )
    assert plan.steps == expected
    assert _reasons(plan) == tuple(
        PYTHON_REASON
        if step.argv in {RUFF_FORMAT_ARGV, RUFF_CHECK_ARGV}
        else EVAL_REASON
        if step.argv == EVAL_PROMPTS_ARGV
        else SKILL_REASON
        for step in expected
    )


def test_a_shared_fragment_selects_skill_and_markdown_steps() -> None:
    # A shared fragment is inlined by the build; an eval names its producer by
    # an authored `src/plugins/` path, so no shared-fragment edit stales a
    # materialized prompt and the prompt check stays unselected here.
    plan = build_selected_gate_plan((SELECTED_GATE_SHARED_SOURCE_PATH,))

    expected = tuple(
        step
        for step in VALIDATION_STEPS
        if step.label in SKILL_STEP_LABELS
        or step.argv in {FMT_CHECK_ARGV, SPX_MARKDOWN_ARGV}
    )
    assert plan.steps == expected
    assert _reasons(plan) == tuple(
        MARKDOWN_REASON
        if step.argv in {FMT_CHECK_ARGV, SPX_MARKDOWN_ARGV}
        else SKILL_REASON
        for step in expected
    )


def test_the_instruction_block_source_selects_the_currency_check() -> None:
    plan = build_selected_gate_plan((SELECTED_GATE_INSTRUCTION_BLOCK_SOURCE_PATH,))

    assert INSTRUCTION_BLOCK_ARGV in _argvs(plan)
    assert (
        next(
            item.reason
            for item in plan.selected_steps
            if item.step.argv == INSTRUCTION_BLOCK_ARGV
        )
        == INSTRUCTION_BLOCK_REASON
    )


def test_changed_paths_collect_from_all_four_git_surfaces() -> None:
    branch_path, staged_path, unstaged_path, untracked_path = (
        selected_gate_changed_path_domain()
    )

    observation = collected_paths_observation(
        branch_path=branch_path,
        staged_path=staged_path,
        unstaged_path=unstaged_path,
        untracked_path=untracked_path,
    )

    assert observation.collected == tuple(sorted(observation.inputs))
    assert observation.runner_repos == (observation.repo,) * observation.command_count


def test_whitespace_paths_survive_collection() -> None:
    observation = collected_paths_observation(
        branch_path=SELECTED_GATE_WHITESPACE_PATH,
        staged_path=SELECTED_GATE_WHITESPACE_PATH,
        unstaged_path=SELECTED_GATE_WHITESPACE_PATH,
        untracked_path=SELECTED_GATE_WHITESPACE_PATH,
    )

    assert observation.collected == (SELECTED_GATE_WHITESPACE_PATH,)


def test_an_injected_base_ref_resolver_drives_branch_discovery() -> None:
    observation = resolved_base_observation()

    assert observation.collected == (observation.branch_path,)
    assert observation.resolver_repos == (observation.repo,)
    assert observation.first_runner_call == selected_gate_branch_discovery_argv(
        base_ref=observation.base_ref
    )


def test_a_rename_collects_both_sides() -> None:
    observation = collected_paths_observation(
        branch_old_path=SELECTED_GATE_PYTHON_TEST_PATH,
        branch_path=SELECTED_GATE_RENAMED_TARGET_ARG,
        branch_status="R100",
    )

    assert observation.collected == tuple(
        sorted((SELECTED_GATE_PYTHON_TEST_PATH, SELECTED_GATE_RENAMED_TARGET_ARG))
    )


def test_a_renamed_test_source_never_reaches_pytest() -> None:
    run = run_check_observation(
        branch_old_path=SELECTED_GATE_PYTHON_TEST_PATH,
        branch_path=SELECTED_GATE_RENAMED_TARGET_ARG,
        branch_status="R100",
    )

    assert run.exit_code == 0
    assert all(PYTEST_ARGV != call[: len(PYTEST_ARGV)] for call in run.spawn_calls)


def test_a_deleted_then_modified_test_still_runs_when_present() -> None:
    run = run_check_observation(
        branch_path=SELECTED_GATE_PYTHON_TEST_PATH,
        branch_status="D",
        staged_path=SELECTED_GATE_PYTHON_TEST_PATH,
        staged_status="M",
        create_repo_file=SELECTED_GATE_PYTHON_TEST_PATH,
    )

    assert run.exit_code == 0
    assert run.spawn_calls[-1] == (*PYTEST_ARGV, SELECTED_GATE_PYTHON_TEST_PATH)


def test_a_copied_test_selects_pytest_for_the_surviving_source() -> None:
    run = run_check_observation(
        branch_old_path=SELECTED_GATE_PYTHON_TEST_PATH,
        branch_path=SELECTED_GATE_RENAMED_TARGET_ARG,
        branch_status="C100",
    )

    assert run.exit_code == 0
    assert (*PYTEST_ARGV, SELECTED_GATE_PYTHON_TEST_PATH) in run.spawn_calls


@pytest.mark.parametrize("kind", list(InfrastructureReach), ids=str)
def test_test_infrastructure_reach_maps_to_gate_steps(
    kind: InfrastructureReach,
) -> None:
    with synthetic_repository() as repo:
        layout = reach_layout(kind, repo)

    plan = build_selected_gate_plan(
        (layout.changed_path,), test_infrastructure=layout.index
    )
    pytest_steps = [
        item
        for item in plan.selected_steps
        if item.step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
    ]

    if kind is InfrastructureReach.NODE_LOCAL:
        assert plan.full_gate is False
        assert [item.step.argv for item in pytest_steps] == [
            (*PYTEST_ARGV, *layout.tests)
        ]
        assert [item.reason for item in pytest_steps] == [REACHED_TESTS_REASON]
    elif kind is InfrastructureReach.SHARED:
        assert plan.full_gate is True
        assert plan.steps == (*VALIDATION_STEPS, *TEST_STEPS)
        assert set(_reasons(plan)) == {SHARED_TEST_INFRASTRUCTURE_REASON}
    elif kind is InfrastructureReach.UNTRACEABLE:
        assert plan.full_gate is True
        assert plan.steps == (*VALIDATION_STEPS, *TEST_STEPS)
        assert set(_reasons(plan)) == {UNTRACEABLE_TEST_INFRASTRUCTURE_REASON}
    else:
        assert kind is InfrastructureReach.UNREACHED
        assert plan.full_gate is False
        assert pytest_steps == []


def test_module_reached_by_conftest_selects_the_full_surface() -> None:
    with synthetic_repository() as repo:
        layout = conftest_reach_layout(repo)

    plan = build_selected_gate_plan(
        (layout.changed_path,), test_infrastructure=layout.index
    )

    assert layout.index.reach(layout.changed_path).kind is InfrastructureReach.SHARED
    assert plan.full_gate is True
    assert set(_reasons(plan)) == {SHARED_TEST_INFRASTRUCTURE_REASON}


def test_step_fed_by_changed_and_reached_tests_names_both_reasons() -> None:
    with synthetic_repository() as repo:
        layout = mixed_reach_layout(repo)

    plan = build_selected_gate_plan(
        (layout.changed_path, layout.changed_test),
        test_infrastructure=layout.index,
    )
    pytest_steps = [
        item
        for item in plan.selected_steps
        if item.step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
    ]

    assert plan.full_gate is False
    assert [item.step.argv for item in pytest_steps] == [
        (*PYTEST_ARGV, *sorted((layout.changed_test, *layout.reached_tests)))
    ]
    assert TEST_REASON in pytest_steps[0].reason
    assert REACHED_TESTS_REASON in pytest_steps[0].reason


def test_the_gate_harness_shared_with_the_parent_node_selects_the_full_surface() -> (
    None
):
    # This file and the parent node's tests both import the gate harness, so
    # the real checkout is the case: a change to that harness is shared.
    observation = repository_reach(gate_harness.__file__)

    plan = build_selected_gate_plan(
        (observation.path,), test_infrastructure=observation.index
    )

    assert observation.index.reach(observation.path).kind is InfrastructureReach.SHARED
    assert plan.full_gate is True
    assert set(_reasons(plan)) == {SHARED_TEST_INFRASTRUCTURE_REASON}


def test_template_script_maps_to_skill_and_lint_steps() -> None:
    # The template tree is an authored source root the generated-source
    # declaration and the raw-token enforcement roots both name, so a change to
    # a shipped template script has to reach the build, drift, and lint steps
    # that carry it into every plugin's generated tree. An eval names its
    # producer by an authored `src/plugins/` path, so a template edit stales no
    # materialized prompt and the prompt check stays unselected.
    plan = build_selected_gate_plan((SELECTED_GATE_TEMPLATE_SCRIPT_PATH,))

    expected = tuple(
        step
        for step in VALIDATION_STEPS
        if step.label in SKILL_STEP_LABELS
        or step.argv in {RUFF_FORMAT_ARGV, RUFF_CHECK_ARGV}
    )
    assert plan.full_gate is False
    assert plan.steps == expected
    assert _reasons(plan) == tuple(
        PYTHON_REASON
        if step.argv in {RUFF_FORMAT_ARGV, RUFF_CHECK_ARGV}
        else SKILL_REASON
        for step in expected
    )
