"""Mapping evidence for selected local gate planning."""

from __future__ import annotations

import pytest

from outcomeeng.validation import PYTEST_ARGV, TEST_STEPS, VALIDATION_STEPS
from outcomeeng.validation.selected_gate import (
    REACHED_TESTS_REASON,
    SHARED_TEST_INFRASTRUCTURE_REASON,
    UNTRACEABLE_TEST_INFRASTRUCTURE_REASON,
    build_selected_gate_plan,
)
from outcomeeng.validation.infrastructure_index import InfrastructureReach
from outcomeeng_testing.harnesses.gate import (
    assert_selected_gate_mapping_contract,
    template_script_gate_mapping,
)
from outcomeeng_testing.harnesses.infrastructure_index import (
    conftest_reach_layout,
    reach_layout,
    synthetic_repository,
)


def test_selected_gate_mapping_contract() -> None:
    assert_selected_gate_mapping_contract()


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
        assert plan.steps == (*VALIDATION_STEPS, *TEST_STEPS)
        assert {item.reason for item in plan.selected_steps} == {
            SHARED_TEST_INFRASTRUCTURE_REASON
        }
    elif kind is InfrastructureReach.UNTRACEABLE:
        assert plan.full_gate is True
        assert plan.steps == (*VALIDATION_STEPS, *TEST_STEPS)
        assert {item.reason for item in plan.selected_steps} == {
            UNTRACEABLE_TEST_INFRASTRUCTURE_REASON
        }
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
    assert {item.reason for item in plan.selected_steps} == {
        SHARED_TEST_INFRASTRUCTURE_REASON
    }


def test_template_script_maps_to_skill_and_lint_steps() -> None:
    # The template tree is an authored source root the generated-source
    # declaration and the raw-token enforcement roots both name, so a change to
    # a shipped template script has to reach the build, drift, and lint steps
    # that carry it into every plugin's generated tree.
    mapping = template_script_gate_mapping()

    assert not mapping.full_gate, (
        "a template script escalated to the full gate instead of selecting a subset"
    )
    assert mapping.selected, "a template script selected no validation step at all"
    assert mapping.selected == mapping.expected, (
        "selected steps and reasons differ from the expectation: "
        f"{set(mapping.selected) ^ set(mapping.expected)}"
    )
