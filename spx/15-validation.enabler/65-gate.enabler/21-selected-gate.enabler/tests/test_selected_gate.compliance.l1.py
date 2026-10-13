"""Compliance evidence for selected gate execution."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from outcomeeng.validation import (
    CHECK_RECIPES,
    PREFLIGHT_STEPS,
    PYTEST_ARGV,
    RECIPE_CHECK,
    RECIPE_HEADER_PREFIX,
    RECIPE_TEST,
    RECIPE_VALIDATION,
    SUMMARY_PATH_LABEL,
    recipe_header,
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
    CHANGESET_BASE_LABEL,
    FIRST_PARENT_BASE_REF,
    INSTRUCTION_BLOCK_SOURCE_PATH,
    PATH_CATEGORY_PATTERNS,
    PYPROJECT_PATH,
    REAL_AGENT_CODEX_EXCLUDED_REASON,
    REAL_AGENT_CODEX_EXCLUSION,
    REAL_AGENT_CODEX_INCLUDED_REASON,
    REAL_AGENT_CODEX_TEST_MODULE,
    REAL_AGENT_CODEX_TESTS,
    PathCategory,
    SelectedGatePlan,
    TEST_REASON,
    build_full_gate_plan,
    build_selected_gate_plan,
    render_plan,
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
    selected_gate_branch_discovery_argv,
    unrelated_validation_source_path,
)
from outcomeeng_testing.harnesses.infrastructure_index import (
    reach_layout,
    repository_reach,
    synthetic_repository,
)
from outcomeeng_testing.harnesses.real_agent_selection import (
    checkout_agent_definition_inventory,
    codex_credential_environment,
    direct_test_observation,
    first_parent_full_check_observation,
    pytest_collection_observation,
    repository_relative_path,
    run_full_check_observation,
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


def _pytest_calls(
    spawn_calls: tuple[tuple[str, ...], ...],
) -> tuple[tuple[str, ...], ...]:
    return tuple(
        call for call in spawn_calls if call[: len(PYTEST_ARGV)] == PYTEST_ARGV
    )


def test_an_empty_changeset_selects_no_steps() -> None:
    plan = build_selected_gate_plan(())

    assert plan.steps == ()
    assert plan.full_gate is False


def test_the_plan_prints_before_the_recipes_run() -> None:
    run = run_check_observation(branch_path=SELECTED_GATE_PYTHON_SOURCE_PATH)

    plan_text = render_plan(
        build_selected_gate_plan((SELECTED_GATE_PYTHON_SOURCE_PATH,))
    )
    assert run.exit_code == 0
    assert run.output.startswith(plan_text)
    assert len(plan_text) <= run.output.index(recipe_header(RECIPE_CHECK))
    assert SUMMARY_PATH_LABEL in run.output


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
    assert recipe_header(RECIPE_VALIDATION) in run.output
    assert recipe_header(RECIPE_TEST) in run.output


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
    observation = missing_origin_observation()

    assert observation.run.exit_code == GIT_DISCOVERY_FAILURE_EXIT_CODE
    assert observation.run.spawn_calls == ()
    assert GIT_DISCOVERY_ERROR_PREFIX in observation.run.output
    assert observation.helper_failure in observation.run.output


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


@pytest.mark.parametrize(
    "kind", tuple(checkout_agent_definition_inventory().by_kind()), ids=str
)
def test_every_kind_of_checkout_agent_definition_selects_the_real_agent_codex_tests(
    kind: str,
) -> None:
    paths = checkout_agent_definition_inventory().by_kind()[kind]

    assert paths
    for path in paths:
        local = build_selected_gate_plan((path,))
        full = build_full_gate_plan((path,))
        for plan in (local, full):
            assert plan.real_agent_codex, path
            assert plan.real_agent_codex_reason == REAL_AGENT_CODEX_INCLUDED_REASON
            pytest_arguments = _pytest_arguments(plan)
            assert pytest_arguments, path
            assert all(
                arguments[-len(REAL_AGENT_CODEX_EXCLUSION) :]
                != REAL_AGENT_CODEX_EXCLUSION
                for arguments in pytest_arguments
            )
            if not plan.full_gate:
                assert set(REAL_AGENT_CODEX_TESTS) <= {
                    argument for arguments in pytest_arguments for argument in arguments
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


@pytest.mark.parametrize(
    "category",
    tuple(
        category
        for category in PathCategory
        if category is not PathCategory.AGENT_DEFINITION
    ),
    ids=str,
)
def test_no_other_changed_path_category_selects_a_real_agent_codex_test(
    category: PathCategory,
) -> None:
    full_recipe_argvs = tuple(
        step.argv for recipe in CHECK_RECIPES for step in recipe.steps
    )
    for pattern in PATH_CATEGORY_PATTERNS[category]:
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
    # A changeset confined to the real-agent tests' own evidence changes their
    # harnesses, their module, this node's selection code and spec, and the
    # gate configuration, and no agent definition.
    reach = repository_reach(installation_harness.__file__)
    changeset = (
        REAL_AGENT_CODEX_TEST_MODULE,
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
    modules = (REAL_AGENT_CODEX_TEST_MODULE,)
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
        recipe_header(RECIPE_VALIDATION)
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
        assert run.output.index(reason) < run.output.index(RECIPE_HEADER_PREFIX)


def test_direct_execution_runs_a_named_real_agent_codex_test_whatever_the_changeset() -> (
    None
):
    # The changeset changes no agent definition, so both gate wrappers exclude
    # the real-agent Codex tests; direct execution naming them still runs them.
    unrelated = unrelated_validation_source_path()
    gate_runs = (
        run_check_observation(branch_path=unrelated),
        run_full_check_observation(branch_path=unrelated),
    )
    direct = direct_test_observation(REAL_AGENT_CODEX_TESTS)

    for run in gate_runs:
        gate_pytest_calls = tuple(
            call for call in run.spawn_calls if call[: len(PYTEST_ARGV)] == PYTEST_ARGV
        )
        assert gate_pytest_calls
        assert all(
            call[-len(REAL_AGENT_CODEX_EXCLUSION) :] == REAL_AGENT_CODEX_EXCLUSION
            for call in gate_pytest_calls
        )

    assert direct.exit_code == 0
    (direct_pytest_call,) = (
        call for call in direct.spawn_calls if call[: len(PYTEST_ARGV)] == PYTEST_ARGV
    )
    direct_arguments = direct_pytest_call[len(PYTEST_ARGV) :]
    assert direct_arguments == tuple(REAL_AGENT_CODEX_TESTS)
    collection = pytest_collection_observation(direct_arguments)
    assert collection.exit_code == 0, collection.output
    assert collection.collected == frozenset(REAL_AGENT_CODEX_TESTS)


def test_ci_full_verification_without_a_default_branch_selects_by_the_first_parent() -> (
    None
):
    # CI's merge-commit checkout carries no remote default branch, so the full
    # gate discovers the changeset against the first parent.
    agent_definition = repository_relative_path(agent_conversion.__file__)

    run = first_parent_full_check_observation(branch_path=agent_definition)

    assert run.exit_code == 0
    assert run.runner_calls[0] == selected_gate_branch_discovery_argv(
        base_ref=FIRST_PARENT_BASE_REF
    )
    pytest_calls = _pytest_calls(run.spawn_calls)
    assert pytest_calls
    assert all(
        call[-len(REAL_AGENT_CODEX_EXCLUSION) :] != REAL_AGENT_CODEX_EXCLUSION
        for call in pytest_calls
    )
    plan_end = run.output.index(RECIPE_HEADER_PREFIX)
    assert run.output.index(REAL_AGENT_CODEX_INCLUDED_REASON) < plan_end
    assert (
        run.output.index(f"{CHANGESET_BASE_LABEL}: {FIRST_PARENT_BASE_REF}") < plan_end
    )


def test_ci_full_verification_without_a_default_branch_excludes_unrelated_changes() -> (
    None
):
    run = first_parent_full_check_observation(
        branch_path=unrelated_validation_source_path()
    )

    assert run.exit_code == 0
    assert run.runner_calls[0] == selected_gate_branch_discovery_argv(
        base_ref=FIRST_PARENT_BASE_REF
    )
    pytest_calls = _pytest_calls(run.spawn_calls)
    assert pytest_calls
    assert all(
        call[-len(REAL_AGENT_CODEX_EXCLUSION) :] == REAL_AGENT_CODEX_EXCLUSION
        for call in pytest_calls
    )
    assert run.output.index(REAL_AGENT_CODEX_EXCLUDED_REASON) < run.output.index(
        RECIPE_HEADER_PREFIX
    )
