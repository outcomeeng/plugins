"""Conformance evidence over the shipped runtime producer corpus."""

from pathlib import Path

from outcomeeng_testing.evals.producer_prompt import (
    PRODUCER_RELATIVE_PATHS,
    PRODUCER_SOURCE_PATHS,
    materialize_runtime_files,
)
from outcomeeng_testing.harnesses.eval_workspaces import with_temp_workspace


@with_temp_workspace
def test_whole_file_materialization_uses_shipped_runtime_producers(
    tmp_path: Path,
) -> None:
    observations = materialize_runtime_files(tmp_path)

    assert PRODUCER_SOURCE_PATHS
    assert len(observations) == len(PRODUCER_SOURCE_PATHS)
    assert tuple(observation.case.relative_path for observation in observations) == (
        PRODUCER_RELATIVE_PATHS
    )
    for observation in observations:
        assert observation.producer_text in observation.prompt_text
        assert observation.case.relative_path in observation.prompt_text
