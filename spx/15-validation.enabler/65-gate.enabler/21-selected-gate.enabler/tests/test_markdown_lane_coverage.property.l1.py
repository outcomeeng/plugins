"""Property evidence for Markdown-lane coverage of the selected gate."""

from __future__ import annotations

from outcomeeng.validation.selected_gate import build_selected_gate_plan
from outcomeeng_testing.harnesses.markdown_lane import (
    declared_lane_command_lines,
    markdown_lane_property,
    without_launcher,
)


@markdown_lane_property
def _selected_steps_are_run_by_a_declared_markdown_lane(paths: list[str]) -> None:
    declared_lines = declared_lane_command_lines()

    plan = build_selected_gate_plan(tuple(paths))

    assert plan.selected_steps
    for selected in plan.selected_steps:
        step_tokens = without_launcher(selected.step.argv)
        assert any(
            line[: len(step_tokens)] == step_tokens for line in declared_lines
        ), (
            f"step {selected.step.label!r} ({' '.join(step_tokens)}) is selected for "
            f"{paths} and no declared Markdown lane runs it"
        )


def test_selected_steps_are_run_by_a_declared_markdown_lane() -> None:
    _selected_steps_are_run_by_a_declared_markdown_lane()
