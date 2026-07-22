"""Mapping evidence for selected local gate planning."""

from __future__ import annotations

from outcomeeng_testing.harnesses.gate import (
    assert_selected_gate_mapping_contract,
    template_script_gate_mapping,
)


def test_selected_gate_mapping_contract() -> None:
    assert_selected_gate_mapping_contract()


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
