"""Mapping evidence for selected local gate planning."""

from __future__ import annotations

import pytest

from outcomeeng.validation import (
    CHECK_RECIPES,
    EVAL_LINKS_ARGV,
    EXECUTION_LEVELS,
    L3_LEVEL,
    PREFLIGHT_STEPS,
    PYTEST_ARGV,
    TEST_STEPS,
    VALIDATION_STEPS,
)
from outcomeeng.validation.infrastructure_index import (
    InfrastructureReach,
    PRODUCT_TREE_ROOT,
)
from outcomeeng.validation.selected_gate import (
    PATH_CATEGORY_PATTERNS,
    ChangedPath,
    FULL_GATE_REASON,
    InfrastructureIndexRequired,
    PathCategory,
    REACHED_TESTS_REASON,
    SHARED_TEST_INFRASTRUCTURE_REASON,
    SelectedGatePlan,
    TEST_REASON,
    UNTRACEABLE_TEST_INFRASTRUCTURE_REASON,
    PYTHON_REASON,
    build_full_gate_plan,
    build_selected_gate_plan,
    deleted_paths_after_status_resolution,
)
from outcomeeng_testing.generators.gate import (
    SELECTED_GATE_PYTHON_SOURCE_PATH,
    SELECTED_GATE_PYTHON_TEST_PATH,
    category_patterns,
    declared_lane_steps,
    l3_fixture_files,
    path_from_pattern,
)
from outcomeeng_testing.harnesses import gate as gate_harness
from outcomeeng_testing.harnesses.gate import (
    PYTEST_TARGET_ARG,
    SELECTED_GATE_RENAMED_TARGET_ARG,
    SELECTED_GATE_WHITESPACE_PATH,
    category_pattern_path_matches,
    collected_paths_observation,
    resolved_base_observation,
    run_check_observation,
    selected_gate_branch_discovery_argv,
    selected_gate_changed_path_domain,
)
from outcomeeng_testing.harnesses.infrastructure_index import (
    conftest_reach_layout,
    mixed_reach_layout,
    l3_reach_layout,
    reach_layout,
    repository_reach,
    synthetic_repository,
)
from outcomeeng_testing.harnesses.l3_collection import (
    default_suite_fixture_paths,
    plan_collected_files,
    plan_pytest_arguments,
    plan_pytest_targets,
)
from outcomeeng_testing.harnesses.real_agent_selection import (
    run_full_check_observation,
)


def _argvs(plan: SelectedGatePlan) -> tuple[tuple[str, ...], ...]:
    return tuple(item.step.argv for item in plan.selected_steps)


def _reasons(plan: SelectedGatePlan) -> tuple[str, ...]:
    return tuple(item.reason for item in plan.selected_steps)


def _pathspec_categories(path: str) -> frozenset[PathCategory]:
    # Git's pathspec matcher, not the selector's own classification, decides
    # which category patterns select the path.
    matched = category_pattern_path_matches()[path]
    return frozenset(
        category
        for category, patterns in PATH_CATEGORY_PATTERNS.items()
        if matched.intersection(patterns)
    )


def _lane_steps(
    categories: frozenset[PathCategory],
) -> frozenset[tuple[tuple[str, ...], str]]:
    # Each spec-declared lane of a category the path lies in contributes every
    # step it names, carrying that lane's reason.
    declared = declared_lane_steps()
    return frozenset(
        step for category in categories & declared.keys() for step in declared[category]
    )


def _validation_steps(
    plan: SelectedGatePlan,
) -> tuple[tuple[tuple[str, ...], str], ...]:
    return tuple(
        (item.step.argv, item.reason)
        for item in plan.selected_steps
        if item.step.argv[: len(PYTEST_ARGV)] != PYTEST_ARGV
    )


def _source_order(argvs: tuple[tuple[str, ...], ...]) -> tuple[tuple[str, ...], ...]:
    return tuple(step.argv for step in VALIDATION_STEPS if step.argv in argvs)


def _lane_decided(path: str) -> bool:
    # Full-gate paths select the complete recipe set and test-infrastructure
    # paths select by import reach; every other path selects by its lanes.
    return not _pathspec_categories(path) & {
        PathCategory.FULL_GATE,
        PathCategory.TEST_INFRASTRUCTURE,
    }


@pytest.mark.parametrize("pattern", category_patterns())
def test_every_category_path_selects_the_lanes_of_every_category_it_lies_in(
    pattern: str,
) -> None:
    path = path_from_pattern(pattern)
    categories = _pathspec_categories(path)

    if PathCategory.FULL_GATE in categories:
        assert build_selected_gate_plan((path,)).full_gate is True
    elif PathCategory.TEST_INFRASTRUCTURE in categories:
        with pytest.raises(InfrastructureIndexRequired):
            build_selected_gate_plan((path,))
    else:
        plan = build_selected_gate_plan((path,))
        steps = _validation_steps(plan)
        argvs = tuple(argv for argv, _ in steps)

        assert plan.full_gate is False
        assert len(set(steps)) == len(steps)
        assert frozenset(steps) == _lane_steps(categories)
        assert argvs == _source_order(argvs)


def test_paths_of_every_lane_merge_their_lanes_in_validation_step_order() -> None:
    paths = tuple(
        path
        for path in map(path_from_pattern, category_patterns())
        if _lane_decided(path)
    )

    plan = build_selected_gate_plan(paths)
    steps = _validation_steps(plan)
    argvs = tuple(argv for argv, _ in steps)

    assert plan.full_gate is False
    assert len(set(steps)) == len(steps)
    assert frozenset(steps) == frozenset().union(
        *(_lane_steps(_pathspec_categories(path)) for path in paths)
    )
    assert argvs == _source_order(argvs)


@pytest.mark.parametrize(
    "pattern", PATH_CATEGORY_PATTERNS[PathCategory.PYTHON_ASSERTION_TEST]
)
@pytest.mark.parametrize("deleted", (False, True))
def test_every_assertion_path_category_maps_presence_to_targeted_execution(
    pattern: str, deleted: bool
) -> None:
    path = path_from_pattern(pattern)
    plan = build_selected_gate_plan((path,), deleted_paths=(path,) if deleted else ())

    assert (path in plan_pytest_targets(plan)) is not deleted


@pytest.mark.parametrize("level", EXECUTION_LEVELS)
def test_changed_test_files_of_a_level_are_targeted_exactly_when_the_level_is_not_l3(
    level: str,
) -> None:
    paths = tuple(
        test_file.path
        for test_file in l3_fixture_files()
        if test_file.level == level
        and test_file.path.startswith(f"{PRODUCT_TREE_ROOT}/")
    )

    plan = build_selected_gate_plan(paths)

    assert paths
    assert plan_pytest_targets(plan) == (
        frozenset() if level == L3_LEVEL else frozenset(paths)
    )


@pytest.mark.parametrize("pattern", PATH_CATEGORY_PATTERNS[PathCategory.EVIDENCE_LINK])
def test_every_evidence_link_path_category_selects_link_validation(
    pattern: str,
) -> None:
    path = path_from_pattern(pattern)
    inside = build_selected_gate_plan((path,))
    outside = build_selected_gate_plan((path.removeprefix(f"{PRODUCT_TREE_ROOT}/"),))

    assert EVAL_LINKS_ARGV in _argvs(inside)
    assert EVAL_LINKS_ARGV not in _argvs(outside)


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


@pytest.mark.parametrize("path", PATH_CATEGORY_PATTERNS[PathCategory.FULL_GATE])
def test_full_gate_paths_select_the_complete_recipe_set(path: str) -> None:
    plan = build_selected_gate_plan((path_from_pattern(path),))

    assert plan.full_gate is True
    assert tuple(step.argv for step in plan.steps) == tuple(
        step.argv for step in (*VALIDATION_STEPS, *TEST_STEPS)
    )
    assert set(_reasons(plan)) == {FULL_GATE_REASON}


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
    assert PYTHON_REASON in run.output


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


def test_a_copy_collects_both_sides() -> None:
    observation = collected_paths_observation(
        branch_old_path=SELECTED_GATE_PYTHON_TEST_PATH,
        branch_path=SELECTED_GATE_RENAMED_TARGET_ARG,
        branch_status="C100",
    )

    assert observation.collected == tuple(
        sorted((SELECTED_GATE_PYTHON_TEST_PATH, SELECTED_GATE_RENAMED_TARGET_ARG))
    )


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
        assert [item.step.argv[: len(PYTEST_ARGV)] for item in pytest_steps] == [
            PYTEST_ARGV
        ]
        assert [set(item.step.argv[len(PYTEST_ARGV) :]) for item in pytest_steps] == [
            set(layout.tests)
        ]
        assert [item.reason for item in pytest_steps] == [REACHED_TESTS_REASON]
    elif kind is InfrastructureReach.SHARED:
        assert plan.full_gate is True
        assert tuple(step.argv for step in plan.steps) == (
            *(step.argv for step in VALIDATION_STEPS),
            *(step.argv for step in TEST_STEPS),
        )
        assert set(_reasons(plan)) == {SHARED_TEST_INFRASTRUCTURE_REASON}
    elif kind is InfrastructureReach.UNTRACEABLE:
        assert plan.full_gate is True
        assert tuple(step.argv for step in plan.steps) == (
            *(step.argv for step in VALIDATION_STEPS),
            *(step.argv for step in TEST_STEPS),
        )
        assert set(_reasons(plan)) == {UNTRACEABLE_TEST_INFRASTRUCTURE_REASON}
    else:
        assert kind is InfrastructureReach.UNREACHED
        assert plan.full_gate is False
        assert pytest_steps == []


@pytest.mark.parametrize(
    "kind", (InfrastructureReach.SHARED, InfrastructureReach.UNTRACEABLE), ids=str
)
def test_a_full_surface_reach_collects_every_default_test_and_no_l3_test(
    kind: InfrastructureReach,
) -> None:
    with synthetic_repository() as repo:
        layout = reach_layout(kind, repo)

    plan = build_selected_gate_plan(
        (layout.changed_path,), test_infrastructure=layout.index
    )

    assert plan.full_gate is True
    assert plan_collected_files(plan) == (default_suite_fixture_paths(),)


def test_the_full_gate_wrapper_collects_every_default_test_and_no_l3_test() -> None:
    plan = build_full_gate_plan(())

    assert plan.full_gate is True
    assert plan_collected_files(plan) == (default_suite_fixture_paths(),)


def test_a_node_local_reach_selects_only_the_default_tests_it_reaches() -> None:
    with synthetic_repository() as repo:
        layout = l3_reach_layout(repo)
    default_path, l3_path = layout.tests
    reached = layout.index.reach(layout.changed_path)

    plan = build_selected_gate_plan(
        (layout.changed_path,), test_infrastructure=layout.index
    )

    assert reached.kind is InfrastructureReach.NODE_LOCAL
    assert set(reached.tests) == {default_path, l3_path}
    assert plan_pytest_arguments(plan) == ((default_path,),)


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
    assert [item.step.argv[: len(PYTEST_ARGV)] for item in pytest_steps] == [
        PYTEST_ARGV
    ]
    assert [set(item.step.argv[len(PYTEST_ARGV) :]) for item in pytest_steps] == [
        {layout.changed_test, *layout.reached_tests}
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


@pytest.mark.parametrize("category", tuple(PathCategory), ids=str)
def test_the_full_gate_wrapper_runs_the_complete_recipe_set_for_every_category(
    category: PathCategory,
) -> None:
    for pattern in PATH_CATEGORY_PATTERNS[category]:
        plan = build_full_gate_plan((path_from_pattern(pattern),))

        assert plan.full_gate is True
        assert tuple(step.argv for step in plan.steps) == tuple(
            step.argv for recipe in CHECK_RECIPES for step in recipe.steps
        )


def test_an_empty_changeset_runs_the_complete_recipe_set_in_the_full_gate() -> None:
    plan = build_full_gate_plan(())

    assert plan.full_gate is True
    assert tuple(step.argv for step in plan.steps) == tuple(
        step.argv for recipe in CHECK_RECIPES for step in recipe.steps
    )


def test_explicit_full_execution_spawns_the_planned_recipe_set() -> None:
    run = run_full_check_observation(branch_path=SELECTED_GATE_PYTHON_SOURCE_PATH)

    assert run.exit_code == 0
    assert run.spawn_calls == tuple(
        step.argv
        for recipe in CHECK_RECIPES
        for step in (*PREFLIGHT_STEPS, *recipe.steps)
    )
