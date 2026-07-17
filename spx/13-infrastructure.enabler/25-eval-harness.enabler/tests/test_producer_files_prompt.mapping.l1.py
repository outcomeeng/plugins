"""Mapping evidence over the shipped runtime producer corpus."""

from pathlib import Path

from outcomeeng.distribution.contracts import (
    DIST_DIR_NAME,
    PLUGINS_DIR_NAME,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
)
from outcomeeng_testing.evals.producer_prompt import (
    PROJECT_ROOT,
    materialize_runtime_files,
)
from outcomeeng_testing.harnesses.eval_workspaces import with_temp_workspace


@with_temp_workspace
def test_whole_file_materialization_uses_shipped_runtime_producers(
    tmp_path: Path,
) -> None:
    observations = materialize_runtime_files(tmp_path)

    assert tuple(observation.case.relative_path for observation in observations) == (
        tuple(
            sorted(
                (
                    Path(DIST_DIR_NAME)
                    / target.value
                    / source_path.relative_to(
                        PROJECT_ROOT / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME
                    )
                ).as_posix()
                for target in Target
                for source_path in (
                    PROJECT_ROOT / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME
                ).glob(f"*/{SKILLS_SUBDIR_NAME}/audit*tests/{SKILL_FILENAME}")
            )
        )
    )
    for observation in observations:
        assert observation.producer_text in observation.prompt_text
        assert observation.case.relative_path in observation.prompt_text
