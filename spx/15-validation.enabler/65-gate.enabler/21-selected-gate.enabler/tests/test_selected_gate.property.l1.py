"""Property evidence for selected gate determinism."""

from __future__ import annotations

from outcomeeng.validation import ON_DEMAND_LEVEL, PYTEST_ARGV
from outcomeeng.validation.infrastructure_index import SPEC_TREE_ROOT
from outcomeeng.validation.selected_gate import build_selected_gate_plan
from outcomeeng_testing.generators.gate import GeneratedTestFile
from outcomeeng_testing.harnesses.gate import (
    SELECTED_GATE_PROPERTY_REPLAY_PATH,
    SELECTED_GATE_PROPERTY_SEED,
    captured_property_failure_notes,
    on_demand_suite_property,
    selected_gate_property,
    selected_gate_reach_index,
)
from outcomeeng_testing.harnesses.property_evidence import (
    REPLAY_NOTE_PREFIX,
    SEED_NOTE_PREFIX,
)


@selected_gate_property
def _selection_is_order_and_duplication_insensitive(paths: list[str]) -> None:
    index = selected_gate_reach_index()

    forward = build_selected_gate_plan(tuple(paths), test_infrastructure=index)
    reverse = build_selected_gate_plan(
        tuple(reversed(paths * 2)), test_infrastructure=index
    )

    assert forward == reverse


def test_selection_is_deterministic_for_path_order_and_duplicates() -> None:
    _selection_is_order_and_duplication_insensitive()


@on_demand_suite_property
def _planned_pytest_targets_lie_outside_the_on_demand_suite(
    test_files: list[GeneratedTestFile],
) -> None:
    paths = tuple(f"{SPEC_TREE_ROOT}/{test_file.path}" for test_file in test_files)
    expected = {
        path
        for path, test_file in zip(paths, test_files, strict=True)
        if test_file.level != ON_DEMAND_LEVEL
    }

    plan = build_selected_gate_plan(paths)

    assert [
        set(step.argv[len(PYTEST_ARGV) :])
        for step in plan.steps
        if step.argv[: len(PYTEST_ARGV)] == PYTEST_ARGV
    ] == ([expected] if expected else [])


def test_planned_pytest_targets_lie_outside_the_on_demand_suite() -> None:
    _planned_pytest_targets_lie_outside_the_on_demand_suite()


def test_property_failure_reports_seed_and_replay_path() -> None:
    @selected_gate_property
    def always_fails(paths: list[str]) -> None:
        assert not paths

    notes = captured_property_failure_notes(always_fails)

    assert f"{SEED_NOTE_PREFIX}{SELECTED_GATE_PROPERTY_SEED}" in notes
    assert f"{REPLAY_NOTE_PREFIX}{SELECTED_GATE_PROPERTY_REPLAY_PATH}" in notes
