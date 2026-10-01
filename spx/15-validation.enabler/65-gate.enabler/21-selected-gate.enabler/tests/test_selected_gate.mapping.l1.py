"""Mapping evidence for selected local gate planning."""

from __future__ import annotations

import pytest

from outcomeeng.distribution.contracts import INSTRUCTION_BLOCK_ARGV
from outcomeeng.validation import (
    EVAL_LINKS_ARGV,
    EVAL_PROMPTS_ARGV,
    EVAL_TRIGGERS_ARGV,
    PYTEST_ARGV,
    TEST_STEPS,
    VALIDATION_STEPS,
)
from outcomeeng.validation._steps import RUNTIME_TOKEN_STEP
from outcomeeng.validation.infrastructure_index import (
    InfrastructureReach,
    SPEC_TREE_ROOT,
    index_test_infrastructure,
)
from outcomeeng.validation.selected_gate import (
    EVAL_CONFIGURATION_REASON,
    FULL_GATE_REASON,
    INSTRUCTION_BLOCK_REASON,
    INSTRUCTION_BLOCK_SOURCE_PATH,
    LIVE_DISCOVERY_EXCLUSION,
    PYTHON_ASSERTION_TEST_PATTERNS,
    PYTHON_REASON,
    REACHED_TESTS_REASON,
    REASON_SEPARATOR,
    SELECTION_LANES,
    SHARED_TEST_INFRASTRUCTURE_REASON,
    SKILL_LANE,
    SKILL_REASON,
    SelectedGatePlan,
    SelectionLane,
    TEST_REASON,
    UNTRACEABLE_TEST_INFRASTRUCTURE_REASON,
    EVIDENCE_LINK_PATTERNS,
    EVIDENCE_LINK_REASON,
    branch_diff_argv,
    build_selected_gate_plan,
)
from outcomeeng_testing.generators.gate import (
    alternate_base_ref,
    assertion_test_paths,
    distinct_changed_paths,
    full_gate_paths,
    guarded_eval_configuration_paths,
    guarded_eval_definition_paths,
    outside_spec_tree_paths,
    path_from_pattern,
    pattern_representatives,
    renamed_away_path,
    required_domain,
    selection_lane_paths,
    selection_paths,
    spec_tree_paths,
    whitespace_paths,
)
from outcomeeng_testing.harnesses import gate as gate_harness
from outcomeeng_testing.harnesses.gate import (
    ChangeKind,
    PathChange,
    RepositoryChanges,
    collected_entries_observation,
    collected_paths_observation,
    resolved_base_observation,
    run_check_observation,
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


def _reason_by_argv(plan: SelectedGatePlan) -> dict[tuple[str, ...], str]:
    return {item.step.argv: item.reason for item in plan.selected_steps}


def _plan_in_synthetic_repository(path: str) -> SelectedGatePlan:
    with synthetic_repository() as repo:
        return build_selected_gate_plan(
            (path,), test_infrastructure=index_test_infrastructure(repo.root)
        )


@pytest.mark.parametrize(
    "lane",
    required_domain(SELECTION_LANES, "selection lanes"),
    ids=[f"lane-{position}" for position, _ in enumerate(SELECTION_LANES)],
)
def test_every_path_a_lane_declares_selects_that_lanes_steps_with_its_reason(
    lane: SelectionLane,
) -> None:
    for path in selection_lane_paths(lane):
        plan = _plan_in_synthetic_repository(path)
        reason_by_argv = _reason_by_argv(plan)

        assert set(lane.argvs) <= set(reason_by_argv), path
        assert all(reason.strip() for reason in reason_by_argv.values()), path
        if not plan.full_gate:
            assert all(
                lane.reason in reason_by_argv[argv].split(REASON_SEPARATOR)
                for argv in lane.argvs
            ), path


@pytest.mark.parametrize(
    "path", (*selection_paths(), *guarded_eval_configuration_paths())
)
def test_every_changed_path_selects_an_ordered_subset_of_source_owned_steps(
    path: str,
) -> None:
    plan = _plan_in_synthetic_repository(path)
    validation_positions = {
        step.argv: position for position, step in enumerate(VALIDATION_STEPS)
    }
    selected = _argvs(plan)
    positions = [
        validation_positions[argv] for argv in selected if argv in validation_positions
    ]
    trailing = selected[len(positions) :]

    assert selected
    assert positions == sorted(set(positions))
    assert all(argv[: len(PYTEST_ARGV)] == PYTEST_ARGV for argv in trailing)
    assert all(reason.strip() for reason in _reasons(plan))
    assert _plan_in_synthetic_repository(path) == plan
    if not plan.full_gate:
        assert all(
            any(
                item.step.argv in lane.argvs
                and lane.reason in item.reason.split(REASON_SEPARATOR)
                for lane in SELECTION_LANES
            )
            for item in plan.selected_steps
            if item.step.argv in validation_positions
        )


@pytest.mark.parametrize(
    "pattern", required_domain(PYTHON_ASSERTION_TEST_PATTERNS, "assertion patterns")
)
@pytest.mark.parametrize("deleted", (False, True))
def test_every_assertion_path_category_maps_presence_to_targeted_execution(
    pattern: str, deleted: bool
) -> None:
    path = path_from_pattern(pattern)
    plan = build_selected_gate_plan((path,), deleted_paths=(path,) if deleted else ())

    targets = {
        argument
        for step in plan.steps
        if step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
        for argument in step.argv[len(PYTEST_ARGV) :]
    }
    assert (path in targets) is not deleted


@pytest.mark.parametrize(
    "pattern", required_domain(EVIDENCE_LINK_PATTERNS, "evidence-link patterns")
)
def test_every_evidence_link_path_category_selects_link_validation(
    pattern: str,
) -> None:
    path = path_from_pattern(pattern)
    inside = build_selected_gate_plan((path,))
    outside = build_selected_gate_plan((path.removeprefix(f"{SPEC_TREE_ROOT}/"),))

    assert EVAL_LINKS_ARGV in _argvs(inside)
    assert EVAL_LINKS_ARGV not in _argvs(outside)


@pytest.mark.parametrize("path", spec_tree_paths(selection_paths()))
def test_spec_tree_paths_select_the_evidence_link_step(path: str) -> None:
    plan = _plan_in_synthetic_repository(path)

    assert EVAL_LINKS_ARGV in _argvs(plan)
    assert plan.full_gate or EVIDENCE_LINK_REASON in _reason_by_argv(plan)[
        EVAL_LINKS_ARGV
    ].split(REASON_SEPARATOR)


@pytest.mark.parametrize("path", outside_spec_tree_paths(selection_paths()))
def test_paths_outside_the_spec_tree_select_the_evidence_link_step_only_with_the_full_surface(
    path: str,
) -> None:
    plan = _plan_in_synthetic_repository(path)

    assert (EVAL_LINKS_ARGV in _argvs(plan)) is plan.full_gate


@pytest.mark.parametrize("path", guarded_eval_definition_paths())
def test_an_eval_definition_selects_both_currency_checks_and_the_configuration_guard(
    path: str,
) -> None:
    # An eval definition generates both the CI trigger list and, for a
    # producer-coupled suite, the materialized prompt, and the runtime-token
    # step's configuration guard reads it for a literal model identifier.
    plan = build_selected_gate_plan((path,))

    assert plan.full_gate is False
    assert {RUNTIME_TOKEN_STEP.argv, EVAL_TRIGGERS_ARGV, EVAL_PROMPTS_ARGV} <= set(
        _argvs(plan)
    )


@pytest.mark.parametrize("path", guarded_eval_configuration_paths())
def test_every_file_the_configuration_guard_reads_selects_the_runtime_token_step(
    path: str,
) -> None:
    # The guard reads every eval definition under the spec tree and each prompt
    # template it declares; a change to any of them selects the step that runs
    # the guard, without widening to the full gate.
    plan = build_selected_gate_plan((path,))

    assert plan.full_gate is False
    assert _reason_by_argv(plan)[RUNTIME_TOKEN_STEP.argv] == EVAL_CONFIGURATION_REASON


@pytest.mark.parametrize("path", guarded_eval_configuration_paths())
def test_a_guarded_eval_file_beside_a_skill_path_names_both_runtime_token_reasons(
    path: str,
) -> None:
    skill_paths = pattern_representatives(SKILL_LANE.patterns)
    assert skill_paths

    for skill_path in skill_paths:
        plan = build_selected_gate_plan((skill_path, path))

        reasons = _reason_by_argv(plan)[RUNTIME_TOKEN_STEP.argv]
        assert set(reasons.split(REASON_SEPARATOR)) == {
            SKILL_REASON,
            EVAL_CONFIGURATION_REASON,
        }, skill_path


@pytest.mark.parametrize("path", spec_tree_paths(selection_paths()))
def test_spec_tree_paths_the_configuration_guard_does_not_read_leave_it_unselected(
    path: str,
) -> None:
    assert path not in guarded_eval_configuration_paths()

    plan = build_selected_gate_plan((path,))

    assert RUNTIME_TOKEN_STEP.argv not in _argvs(plan)


def test_deleted_assertion_tests_never_select_pytest() -> None:
    test_path, surviving_test_path = assertion_test_paths(2)

    plan = build_selected_gate_plan((test_path,), deleted_paths=(test_path,))
    assert all(item.reason != TEST_REASON for item in plan.selected_steps)

    # Modified on the branch, then deleted from the working tree: git reports
    # both statuses for one path, and the absent file resolves it as deleted.
    observation = collected_entries_observation(
        RepositoryChanges(
            branch=(PathChange(test_path, ChangeKind.MODIFY),),
            unstaged=(PathChange(test_path, ChangeKind.DELETE),),
        )
    )
    assert len({entry.status for entry in observation.entries}) > 1
    assert observation.deleted_paths == (test_path,)
    plan = build_selected_gate_plan(
        (test_path,), deleted_paths=observation.deleted_paths
    )
    assert all(item.reason != TEST_REASON for item in plan.selected_steps)

    plan = build_selected_gate_plan(
        (test_path, surviving_test_path),
        deleted_paths=(test_path,),
    )
    assert plan.selected_steps[-1].reason == TEST_REASON
    assert plan.selected_steps[-1].step.argv == (*PYTEST_ARGV, surviving_test_path)


@pytest.mark.parametrize("path", full_gate_paths())
def test_full_gate_paths_select_the_complete_recipe_set(path: str) -> None:
    plan = build_selected_gate_plan((path,))

    assert plan.full_gate is True
    assert tuple(
        step.argv[: -len(LIVE_DISCOVERY_EXCLUSION)]
        if step.argv[-len(LIVE_DISCOVERY_EXCLUSION) :] == LIVE_DISCOVERY_EXCLUSION
        else step.argv
        for step in plan.steps
    ) == tuple(step.argv for step in (*VALIDATION_STEPS, *TEST_STEPS))
    assert set(_reasons(plan)) == {FULL_GATE_REASON}


def test_the_instruction_block_source_selects_the_currency_check() -> None:
    plan = build_selected_gate_plan((INSTRUCTION_BLOCK_SOURCE_PATH,))

    assert _reason_by_argv(plan)[INSTRUCTION_BLOCK_ARGV] == INSTRUCTION_BLOCK_REASON


def test_changed_paths_collect_from_all_four_git_surfaces() -> None:
    branch_path, staged_path, unstaged_path, untracked_path = distinct_changed_paths(4)

    observation = collected_paths_observation(
        RepositoryChanges(
            branch=(PathChange(branch_path),),
            staged=(PathChange(staged_path),),
            unstaged=(PathChange(unstaged_path, ChangeKind.MODIFY),),
            untracked=(untracked_path,),
        )
    )

    assert observation.collected == tuple(sorted(observation.named))
    assert observation.runner_calls
    assert set(observation.runner_repos) == {observation.repo}


@pytest.mark.parametrize("path", whitespace_paths())
def test_whitespace_paths_survive_collection_from_every_surface(path: str) -> None:
    surfaces = (
        RepositoryChanges(branch=(PathChange(path),)),
        RepositoryChanges(staged=(PathChange(path),)),
        RepositoryChanges(unstaged=(PathChange(path, ChangeKind.MODIFY),)),
        RepositoryChanges(untracked=(path,)),
    )

    for changes in surfaces:
        assert collected_paths_observation(changes).collected == (path,), changes


def test_a_path_changed_on_every_tracked_surface_collects_once() -> None:
    (path,) = distinct_changed_paths(1)

    observation = collected_paths_observation(
        RepositoryChanges(
            branch=(PathChange(path, ChangeKind.MODIFY),),
            staged=(PathChange(path, ChangeKind.MODIFY),),
            unstaged=(PathChange(path, ChangeKind.MODIFY),),
        )
    )

    assert observation.collected == (path,)


def test_an_injected_base_ref_resolver_drives_branch_discovery() -> None:
    (branch_path,) = distinct_changed_paths(1)

    observation = resolved_base_observation(
        base_ref=alternate_base_ref(),
        changes=RepositoryChanges(branch=(PathChange(branch_path),)),
    )

    assert observation.collected == (branch_path,)
    assert observation.resolver_repos == (observation.repo,)
    assert observation.first_runner_call == branch_diff_argv(alternate_base_ref())


def test_a_rename_collects_both_sides() -> None:
    (test_path,) = assertion_test_paths(1)
    renamed_path = renamed_away_path(test_path)

    observation = collected_paths_observation(
        RepositoryChanges(
            branch=(PathChange(renamed_path, ChangeKind.RENAME, source=test_path),)
        )
    )

    assert observation.collected == tuple(sorted((test_path, renamed_path)))


def test_a_renamed_test_source_never_reaches_pytest() -> None:
    (test_path,) = assertion_test_paths(1)

    run = run_check_observation(
        RepositoryChanges(
            branch=(
                PathChange(
                    renamed_away_path(test_path), ChangeKind.RENAME, source=test_path
                ),
            )
        )
    )

    assert run.exit_code == 0
    assert all(PYTEST_ARGV != call[: len(PYTEST_ARGV)] for call in run.spawn_calls)
    assert PYTHON_REASON in run.output


def test_a_deleted_then_restored_test_still_runs_when_present() -> None:
    (test_path,) = assertion_test_paths(1)

    run = run_check_observation(
        RepositoryChanges(
            branch=(PathChange(test_path, ChangeKind.DELETE),),
            staged=(PathChange(test_path),),
        )
    )

    assert run.exit_code == 0
    assert run.spawn_calls[-1] == (*PYTEST_ARGV, test_path)


def test_a_copy_collects_both_sides() -> None:
    (test_path,) = assertion_test_paths(1)
    copied_path = renamed_away_path(test_path)

    observation = collected_paths_observation(
        RepositoryChanges(
            branch=(PathChange(copied_path, ChangeKind.COPY, source=test_path),)
        )
    )

    assert observation.collected == tuple(sorted((test_path, copied_path)))


def test_a_copied_test_selects_pytest_for_the_surviving_source() -> None:
    (test_path,) = assertion_test_paths(1)

    run = run_check_observation(
        RepositoryChanges(
            branch=(
                PathChange(
                    renamed_away_path(test_path), ChangeKind.COPY, source=test_path
                ),
            )
        )
    )

    assert run.exit_code == 0
    assert (*PYTEST_ARGV, test_path) in run.spawn_calls


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
        assert tuple(step.argv for step in plan.steps) == (
            *(step.argv for step in VALIDATION_STEPS),
            *((*step.argv, *LIVE_DISCOVERY_EXCLUSION) for step in TEST_STEPS),
        )
        assert set(_reasons(plan)) == {SHARED_TEST_INFRASTRUCTURE_REASON}
    elif kind is InfrastructureReach.UNTRACEABLE:
        assert plan.full_gate is True
        assert tuple(step.argv for step in plan.steps) == (
            *(step.argv for step in VALIDATION_STEPS),
            *((*step.argv, *LIVE_DISCOVERY_EXCLUSION) for step in TEST_STEPS),
        )
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
