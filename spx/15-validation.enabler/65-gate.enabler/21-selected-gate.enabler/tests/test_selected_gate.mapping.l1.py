"""Mapping evidence for selected local gate planning."""

from __future__ import annotations

from collections.abc import Sequence
from fnmatch import fnmatchcase

import pytest

from outcomeeng.distribution.contracts import INSTRUCTION_BLOCK_ARGV
from outcomeeng.validation import (
    ACTIONLINT_ARGV,
    EVAL_LINKS_ARGV,
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
from outcomeeng.validation._steps import RUNTIME_TOKEN_STEP
from outcomeeng.validation.infrastructure_index import (
    InfrastructureReach,
    SPEC_TREE_ROOT,
    index_test_infrastructure,
)
from outcomeeng.validation.selected_gate import (
    ChangedPath,
    EVAL_CONFIGURATION_REASON,
    EVAL_REASON,
    EVIDENCE_LINK_REASON,
    FULL_GATE_REASON,
    INSTRUCTION_BLOCK_REASON,
    LIVE_DISCOVERY_EXCLUSION,
    LIVE_DISCOVERY_INCLUDED_REASON,
    LIVE_DISCOVERY_TEST,
    MARKDOWN_REASON,
    PYTHON_REASON,
    REACHED_TESTS_REASON,
    REASON_SEPARATOR,
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
from outcomeeng.validation import selected_gate as selection_source
from outcomeeng_testing.generators.gate import (
    SELECTED_GATE_EVAL_DEFINITION_PATH,
    SELECTED_GATE_INSTRUCTION_BLOCK_SOURCE_PATH,
    SELECTED_GATE_LANE_PATH_EXAMPLES,
    SELECTED_GATE_MARKDOWN_PATH,
    SELECTED_GATE_PYTHON_SOURCE_PATH,
    SELECTED_GATE_PYTHON_TEST_PATH,
    SELECTED_GATE_README_PATH,
    SELECTED_GATE_SKILL_PATH,
    SELECTED_GATE_SPX_CONFIG_PATH,
    SELECTED_GATE_WORKFLOW_PATH,
    guarded_eval_configuration_paths,
    path_from_pattern,
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


def _selection(plan: SelectedGatePlan) -> tuple[tuple[tuple[str, ...], str], ...]:
    return tuple((item.step.argv, item.reason) for item in plan.selected_steps)


# The lane law: each source-declared path category selects the validation steps
# that check that category's files, and names the category as the reason. The
# categories, steps, and reasons are source-owned; this table declares only
# which steps check which category, the correspondence the spec assertion makes.
_PATTERN_LANES: tuple[tuple[tuple[str, ...], tuple[tuple[str, ...], ...], str], ...] = (
    (
        selection_source.MARKDOWN_PATTERNS,
        (FMT_CHECK_ARGV, SPX_MARKDOWN_ARGV),
        MARKDOWN_REASON,
    ),
    (
        selection_source.WORKFLOW_PATTERNS,
        (ACTIONLINT_ARGV, SHELLCHECK_ARGV),
        WORKFLOW_REASON,
    ),
    (
        selection_source.PYTHON_FORMAT_LINT_PATTERNS,
        (RUFF_FORMAT_ARGV, RUFF_CHECK_ARGV),
        PYTHON_REASON,
    ),
    (
        selection_source.PYTHON_TYPECHECK_PATTERNS,
        (MYPY_ARGV, PYRIGHT_ARGV),
        PYTHON_REASON,
    ),
    (
        selection_source.SKILL_PATTERNS,
        tuple(
            step.argv for step in VALIDATION_STEPS if step.label in SKILL_STEP_LABELS
        ),
        SKILL_REASON,
    ),
    (
        selection_source.INSTRUCTION_BLOCK_PATTERNS,
        (INSTRUCTION_BLOCK_ARGV,),
        INSTRUCTION_BLOCK_REASON,
    ),
    (selection_source.EVAL_TRIGGER_PATTERNS, (EVAL_TRIGGERS_ARGV,), EVAL_REASON),
    (selection_source.EVAL_PROMPT_PATTERNS, (EVAL_PROMPTS_ARGV,), EVAL_REASON),
    (
        selection_source.EVIDENCE_LINK_PATTERNS,
        (EVAL_LINKS_ARGV,),
        EVIDENCE_LINK_REASON,
    ),
)


def _matches(paths: Sequence[str], patterns: Sequence[str]) -> bool:
    return any(fnmatchcase(path, pattern) for path in paths for pattern in patterns)


def _lane_law_selection(
    paths: Sequence[str],
) -> tuple[tuple[tuple[str, ...], str], ...]:
    """The steps and reasons the lane law derives for lane-only changed paths.

    Every lane a path matches contributes its steps; a file the configuration
    guard reads contributes the runtime-token step after every pattern lane; a
    step contributed by several lanes names each lane's reason in that order.
    The selection keeps validation-step order and ends with the live-discovery
    test when a path matches a declared discovery surface.
    """
    contributions = [
        (argvs, reason)
        for patterns, argvs, reason in _PATTERN_LANES
        if _matches(paths, patterns)
    ]
    if set(guarded_eval_configuration_paths()).intersection(paths):
        contributions.append(((RUNTIME_TOKEN_STEP.argv,), EVAL_CONFIGURATION_REASON))
    reasons: dict[tuple[str, ...], list[str]] = {}
    for argvs, reason in contributions:
        for argv in argvs:
            reasons.setdefault(argv, []).append(reason)
    selection = [
        (step.argv, REASON_SEPARATOR.join(reasons[step.argv]))
        for step in VALIDATION_STEPS
        if step.argv in reasons
    ]
    if _matches(paths, selection_source.LIVE_DISCOVERY_PATTERNS):
        selection.append(
            ((*PYTEST_ARGV, LIVE_DISCOVERY_TEST), LIVE_DISCOVERY_INCLUDED_REASON)
        )
    return tuple(selection)


@pytest.mark.parametrize(
    ("patterns", "required_argvs", "reason"),
    _PATTERN_LANES,
)
def test_every_declared_path_category_selects_its_validation_lane(
    patterns: tuple[str, ...],
    required_argvs: tuple[tuple[str, ...], ...],
    reason: str,
) -> None:
    for pattern in patterns:
        with synthetic_repository() as repo:
            plan = build_selected_gate_plan(
                (path_from_pattern(pattern),),
                test_infrastructure=index_test_infrastructure(repo.root),
            )

        selected_argvs = _argvs(plan)
        assert set(required_argvs) <= set(selected_argvs)
        validation_argvs = tuple(
            step.argv for step in VALIDATION_STEPS if step.argv in selected_argvs
        )
        assert selected_argvs[: len(validation_argvs)] == validation_argvs
        assert all(reason.strip() for reason in _reasons(plan))
        if not plan.full_gate:
            reason_by_argv = dict(_selection(plan))
            assert all(reason in reason_by_argv[argv] for argv in required_argvs)


@pytest.mark.parametrize("pattern", selection_source.PYTHON_ASSERTION_TEST_PATTERNS)
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


@pytest.mark.parametrize("pattern", selection_source.EVIDENCE_LINK_PATTERNS)
def test_every_evidence_link_path_category_selects_link_validation(
    pattern: str,
) -> None:
    path = path_from_pattern(pattern)
    inside = build_selected_gate_plan((path,))
    outside = build_selected_gate_plan((path.removeprefix(f"{SPEC_TREE_ROOT}/"),))

    assert EVAL_LINKS_ARGV in _argvs(inside)
    assert EVAL_LINKS_ARGV not in _argvs(outside)


@pytest.mark.parametrize("path", SELECTED_GATE_LANE_PATH_EXAMPLES)
def test_a_lane_path_selects_exactly_its_lane_steps_in_validation_order(
    path: str,
) -> None:
    plan = build_selected_gate_plan((path,))

    assert plan.full_gate is False
    assert _selection(plan) == _lane_law_selection((path,))


def test_combined_lane_paths_merge_lanes_in_validation_step_order() -> None:
    plan = build_selected_gate_plan(SELECTED_GATE_LANE_PATH_EXAMPLES)

    assert plan.full_gate is False
    assert _selection(plan) == _lane_law_selection(SELECTED_GATE_LANE_PATH_EXAMPLES)


def test_an_eval_definition_selects_both_currency_checks_and_the_configuration_guard() -> (
    None
):
    # An eval definition generates both the CI trigger list and, for a
    # producer-coupled suite, the materialized prompt, and the runtime-token
    # step's configuration guard reads it for a literal model identifier.
    plan = build_selected_gate_plan((SELECTED_GATE_EVAL_DEFINITION_PATH,))

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

    reason_by_argv = {item.step.argv: item.reason for item in plan.selected_steps}
    assert plan.full_gate is False
    assert reason_by_argv[RUNTIME_TOKEN_STEP.argv] == EVAL_CONFIGURATION_REASON


@pytest.mark.parametrize("path", guarded_eval_configuration_paths())
def test_a_guarded_eval_file_beside_a_skill_path_names_both_runtime_token_reasons(
    path: str,
) -> None:
    plan = build_selected_gate_plan((SELECTED_GATE_SKILL_PATH, path))

    reason_by_argv = {item.step.argv: item.reason for item in plan.selected_steps}
    assert reason_by_argv[RUNTIME_TOKEN_STEP.argv] == REASON_SEPARATOR.join(
        (SKILL_REASON, EVAL_CONFIGURATION_REASON)
    )


@pytest.mark.parametrize(
    "path", (SELECTED_GATE_MARKDOWN_PATH, SELECTED_GATE_PYTHON_TEST_PATH)
)
def test_spec_tree_paths_the_configuration_guard_does_not_read_leave_it_unselected(
    path: str,
) -> None:
    plan = build_selected_gate_plan((path,))

    assert RUNTIME_TOKEN_STEP.argv not in _argvs(plan)


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
    selection_source.FULL_GATE_PATTERNS,
)
def test_full_gate_paths_select_the_complete_recipe_set(path: str) -> None:
    plan = build_selected_gate_plan((path_from_pattern(path),))

    assert plan.full_gate is True
    assert tuple(
        step.argv[: -len(LIVE_DISCOVERY_EXCLUSION)]
        if step.argv[-len(LIVE_DISCOVERY_EXCLUSION) :] == LIVE_DISCOVERY_EXCLUSION
        else step.argv
        for step in plan.steps
    ) == tuple(step.argv for step in (*VALIDATION_STEPS, *TEST_STEPS))
    assert set(_reasons(plan)) == {FULL_GATE_REASON}


@pytest.mark.parametrize(
    "path",
    (
        SELECTED_GATE_MARKDOWN_PATH,
        SELECTED_GATE_EVAL_DEFINITION_PATH,
        SELECTED_GATE_PYTHON_TEST_PATH,
    ),
)
def test_spec_tree_paths_select_the_evidence_link_step(path: str) -> None:
    plan = build_selected_gate_plan((path,))

    assert plan.full_gate is False
    reason_by_argv = {item.step.argv: item.reason for item in plan.selected_steps}
    assert reason_by_argv[EVAL_LINKS_ARGV] == EVIDENCE_LINK_REASON


@pytest.mark.parametrize(
    "path",
    (
        SELECTED_GATE_README_PATH,
        SELECTED_GATE_SPX_CONFIG_PATH,
        SELECTED_GATE_SKILL_PATH,
        SELECTED_GATE_WORKFLOW_PATH,
        SELECTED_GATE_PYTHON_SOURCE_PATH,
    ),
)
def test_paths_outside_the_spec_tree_never_select_the_evidence_link_step(
    path: str,
) -> None:
    plan = build_selected_gate_plan((path,))

    assert EVAL_LINKS_ARGV not in _argvs(plan)


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
