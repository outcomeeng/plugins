"""Mapping evidence that the declared Markdown lanes run every selected gate step."""

from __future__ import annotations

from pathlib import Path

from outcomeeng.validation.infrastructure_index import TEST_INFRASTRUCTURE_PACKAGE
from outcomeeng.validation.selected_gate import build_selected_gate_plan
from outcomeeng_testing.harnesses.markdown_lanes import (
    declared_lanes,
    project_command,
    run_lanes,
    tracked_markdown_paths,
)


def test_every_step_selected_for_a_markdown_changeset_maps_to_a_markdown_lane_running_it(
    tmp_path: Path,
) -> None:
    markdown_lanes = tuple(
        lane for lane in declared_lanes() if "Markdown" in lane.label
    )
    # The overlay routes test infrastructure, Markdown fixtures included, to the
    # implementation lane, so no Markdown lane covers a path under that package.
    covered_paths = tuple(
        path
        for path in tracked_markdown_paths()
        if not path.startswith(f"{TEST_INFRASTRUCTURE_PACKAGE}/")
    )
    changesets = (*((path,) for path in covered_paths), covered_paths)
    selected_steps = {
        step
        for changeset in changesets
        for step in build_selected_gate_plan(changeset).steps
    }
    lane_runs = run_lanes(markdown_lanes, tmp_path)
    lanes_running_step = {
        step.label: sorted(
            {
                run.lane.label
                for run in lane_runs
                if project_command(step.argv)
                in {project_command(executed) for executed in run.executed}
            }
        )
        for step in selected_steps
    }

    assert markdown_lanes
    assert covered_paths
    assert selected_steps
    assert {
        label: lanes for label, lanes in lanes_running_step.items() if not lanes
    } == {}, (
        "selected gate steps no declared Markdown lane runs; lane commands ran: "
        f"{[(run.command, run.exit_code, str(run.output_path)) for run in lane_runs]}"
    )
