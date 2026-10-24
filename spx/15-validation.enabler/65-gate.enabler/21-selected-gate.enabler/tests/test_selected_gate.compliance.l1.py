"""Compliance evidence for selected gate execution."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import PurePosixPath

import pytest

from outcomeeng.validation import (
    CHECK_RECIPES,
    ON_DEMAND_EXCLUSION_ARGV,
    ON_DEMAND_LEVEL,
    PREFLIGHT_STEPS,
    PYTEST_ARGV,
    RECIPE_CHECK,
    RECIPE_HEADER_PREFIX,
    RECIPE_TEST,
    RECIPE_VALIDATION,
    SUMMARY_PATH_LABEL,
    recipe_header,
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
    CHANGESET_BASE_LABEL,
    FIRST_PARENT_BASE_REF,
    ON_DEMAND_EXCLUDED_REASON,
    PATH_CATEGORY_PATTERNS,
    PathCategory,
    SelectedGatePlan,
    TEST_REASON,
    build_full_gate_plan,
    build_selected_gate_plan,
    render_plan,
)
from outcomeeng_testing.generators.gate import (
    SELECTED_GATE_FULL_GATE_PATH,
    SELECTED_GATE_PYTHON_SOURCE_PATH,
    SELECTED_GATE_PYTHON_TEST_PATH,
    on_demand_fixture_files,
    path_from_pattern,
)
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
    on_demand_reach_layout,
    reach_layout,
    repository_reach,
    synthetic_repository,
)
from outcomeeng_testing.harnesses.on_demand_collection import (
    fixture_collection,
    pytest_argument_tail,
)
from outcomeeng_testing.harnesses.real_agent_selection import (
    direct_test_observation,
    first_parent_full_check_observation,
    run_full_check_observation,
)

# The generator composes each fixture file at one execution level, so the level
# of every path below is the generator's, not the selector's.
FIXTURE = on_demand_fixture_files()
ON_DEMAND_PATHS = frozenset(
    test_file.path for test_file in FIXTURE if test_file.level == ON_DEMAND_LEVEL
)
DEFAULT_SUITE_FILES = frozenset(
    test_file.path for test_file in FIXTURE if test_file.level != ON_DEMAND_LEVEL
)


def _pytest_arguments(plan: SelectedGatePlan) -> tuple[tuple[str, ...], ...]:
    return tuple(
        step.argv[len(PYTEST_ARGV) :]
        for step in plan.steps
        if step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
    )


def _pytest_calls(
    spawn_calls: tuple[tuple[str, ...], ...],
) -> tuple[tuple[str, ...], ...]:
    return tuple(
        call for call in spawn_calls if call[: len(PYTEST_ARGV)] == PYTEST_ARGV
    )


def _plan_targets(plan: SelectedGatePlan) -> frozenset[str]:
    return frozenset(
        argument for arguments in _pytest_arguments(plan) for argument in arguments
    )


def _pytest_steps_argv(plan: SelectedGatePlan) -> tuple[tuple[str, ...], ...]:
    return tuple(
        step.argv for step in plan.steps if step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
    )


def _full_surface_steps() -> tuple[tuple[str, ...], ...]:
    return tuple(step.argv for recipe in CHECK_RECIPES for step in recipe.steps)


def _collected_by(pytest_argv: Sequence[str]) -> frozenset[str]:
    # Real pytest collection over the fixture, for the arguments a spawned
    # pytest argv carries.
    return fixture_collection(
        FIXTURE, pytest_argument_tail(pytest_argv)
    ).collected_files


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
        step.argv
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


def test_a_changeset_of_on_demand_files_selects_no_pytest_target() -> None:
    files = tuple(sorted(ON_DEMAND_PATHS))

    local = build_selected_gate_plan(files)
    full = build_full_gate_plan(files)

    assert files
    assert _pytest_arguments(local) == ()
    for plan in (local, full):
        assert not ON_DEMAND_PATHS & _plan_targets(plan)


@pytest.mark.parametrize("category", tuple(PathCategory), ids=str)
def test_no_changed_path_category_selects_an_on_demand_test(
    category: PathCategory,
) -> None:
    for pattern in PATH_CATEGORY_PATTERNS[category]:
        path = path_from_pattern(pattern)
        changed = (path, *sorted(ON_DEMAND_PATHS))
        with synthetic_repository() as repo:
            local = build_selected_gate_plan(
                changed, test_infrastructure=index_test_infrastructure(repo.root)
            )
        full = build_full_gate_plan(changed)

        for plan in (local, full):
            assert not ON_DEMAND_PATHS & _plan_targets(plan), path
            assert all(
                step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
                for step in plan.steps
                if "pytest" in step.argv
            ), path
            if plan.full_gate:
                assert tuple(step.argv for step in plan.steps) == _full_surface_steps()


def test_a_node_local_reach_of_an_on_demand_test_selects_no_on_demand_target() -> None:
    with synthetic_repository() as repo:
        layout = on_demand_reach_layout(repo)
    reached = layout.index.reach(layout.changed_path)
    _, on_demand_path = layout.tests

    plan = build_selected_gate_plan(
        (layout.changed_path,), test_infrastructure=layout.index
    )

    assert reached.kind is InfrastructureReach.NODE_LOCAL
    assert on_demand_path in reached.tests
    assert plan.full_gate is False
    assert on_demand_path not in _plan_targets(plan)
    assert all(
        step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
        for step in plan.steps
        if "pytest" in step.argv
    )


def test_a_shared_test_infrastructure_module_selects_the_full_surface_without_the_on_demand_suite() -> (
    None
):
    reach = repository_reach(installation_harness.__file__)

    plan = build_selected_gate_plan((reach.path,), test_infrastructure=reach.index)

    assert plan.full_gate is True
    assert [_collected_by(call) for call in _pytest_steps_argv(plan)] == [
        DEFAULT_SUITE_FILES
    ]
    assert all(
        step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
        for step in plan.steps
        if "pytest" in step.argv
    )


def test_widening_to_the_full_suite_removes_no_other_step() -> None:
    with synthetic_repository() as repo:
        layout = reach_layout(InfrastructureReach.SHARED, repo)
        plan = build_selected_gate_plan(
            (layout.changed_path,),
            test_infrastructure=index_test_infrastructure(repo.root),
        )

    assert plan.full_gate
    assert tuple(step.argv for step in plan.steps) == _full_surface_steps()
    assert all(
        step.argv[len(PYTEST_ARGV) - len(ON_DEMAND_EXCLUSION_ARGV) : len(PYTEST_ARGV)]
        == ON_DEMAND_EXCLUSION_ARGV
        for step in plan.steps
        if step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
    )


def test_the_exclusion_leaves_on_demand_files_out_of_a_collected_directory() -> None:
    directory = PurePosixPath(sorted(ON_DEMAND_PATHS)[0]).parent.as_posix()
    in_directory = frozenset(
        test_file.path
        for test_file in FIXTURE
        if PurePosixPath(test_file.path).parent.as_posix() == directory
    )

    excluded = fixture_collection(FIXTURE, (*ON_DEMAND_EXCLUSION_ARGV, directory))
    unfiltered = fixture_collection(FIXTURE, (directory,))

    assert excluded.exit_code == 0, excluded.output
    assert unfiltered.exit_code == 0, unfiltered.output
    assert unfiltered.collected_files == in_directory
    assert excluded.collected_files
    assert excluded.collected_files == in_directory - ON_DEMAND_PATHS


@pytest.mark.parametrize(
    "branch_path",
    (
        SELECTED_GATE_PYTHON_SOURCE_PATH,
        SELECTED_GATE_FULL_GATE_PATH,
        unrelated_validation_source_path(),
    ),
    ids=str,
)
@pytest.mark.parametrize(
    "run_observation", (run_check_observation, run_full_check_observation)
)
def test_every_gate_execution_names_the_exclusion_before_any_step_runs(
    run_observation: Callable[..., RunObservation],
    branch_path: str,
) -> None:
    run = run_observation(branch_path=branch_path)

    assert run.exit_code == 0
    assert run.output.index(ON_DEMAND_EXCLUDED_REASON) < run.output.index(
        RECIPE_HEADER_PREFIX
    )


@pytest.mark.parametrize(
    "run_observation", (run_check_observation, run_full_check_observation)
)
def test_a_full_gate_execution_spawns_only_exclusion_carrying_pytest_runs(
    run_observation: Callable[..., RunObservation],
) -> None:
    run = run_observation(branch_path=unrelated_validation_source_path())

    pytest_calls = _pytest_calls(run.spawn_calls)
    assert run.exit_code == 0
    assert pytest_calls
    assert all(_collected_by(call) == DEFAULT_SUITE_FILES for call in pytest_calls)
    assert tuple(call for call in run.spawn_calls if call not in pytest_calls) == tuple(
        step.argv
        for recipe in CHECK_RECIPES
        for step in (*PREFLIGHT_STEPS, *recipe.steps)
        if step.argv[: len(PYTEST_ARGV)] != PYTEST_ARGV
    )


def test_direct_execution_runs_a_named_on_demand_test_whatever_the_changeset() -> None:
    # Both gate wrappers exclude the on-demand suite whatever the changeset is;
    # direct execution naming an on-demand file still runs it.
    named = tuple(sorted(ON_DEMAND_PATHS))
    gate_runs = (
        run_check_observation(branch_path=unrelated_validation_source_path()),
        run_full_check_observation(branch_path=unrelated_validation_source_path()),
    )
    direct = direct_test_observation(named)

    for run in gate_runs:
        assert _pytest_calls(run.spawn_calls)
        assert all(
            _collected_by(call) == DEFAULT_SUITE_FILES
            for call in _pytest_calls(run.spawn_calls)
        )

    assert direct.exit_code == 0
    (direct_pytest_call,) = _pytest_calls(direct.spawn_calls)
    assert direct_pytest_call[len(PYTEST_ARGV) :] == named
    assert _collected_by(direct_pytest_call) == ON_DEMAND_PATHS


def test_ci_full_verification_without_a_default_branch_selects_by_the_first_parent() -> (
    None
):
    # CI's merge-commit checkout carries no remote default branch, so the full
    # gate discovers the changeset against the first parent and still excludes
    # the on-demand suite.
    run = first_parent_full_check_observation(
        branch_path=unrelated_validation_source_path()
    )

    assert run.exit_code == 0
    assert run.runner_calls[0] == selected_gate_branch_discovery_argv(
        base_ref=FIRST_PARENT_BASE_REF
    )
    pytest_calls = _pytest_calls(run.spawn_calls)
    assert pytest_calls
    assert all(_collected_by(call) == DEFAULT_SUITE_FILES for call in pytest_calls)
    plan_end = run.output.index(RECIPE_HEADER_PREFIX)
    assert run.output.index(ON_DEMAND_EXCLUDED_REASON) < plan_end
    assert (
        run.output.index(f"{CHANGESET_BASE_LABEL}: {FIRST_PARENT_BASE_REF}") < plan_end
    )
