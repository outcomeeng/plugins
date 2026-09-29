"""Compliance evidence for selected gate execution."""

from __future__ import annotations

import pytest

from outcomeeng.validation import (
    CHECK_RECIPES,
    PREFLIGHT_STEPS,
    PYTEST_ARGV,
    RECIPE_CHECK,
    RECIPE_TEST,
    RECIPE_VALIDATION,
    SUMMARY_KEY_ARGV,
    SUMMARY_KEY_RECIPE,
)
from outcomeeng.validation.infrastructure_index import (
    InfrastructureReach,
    index_test_infrastructure,
)
from outcomeeng.validation.selected_gate import (
    DEFAULT_BASE_REF,
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
    LIVE_DISCOVERY_PATTERNS,
    LIVE_DISCOVERY_TEST,
    SELECTED_CHECK_PLAN_HEADER,
    TEST_REASON,
    branch_diff_argv,
    build_selected_gate_plan,
    load_changeset_scope,
)
from outcomeeng_testing.generators.gate import (
    DELETED_GIT_STATUS,
    GIT_DISCOVERY_FAILURE_STDERR,
    GIT_DISCOVERY_FAILURE_STDOUT,
    assertion_test_paths,
    discovery_full_gate_paths,
    high_volume_child_output,
    lane_paths,
    path_from_pattern,
    required_domain,
    unrelated_full_gate_paths,
)
from outcomeeng_testing.harnesses.gate import (
    CredentialAvailability,
    across_credential_availability,
    check_full_observation,
    collect_selected_gate_paths,
    entry_point_check_observation,
    entry_point_test_observation,
    failing_discovery_runner,
    production_check_observation,
    repository_without_origin,
    run_check_observation,
    summary_recipes,
    summary_steps,
)
from outcomeeng_testing.harnesses.infrastructure_index import (
    reach_layout,
    synthetic_repository,
)


def test_an_empty_changeset_selects_no_steps() -> None:
    plan = build_selected_gate_plan(())

    assert plan.steps == ()
    assert plan.full_gate is False


@pytest.mark.parametrize("path", lane_paths())
def test_the_plan_prints_before_the_recipes_run(path: str) -> None:
    run = run_check_observation(branch_path=path)
    with synthetic_repository() as repo:
        plan = build_selected_gate_plan(
            (path,), test_infrastructure=index_test_infrastructure(repo.root)
        )
    preflight_argvs = {step.argv for step in PREFLIGHT_STEPS}
    announced = run.output_before_first_spawn.splitlines()
    # One shared cursor over the announced lines: each selected step must name
    # its label and reason on a line after the previous step's line.
    cursor = iter(enumerate(announced))
    announcing_lines = [
        next(
            (
                index
                for index, line in cursor
                if item.step.label in line and item.reason in line
            ),
            None,
        )
        for item in plan.selected_steps
    ]

    assert run.exit_code == 0
    assert plan.selected_steps
    assert announced[0] == SELECTED_CHECK_PLAN_HEADER
    assert None not in announcing_lines, announcing_lines
    assert run.spawn_calls[: len(PREFLIGHT_STEPS)] == tuple(
        step.argv for step in PREFLIGHT_STEPS
    )
    assert tuple(call for call in run.spawn_calls if call not in preflight_argvs) == (
        tuple(step.argv for step in plan.steps)
    )
    assert run.summary is not None
    assert run.summary[SUMMARY_KEY_RECIPE] == RECIPE_CHECK
    assert [step[SUMMARY_KEY_ARGV] for step in summary_steps(run.summary)] == [
        list(argv) for argv in run.spawn_calls
    ]


@pytest.mark.parametrize("path", lane_paths())
def test_child_output_never_streams_to_the_live_sink(path: str) -> None:
    child_output = high_volume_child_output()

    run = run_check_observation(branch_path=path, child_output=child_output)

    assert run.exit_code == 0
    assert child_output not in run.output
    assert len(run.output.splitlines()) < len(child_output.splitlines())


@pytest.mark.parametrize("path", discovery_full_gate_paths())
def test_a_full_gate_path_runs_the_complete_wrapper(path: str) -> None:
    run = run_check_observation(branch_path=path)

    assert run.exit_code == 0
    assert run.spawn_calls == tuple(
        step.argv
        for recipe in CHECK_RECIPES
        for step in (*recipe.preflight_steps, *recipe.steps)
    )
    assert FULL_GATE_REASON in run.output_before_first_spawn
    assert run.summary is not None
    assert [recipe[SUMMARY_KEY_RECIPE] for recipe in summary_recipes(run.summary)] == [
        RECIPE_VALIDATION,
        RECIPE_TEST,
    ]


def test_a_deleted_test_path_selects_no_pytest_run() -> None:
    (test_path,) = assertion_test_paths(1)

    run = run_check_observation(branch_path=test_path, branch_status=DELETED_GIT_STATUS)

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
    assert run.runner_calls == (branch_diff_argv(DEFAULT_BASE_REF),)
    assert GIT_DISCOVERY_ERROR_PREFIX in run.output
    assert GIT_DISCOVERY_STDOUT_LABEL in run.output
    assert GIT_DISCOVERY_STDERR_LABEL in run.output
    assert GIT_DISCOVERY_FAILURE_STDOUT in run.output
    assert GIT_DISCOVERY_FAILURE_STDERR in run.output


def test_a_repo_without_origin_reports_the_unset_head() -> None:
    changeset_scope = load_changeset_scope()
    with repository_without_origin() as repo:
        run = production_check_observation(repo)
        with pytest.raises(changeset_scope.BaseRefNotConfiguredError) as helper_failure:
            changeset_scope.detect_base_ref(repo)

    assert run.exit_code == GIT_DISCOVERY_FAILURE_EXIT_CODE
    assert run.spawn_calls == ()
    assert GIT_DISCOVERY_ERROR_PREFIX in run.output
    assert changeset_scope.ORIGIN_HEAD_REF in run.output
    assert str(helper_failure.value) in run.output


def test_the_check_entry_point_reports_the_unset_head_as_the_selected_gate_does() -> (
    None
):
    with repository_without_origin() as repo:
        entry = entry_point_check_observation(repo)
        direct = production_check_observation(repo)

    assert entry.exit_code == GIT_DISCOVERY_FAILURE_EXIT_CODE
    assert entry.spawn_calls == ()
    assert GIT_DISCOVERY_ERROR_PREFIX in entry.output
    assert entry.output == direct.output


def test_collection_propagates_git_failure_as_a_typed_error() -> None:
    runner = failing_discovery_runner(
        stdout=GIT_DISCOVERY_FAILURE_STDOUT, stderr=GIT_DISCOVERY_FAILURE_STDERR
    )

    with pytest.raises(GitDiscoveryError) as caught:
        with synthetic_repository() as repo:
            collect_selected_gate_paths(repo.root, runner=runner)

    assert GIT_DISCOVERY_ERROR_PREFIX in str(caught.value)
    assert GIT_DISCOVERY_FAILURE_STDERR in str(caught.value)
    assert runner.calls == [branch_diff_argv(DEFAULT_BASE_REF)]


def test_infrastructure_path_without_an_index_is_rejected_by_name() -> None:
    with synthetic_repository() as repo:
        layout = reach_layout(InfrastructureReach.NODE_LOCAL, repo)

    with pytest.raises(InfrastructureIndexRequired) as caught:
        build_selected_gate_plan((layout.changed_path,))

    assert caught.value.paths == (layout.changed_path,)
    assert layout.changed_path in str(caught.value)


def test_definition_guidance_changes_require_the_live_check() -> None:
    plans = across_credential_availability(
        lambda: build_selected_gate_plan((INSTRUCTION_BLOCK_SOURCE_PATH,))
    )

    assert set(plans) == set(CredentialAvailability)
    assert plans[CredentialAvailability.PRESENT] == plans[CredentialAvailability.ABSENT]
    for plan in plans.values():
        assert plan.live_discovery
        assert any(LIVE_DISCOVERY_TEST in step.argv for step in plan.steps)
        assert plan.live_discovery_reason == LIVE_DISCOVERY_INCLUDED_REASON


@pytest.mark.parametrize(
    "pattern", required_domain(LIVE_DISCOVERY_PATTERNS, "live-discovery patterns")
)
def test_each_declared_discovery_surface_requires_the_live_check(pattern: str) -> None:
    with synthetic_repository() as repo:
        index = index_test_infrastructure(repo.root)
        plans = across_credential_availability(
            lambda: build_selected_gate_plan(
                (path_from_pattern(pattern),), test_infrastructure=index
            )
        )

    assert set(plans) == set(CredentialAvailability)
    assert plans[CredentialAvailability.PRESENT] == plans[CredentialAvailability.ABSENT]
    for plan in plans.values():
        assert plan.live_discovery
        assert plan.live_discovery_reason == LIVE_DISCOVERY_INCLUDED_REASON
        assert any(
            step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
            and (plan.full_gate or LIVE_DISCOVERY_TEST in step.argv)
            and step.argv[-len(LIVE_DISCOVERY_EXCLUSION) :] != LIVE_DISCOVERY_EXCLUSION
            for step in plan.steps
        )


def test_discovery_inclusion_is_printed_before_execution() -> None:
    runs = across_credential_availability(
        lambda: run_check_observation(branch_path=INSTRUCTION_BLOCK_SOURCE_PATH)
    )

    assert set(runs) == set(CredentialAvailability)
    assert (
        runs[CredentialAvailability.PRESENT].output_before_first_spawn
        == runs[CredentialAvailability.ABSENT].output_before_first_spawn
    )
    for run in runs.values():
        assert run.exit_code == 0
        assert run.spawn_calls
        assert LIVE_DISCOVERY_INCLUDED_REASON in run.output_before_first_spawn


def test_unrelated_automatic_full_gate_excludes_only_the_live_check() -> None:
    with synthetic_repository() as repo:
        layout = reach_layout(InfrastructureReach.SHARED, repo)
        index = index_test_infrastructure(repo.root)
        plans = across_credential_availability(
            lambda: build_selected_gate_plan(
                (layout.changed_path,), test_infrastructure=index
            )
        )

    assert set(plans) == set(CredentialAvailability)
    assert plans[CredentialAvailability.PRESENT] == plans[CredentialAvailability.ABSENT]
    for plan in plans.values():
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


@pytest.mark.parametrize("path", unrelated_full_gate_paths())
def test_unrelated_full_gate_execution_honors_its_exclusion(path: str) -> None:
    runs = across_credential_availability(
        lambda: run_check_observation(branch_path=path)
    )

    assert set(runs) == set(CredentialAvailability)
    assert (
        runs[CredentialAvailability.PRESENT].output_before_first_spawn
        == runs[CredentialAvailability.ABSENT].output_before_first_spawn
    )
    for run in runs.values():
        assert run.exit_code == 0
        assert any(
            call[: len(PYTEST_ARGV)] == PYTEST_ARGV
            and call[-len(LIVE_DISCOVERY_EXCLUSION) :] == LIVE_DISCOVERY_EXCLUSION
            for call in run.spawn_calls
        )
        assert LIVE_DISCOVERY_EXCLUDED_REASON in run.output_before_first_spawn


@pytest.mark.parametrize("path", discovery_full_gate_paths())
def test_relevant_full_gate_keeps_live_discovery_enabled(path: str) -> None:
    plans = across_credential_availability(lambda: build_selected_gate_plan((path,)))

    assert set(plans) == set(CredentialAvailability)
    assert plans[CredentialAvailability.PRESENT] == plans[CredentialAvailability.ABSENT]
    for plan in plans.values():
        assert plan.full_gate
        assert plan.live_discovery
        assert plan.steps == tuple(
            step for recipe in CHECK_RECIPES for step in recipe.steps
        )


def test_explicit_full_verification_runs_live_discovery() -> None:
    runs = across_credential_availability(check_full_observation)
    full_steps = tuple(
        step.argv
        for recipe in CHECK_RECIPES
        for step in (*recipe.preflight_steps, *recipe.steps)
    )

    assert set(runs) == set(CredentialAvailability)
    for run in runs.values():
        assert run.exit_code == 0
        assert run.spawn_calls == full_steps
        assert any(call[: len(PYTEST_ARGV)] == PYTEST_ARGV for call in run.spawn_calls)
        assert all(
            call[-len(LIVE_DISCOVERY_EXCLUSION) :] != LIVE_DISCOVERY_EXCLUSION
            for call in run.spawn_calls
        )


def test_direct_execution_of_live_check_runs_live_discovery() -> None:
    runs = across_credential_availability(
        lambda: entry_point_test_observation((LIVE_DISCOVERY_TEST,))
    )

    assert set(runs) == set(CredentialAvailability)
    for run in runs.values():
        pytest_calls = [
            call for call in run.spawn_calls if call[: len(PYTEST_ARGV)] == PYTEST_ARGV
        ]
        assert run.exit_code == 0
        assert pytest_calls == [(*PYTEST_ARGV, LIVE_DISCOVERY_TEST)]
        assert all(
            call[index : index + len(LIVE_DISCOVERY_EXCLUSION)]
            != LIVE_DISCOVERY_EXCLUSION
            for call in pytest_calls
            for index in range(len(call))
        )
