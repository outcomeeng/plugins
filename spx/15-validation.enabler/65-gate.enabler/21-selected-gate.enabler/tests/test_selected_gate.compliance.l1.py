"""Compliance evidence for selected gate execution."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from outcomeeng.validation import (
    CHECK_RECIPES,
    PREFLIGHT_STEPS,
    PYTEST_ARGV,
    RECIPE_CHECK,
    RECIPE_TEST,
    RECIPE_VALIDATION,
)
from outcomeeng.distribution import agents as agent_conversion
from outcomeeng.validation import selected_gate as selection_source
from outcomeeng.validation.infrastructure_index import (
    InfrastructureReach,
    index_test_infrastructure,
)
from outcomeeng.validation.selected_gate import (
    CHECK_WORKFLOW_PATH,
    FULL_GATE_REASON,
    GIT_DISCOVERY_ERROR_PREFIX,
    GIT_DISCOVERY_FAILURE_EXIT_CODE,
    GIT_DISCOVERY_STDERR_LABEL,
    GIT_DISCOVERY_STDOUT_LABEL,
    GitDiscoveryError,
    InfrastructureIndexRequired,
    INSTRUCTION_BLOCK_SOURCE_PATH,
    PYPROJECT_PATH,
    PYTHON_REASON,
    REAL_AGENT_CODEX_EXCLUDED_REASON,
    REAL_AGENT_CODEX_EXCLUSION,
    REAL_AGENT_CODEX_INCLUDED_REASON,
    REAL_AGENT_CODEX_TESTS,
    SelectedGatePlan,
    TEST_REASON,
    build_full_gate_plan,
    build_selected_gate_plan,
)
from outcomeeng_testing.generators.gate import (
    SELECTED_GATE_FULL_GATE_PATH,
    SELECTED_GATE_MARKDOWN_PATH,
    SELECTED_GATE_PYTHON_SOURCE_PATH,
    SELECTED_GATE_PYTHON_TEST_PATH,
    path_from_pattern,
)
from outcomeeng_testing.harnesses import discovery_auth as discovery_auth_harness
from outcomeeng_testing.harnesses import installation as installation_harness
from outcomeeng_testing.harnesses.gate import (
    GIT_DISCOVERY_FAILURE_STDERR,
    GIT_DISCOVERY_FAILURE_STDOUT,
    HIGH_VOLUME_CHILD_OUTPUT,
    RunObservation,
    collect_selected_gate_paths,
    failing_discovery_runner,
    missing_origin_observation,
    run_check_observation,
    selected_check_plan_block,
    selected_gate_branch_discovery_argv,
    unrelated_validation_source_path,
)
from outcomeeng_testing.harnesses.infrastructure_index import (
    reach_layout,
    repository_reach,
    synthetic_repository,
)
from outcomeeng_testing.harnesses.real_agent_selection import (
    checkout_agent_definition_paths,
    codex_credential_environment,
    pytest_collection_observation,
    repository_relative_path,
    run_full_check_observation,
)

# Every changed-path category the selector owns other than agent definitions.
NON_AGENT_DEFINITION_CATEGORIES = (
    selection_source.FULL_GATE_PATTERNS,
    selection_source.PYTHON_FORMAT_LINT_PATTERNS,
    selection_source.PYTHON_TYPECHECK_PATTERNS,
    selection_source.PYTHON_ASSERTION_TEST_PATTERNS,
    selection_source.MARKDOWN_PATTERNS,
    selection_source.WORKFLOW_PATTERNS,
    selection_source.SKILL_PATTERNS,
    selection_source.INSTRUCTION_BLOCK_PATTERNS,
    selection_source.EVAL_TRIGGER_PATTERNS,
    selection_source.EVAL_PROMPT_PATTERNS,
    selection_source.EVIDENCE_LINK_PATTERNS,
    selection_source.TEST_INFRASTRUCTURE_PATTERNS,
)


def _pytest_arguments(plan: SelectedGatePlan) -> tuple[tuple[str, ...], ...]:
    return tuple(
        step.argv[len(PYTEST_ARGV) :]
        for step in plan.steps
        if step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
    )


def _argvs_without_exclusion(plan: SelectedGatePlan) -> tuple[tuple[str, ...], ...]:
    return tuple(
        step.argv[: -len(REAL_AGENT_CODEX_EXCLUSION)]
        if step.argv[-len(REAL_AGENT_CODEX_EXCLUSION) :] == REAL_AGENT_CODEX_EXCLUSION
        else step.argv
        for step in plan.steps
    )


def _real_agent_codex_test_modules() -> tuple[str, ...]:
    return tuple(
        sorted(
            {node_id.split("::", maxsplit=1)[0] for node_id in REAL_AGENT_CODEX_TESTS}
        )
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
    assert run.spawn_calls == tuple(
        (*step.argv, *REAL_AGENT_CODEX_EXCLUSION)
        if step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
        else step.argv
        for recipe in CHECK_RECIPES
        for step in (*PREFLIGHT_STEPS, *recipe.steps)
    )
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


@pytest.mark.parametrize("pattern", selection_source.AGENT_DEFINITION_PATTERNS)
def test_every_agent_definition_category_selects_the_real_agent_codex_tests(
    pattern: str,
) -> None:
    path = path_from_pattern(pattern)
    with synthetic_repository() as repo:
        local = build_selected_gate_plan(
            (path,), test_infrastructure=index_test_infrastructure(repo.root)
        )
    full = build_full_gate_plan((path,))

    for plan in (local, full):
        assert plan.real_agent_codex, path
        assert plan.real_agent_codex_reason == REAL_AGENT_CODEX_INCLUDED_REASON
        pytest_arguments = _pytest_arguments(plan)
        assert pytest_arguments, path
        assert all(
            arguments[-len(REAL_AGENT_CODEX_EXCLUSION) :] != REAL_AGENT_CODEX_EXCLUSION
            for arguments in pytest_arguments
        )
        if not plan.full_gate:
            assert set(REAL_AGENT_CODEX_TESTS) <= {
                argument for arguments in pytest_arguments for argument in arguments
            }


def test_every_checkout_agent_definition_selects_the_real_agent_codex_tests() -> None:
    paths = checkout_agent_definition_paths()

    assert repository_relative_path(agent_conversion.__file__) in paths
    for path in paths:
        local = build_selected_gate_plan((path,))
        full = build_full_gate_plan((path,))
        assert local.real_agent_codex, path
        assert full.real_agent_codex, path
        local_arguments = _pytest_arguments(local)
        if local.full_gate:
            assert all(
                arguments[-len(REAL_AGENT_CODEX_EXCLUSION) :]
                != REAL_AGENT_CODEX_EXCLUSION
                for arguments in local_arguments
            )
        else:
            assert set(REAL_AGENT_CODEX_TESTS) <= {
                argument for arguments in local_arguments for argument in arguments
            }


def test_the_real_agent_codex_tests_resolve_to_collected_tests() -> None:
    observation = pytest_collection_observation(REAL_AGENT_CODEX_TESTS)

    assert observation.exit_code == 0, observation.output
    assert observation.collected == frozenset(REAL_AGENT_CODEX_TESTS)


def test_an_agent_definition_full_gate_runs_the_unmodified_recipe_set() -> None:
    path = repository_relative_path(agent_conversion.__file__)

    for plan in (build_selected_gate_plan((path,)), build_full_gate_plan((path,))):
        assert plan.full_gate
        assert plan.real_agent_codex
        assert plan.steps == tuple(
            step for recipe in CHECK_RECIPES for step in recipe.steps
        )


@pytest.mark.parametrize("patterns", NON_AGENT_DEFINITION_CATEGORIES)
def test_no_other_changed_path_category_selects_a_real_agent_codex_test(
    patterns: tuple[str, ...],
) -> None:
    full_recipe_argvs = tuple(
        step.argv for recipe in CHECK_RECIPES for step in recipe.steps
    )
    for pattern in patterns:
        path = path_from_pattern(pattern)
        with synthetic_repository() as repo:
            local = build_selected_gate_plan(
                (path,), test_infrastructure=index_test_infrastructure(repo.root)
            )
        full = build_full_gate_plan((path,))

        for plan in (local, full):
            assert not plan.real_agent_codex, path
            assert plan.real_agent_codex_reason == REAL_AGENT_CODEX_EXCLUDED_REASON
            pytest_arguments = _pytest_arguments(plan)
            assert not set(REAL_AGENT_CODEX_TESTS) & {
                argument for arguments in pytest_arguments for argument in arguments
            }
            if plan.full_gate:
                assert all(
                    arguments[-len(REAL_AGENT_CODEX_EXCLUSION) :]
                    == REAL_AGENT_CODEX_EXCLUSION
                    for arguments in pytest_arguments
                )
                assert _argvs_without_exclusion(plan) == full_recipe_argvs


def test_a_changeset_on_real_agent_evidence_without_agent_definitions_selects_none() -> (
    None
):
    # The changeset that provisions the real-agent tests' Codex homes changes
    # their harnesses, their module, this node's selection code and spec, and
    # the gate configuration, and no agent definition.
    reach = repository_reach(installation_harness.__file__)
    changeset = (
        *_real_agent_codex_test_modules(),
        reach.path,
        repository_relative_path(discovery_auth_harness.__file__),
        repository_relative_path(selection_source.__file__),
        INSTRUCTION_BLOCK_SOURCE_PATH,
        PYPROJECT_PATH,
        CHECK_WORKFLOW_PATH,
        SELECTED_GATE_MARKDOWN_PATH,
    )

    local = build_selected_gate_plan(changeset, test_infrastructure=reach.index)
    full = build_full_gate_plan(changeset)

    for plan in (local, full):
        assert plan.full_gate
        assert not plan.real_agent_codex
        assert _argvs_without_exclusion(plan) == tuple(
            step.argv for recipe in CHECK_RECIPES for step in recipe.steps
        )
        assert all(
            arguments[-len(REAL_AGENT_CODEX_EXCLUSION) :] == REAL_AGENT_CODEX_EXCLUSION
            for arguments in _pytest_arguments(plan)
        )


def test_a_changed_real_agent_test_module_runs_every_other_test_in_it() -> None:
    modules = _real_agent_codex_test_modules()
    plan = build_selected_gate_plan(modules)

    assert not plan.full_gate
    assert not plan.real_agent_codex
    (arguments,) = _pytest_arguments(plan)
    selected = pytest_collection_observation(arguments)
    direct = pytest_collection_observation(modules)
    assert selected.exit_code == 0, selected.output
    assert direct.exit_code == 0, direct.output
    assert set(REAL_AGENT_CODEX_TESTS) <= direct.collected
    assert selected.collected == direct.collected - set(REAL_AGENT_CODEX_TESTS)


def test_unrelated_automatic_full_gate_excludes_only_the_real_agent_codex_tests() -> (
    None
):
    with synthetic_repository() as repo:
        layout = reach_layout(InfrastructureReach.SHARED, repo)
        plan = build_selected_gate_plan(
            (layout.changed_path,),
            test_infrastructure=index_test_infrastructure(repo.root),
        )

    assert plan.full_gate
    assert not plan.real_agent_codex
    assert _argvs_without_exclusion(plan) == tuple(
        step.argv for recipe in CHECK_RECIPES for step in recipe.steps
    )
    assert all(
        arguments[-len(REAL_AGENT_CODEX_EXCLUSION) :] == REAL_AGENT_CODEX_EXCLUSION
        for arguments in _pytest_arguments(plan)
    )


@pytest.mark.parametrize(
    "run_observation", (run_check_observation, run_full_check_observation)
)
def test_unrelated_full_gate_execution_honors_its_exclusion(
    run_observation: Callable[..., RunObservation],
) -> None:
    run = run_observation(branch_path=unrelated_validation_source_path())

    pytest_calls = tuple(
        call for call in run.spawn_calls if call[: len(PYTEST_ARGV)] == PYTEST_ARGV
    )
    assert run.exit_code == 0
    assert pytest_calls
    assert all(
        call[-len(REAL_AGENT_CODEX_EXCLUSION) :] == REAL_AGENT_CODEX_EXCLUSION
        for call in pytest_calls
    )
    assert run.output.index(REAL_AGENT_CODEX_EXCLUDED_REASON) < run.output.index(
        f"Recipe {RECIPE_VALIDATION}"
    )


@pytest.mark.parametrize("credentials_present", (False, True))
def test_the_selection_reason_prints_before_execution_whatever_the_credentials(
    credentials_present: bool,
) -> None:
    agent_definition = repository_relative_path(agent_conversion.__file__)

    with codex_credential_environment(present=credentials_present):
        runs = (
            (
                run_check_observation(branch_path=agent_definition),
                REAL_AGENT_CODEX_INCLUDED_REASON,
            ),
            (
                run_check_observation(branch_path=SELECTED_GATE_PYTHON_SOURCE_PATH),
                REAL_AGENT_CODEX_EXCLUDED_REASON,
            ),
            (
                run_full_check_observation(branch_path=agent_definition),
                REAL_AGENT_CODEX_INCLUDED_REASON,
            ),
            (
                run_full_check_observation(
                    branch_path=SELECTED_GATE_PYTHON_SOURCE_PATH
                ),
                REAL_AGENT_CODEX_EXCLUDED_REASON,
            ),
        )

    for run, reason in runs:
        assert run.exit_code == 0
        assert run.output.index(reason) < run.output.index("Recipe ")
