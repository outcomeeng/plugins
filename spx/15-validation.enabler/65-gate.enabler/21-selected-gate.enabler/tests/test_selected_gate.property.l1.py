"""Property evidence for selected gate determinism."""

from __future__ import annotations

from outcomeeng.validation import L3_LEVEL
from outcomeeng.validation.infrastructure_index import PRODUCT_TREE_ROOT
from outcomeeng.validation.selected_gate import build_selected_gate_plan
from outcomeeng_testing.generators.gate import GeneratedTestFile
from outcomeeng_testing.harnesses.gate import (
    SELECTED_GATE_PROPERTY_REPLAY_PATH,
    SELECTED_GATE_PROPERTY_SEED,
    captured_property_failure_notes,
    l3_tests_property,
    selected_gate_property,
    selected_gate_reach_index,
)
from outcomeeng_testing.harnesses.l3_collection import plan_pytest_arguments
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


@l3_tests_property
def _planned_pytest_targets_lie_outside_the_l3_tests(
    test_files: list[GeneratedTestFile],
) -> None:
    paths = tuple(f"{PRODUCT_TREE_ROOT}/{test_file.path}" for test_file in test_files)
    expected = {
        path
        for path, test_file in zip(paths, test_files, strict=True)
        if test_file.level != L3_LEVEL
    }

    plan = build_selected_gate_plan(paths)

    assert [set(arguments) for arguments in plan_pytest_arguments(plan)] == (
        [expected] if expected else []
    )


def test_planned_pytest_targets_lie_outside_the_l3_tests() -> None:
    _planned_pytest_targets_lie_outside_the_l3_tests()


def test_property_failure_reports_seed_and_replay_path() -> None:
    @selected_gate_property
    def always_fails(paths: list[str]) -> None:
        assert not paths

    notes = captured_property_failure_notes(always_fails)

    assert f"{SEED_NOTE_PREFIX}{SELECTED_GATE_PROPERTY_SEED}" in notes
    assert f"{REPLAY_NOTE_PREFIX}{SELECTED_GATE_PROPERTY_REPLAY_PATH}" in notes
