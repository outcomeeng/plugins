"""Compliance evidence for selected gate execution."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import PurePosixPath

import pytest

from outcomeeng.validation import (
    CHECK_RECIPES,
    L3_SKIP_ARGV,
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
    L3_SKIPPED_REASON,
    PATH_CATEGORY_PATTERNS,
    PathCategory,
    TEST_REASON,
    build_full_gate_plan,
    build_selected_gate_plan,
)
from outcomeeng_testing.generators.gate import (
    SELECTED_GATE_FULL_GATE_PATH,
    SELECTED_GATE_PYTHON_SOURCE_PATH,
    SELECTED_GATE_PYTHON_TEST_PATH,
    l3_fixture_files,
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
    l3_reach_layout,
    reach_layout,
    repository_reach,
    synthetic_repository,
)
from outcomeeng_testing.harnesses.l3_collection import (
    default_suite_fixture_paths,
    fixture_collected_files,
    fixture_collection,
    l3_fixture_paths,
    plan_collected_files,
    plan_pytest_arguments,
    plan_pytest_targets,
    pytest_argvs,
)
from outcomeeng_testing.harnesses.real_agent_selection import (
    direct_test_observation,
    first_parent_full_check_observation,
    run_full_check_observation,
)


def _full_surface_steps() -> tuple[tuple[str, ...], ...]:
    return tuple(step.argv for recipe in CHECK_RECIPES for step in recipe.steps)


def test_an_empty_changeset_selects_no_steps() -> None:
    plan = build_selected_gate_plan(())

    assert plan.steps == ()
    assert plan.full_gate is False


# Assertion design record: selected steps print before the recipes run
# - Assertion: ALWAYS: the selected gate prints the selected steps and reasons
#   before running them through the signal-safe recipe orchestrator,
#   preserving bounded output and structured summaries (universal rule).
# - Production subject: the plan the selected check writes to its live sink
#   before the first recipe header, observed through the run's output.
# - Case provenance: the Python source path from the gate generator; its
#   planned steps are the complete selected set, and its lint and type steps
#   share one reason, so a line shared by several steps is a reachable defect.
# - Oracle owner: the assertion's sentence, read as one plan line per selected
#   step carrying that step's label as a whole word and its reason; the
#   expected pairs come from the planner's selected set, never from
#   render_plan, and label words are runs of the selected labels' characters.
# - Rejected mutations: the plan line drops its label, the plan omits a
#   selected step, or the plan prints one line for every step sharing a reason.
# - Failure observation: a selected step that no plan line or several plan
#   lines name, or fewer distinct naming lines than selected steps.
def test_the_plan_prints_before_the_recipes_run() -> None:
    run = run_check_observation(branch_path=SELECTED_GATE_PYTHON_SOURCE_PATH)

    selected = build_selected_gate_plan((SELECTED_GATE_PYTHON_SOURCE_PATH,))
    plan_lines = run.output[: run.output.index(recipe_header(RECIPE_CHECK))]
    label_characters = "".join(
        sorted({char for item in selected.selected_steps for char in item.step.label})
    )
    label_word = re.compile(f"[{re.escape(label_characters)}]+")
    naming_lines = [
        [
            index
            for index, line in enumerate(plan_lines.splitlines())
            if item.step.label in label_word.findall(line) and item.reason in line
        ]
        for item in selected.selected_steps
    ]
    assert run.exit_code == 0
    assert selected.selected_steps
    assert all(len(lines) == 1 for lines in naming_lines), naming_lines
    assert len({lines[0] for lines in naming_lines}) == len(selected.selected_steps)
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


def test_a_changeset_of_l3_files_selects_no_pytest_target() -> None:
    files = tuple(sorted(l3_fixture_paths()))

    local = build_selected_gate_plan(files)
    full = build_full_gate_plan(files)

    assert files
    assert plan_pytest_arguments(local) == ()
    for plan in (local, full):
        assert not l3_fixture_paths() & plan_pytest_targets(plan)


@pytest.mark.parametrize("category", tuple(PathCategory), ids=str)
def test_no_changed_path_category_selects_an_l3_test(
    category: PathCategory,
) -> None:
    for pattern in PATH_CATEGORY_PATTERNS[category]:
        path = path_from_pattern(pattern)
        changed = (path, *sorted(l3_fixture_paths()))
        with synthetic_repository() as repo:
            local = build_selected_gate_plan(
                changed, test_infrastructure=index_test_infrastructure(repo.root)
            )
        full = build_full_gate_plan(changed)

        for plan in (local, full):
            assert not l3_fixture_paths() & plan_pytest_targets(plan), path
            assert all(
                step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
                for step in plan.steps
                if "pytest" in step.argv
            ), path
            if plan.full_gate:
                assert tuple(step.argv for step in plan.steps) == _full_surface_steps()


def test_a_node_local_reach_of_an_l3_test_selects_no_l3_target() -> None:
    with synthetic_repository() as repo:
        layout = l3_reach_layout(repo)
    reached = layout.index.reach(layout.changed_path)
    _, l3_path = layout.tests

    plan = build_selected_gate_plan(
        (layout.changed_path,), test_infrastructure=layout.index
    )

    assert reached.kind is InfrastructureReach.NODE_LOCAL
    assert l3_path in reached.tests
    assert plan.full_gate is False
    assert l3_path not in plan_pytest_targets(plan)
    assert all(
        step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
        for step in plan.steps
        if "pytest" in step.argv
    )


def test_a_shared_test_infrastructure_module_selects_the_full_surface_without_the_l3_tests() -> (
    None
):
    reach = repository_reach(installation_harness.__file__)

    plan = build_selected_gate_plan((reach.path,), test_infrastructure=reach.index)

    assert plan.full_gate is True
    assert plan_collected_files(plan) == (default_suite_fixture_paths(),)
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


def test_the_exclusion_leaves_l3_files_out_of_a_collected_directory() -> None:
    directory = PurePosixPath(sorted(l3_fixture_paths())[0]).parent.as_posix()
    in_directory = frozenset(
        test_file.path
        for test_file in l3_fixture_files()
        if PurePosixPath(test_file.path).parent.as_posix() == directory
    )

    excluded = fixture_collection(l3_fixture_files(), (*L3_SKIP_ARGV, directory))
    unfiltered = fixture_collection(l3_fixture_files(), (directory,))

    assert excluded.exit_code == 0, excluded.output
    assert unfiltered.exit_code == 0, unfiltered.output
    assert unfiltered.collected_files == in_directory
    assert excluded.collected_files
    assert excluded.collected_files == in_directory - l3_fixture_paths()


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
    assert run.output.index(L3_SKIPPED_REASON) < run.output.index(RECIPE_HEADER_PREFIX)


@pytest.mark.parametrize(
    "run_observation", (run_check_observation, run_full_check_observation)
)
def test_a_full_gate_execution_spawns_only_exclusion_carrying_pytest_runs(
    run_observation: Callable[..., RunObservation],
) -> None:
    run = run_observation(branch_path=unrelated_validation_source_path())

    pytest_calls = pytest_argvs(run.spawn_calls)
    assert run.exit_code == 0
    assert pytest_calls
    assert all(
        fixture_collected_files(call) == default_suite_fixture_paths()
        for call in pytest_calls
    )
    assert tuple(call for call in run.spawn_calls if call not in pytest_calls) == tuple(
        step.argv
        for recipe in CHECK_RECIPES
        for step in (*PREFLIGHT_STEPS, *recipe.steps)
        if step.argv[: len(PYTEST_ARGV)] != PYTEST_ARGV
    )


def test_direct_execution_runs_a_named_l3_test_whatever_the_changeset() -> None:
    # Both gate wrappers exclude the L3 tests whatever the changeset is;
    # direct execution naming an L3 file still runs it.
    named = tuple(l3_fixture_paths())
    gate_runs = (
        run_check_observation(branch_path=unrelated_validation_source_path()),
        run_full_check_observation(branch_path=unrelated_validation_source_path()),
    )
    direct = direct_test_observation(named)

    for run in gate_runs:
        assert pytest_argvs(run.spawn_calls)
        assert all(
            fixture_collected_files(call) == default_suite_fixture_paths()
            for call in pytest_argvs(run.spawn_calls)
        )

    assert direct.exit_code == 0
    (direct_pytest_call,) = pytest_argvs(direct.spawn_calls)
    assert set(direct_pytest_call[len(PYTEST_ARGV) :]) == set(named)
    assert fixture_collected_files(direct_pytest_call) == l3_fixture_paths()


def test_ci_full_verification_without_a_default_branch_selects_by_the_first_parent() -> (
    None
):
    # CI's merge-commit checkout carries no remote default branch, so the full
    # gate discovers the changeset against the first parent and still excludes
    # the L3 tests.
    run = first_parent_full_check_observation(
        branch_path=unrelated_validation_source_path()
    )

    assert run.exit_code == 0
    assert run.runner_calls[0] == selected_gate_branch_discovery_argv(
        base_ref=FIRST_PARENT_BASE_REF
    )
    pytest_calls = pytest_argvs(run.spawn_calls)
    assert pytest_calls
    assert all(
        fixture_collected_files(call) == default_suite_fixture_paths()
        for call in pytest_calls
    )
    plan_end = run.output.index(RECIPE_HEADER_PREFIX)
    assert run.output.index(L3_SKIPPED_REASON) < plan_end
    assert (
        run.output.index(f"{CHANGESET_BASE_LABEL}: {FIRST_PARENT_BASE_REF}") < plan_end
    )
