"""Mapping evidence for producer-prompt CLI modes."""

import os

from outcomeeng_testing.evals.producer_prompt import (
    CliMaterializationObservation,
    NestedCliObservation,
    PROMPT_FILENAME,
    run_cli_materialization_mapping,
    run_nested_cli_mapping,
)


def test_cli_write_and_check_modes_map_to_prompt_state() -> None:
    def predicate(observation: CliMaterializationObservation) -> None:
        assert observation.write_result.exit_code == os.EX_OK
        assert PROMPT_FILENAME in observation.write_result.output
        assert observation.check_result.exit_code == os.EX_OK
        assert observation.stale_result.exit_code != os.EX_OK
        assert PROMPT_FILENAME in observation.stale_result.output
        assert (
            observation.prompt_path.read_text(encoding="utf-8")
            == observation.stale_prompt
        )
        assert observation.prompt_path.stat().st_mtime_ns == observation.stale_mtime_ns

    run_cli_materialization_mapping(predicate)


def test_cli_eval_root_maps_to_nested_definitions() -> None:
    def predicate(observation: NestedCliObservation) -> None:
        assert observation.write_result.exit_code == os.EX_OK
        assert observation.check_result.exit_code == os.EX_OK
        assert str(observation.prompt_path) in observation.write_result.output
        assert str(observation.prompt_path) in observation.check_result.output

    run_nested_cli_mapping(predicate)
