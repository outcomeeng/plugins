"""Mapping evidence for producer-prompt CLI modes."""

import os
from pathlib import Path

from outcomeeng_testing.evals.producer_prompt import (
    PROMPT_FILENAME,
    cli_materialization_observation,
    nested_cli_results,
)
from outcomeeng_testing.harnesses.eval_workspaces import with_temp_workspace


@with_temp_workspace
def test_cli_write_and_check_modes_map_to_prompt_state(tmp_path: Path) -> None:
    observation = cli_materialization_observation(tmp_path)

    assert observation.write_result.exit_code == os.EX_OK
    assert PROMPT_FILENAME in observation.write_result.output
    assert observation.check_result.exit_code == os.EX_OK
    assert observation.stale_result.exit_code != os.EX_OK
    assert PROMPT_FILENAME in observation.stale_result.output
    assert (
        observation.prompt_path.read_text(encoding="utf-8") == observation.stale_prompt
    )
    assert observation.prompt_path.stat().st_mtime_ns == observation.stale_mtime_ns


@with_temp_workspace
def test_cli_eval_root_maps_to_nested_definitions(tmp_path: Path) -> None:
    write_result, check_result, workspace = nested_cli_results(tmp_path)

    assert write_result.exit_code == os.EX_OK
    assert check_result.exit_code == os.EX_OK
    assert str(workspace.prompt_path) in write_result.output
    assert str(workspace.prompt_path) in check_result.output
