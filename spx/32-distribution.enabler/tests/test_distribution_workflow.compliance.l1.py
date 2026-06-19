"""Compliance evidence for the distribution workflow contract."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Final, cast

# PyYAML ships without inline types; this test casts parsed workflow structure below.
import yaml  # type: ignore[import-untyped]

from outcomeeng.distribution.contracts import DIST_DIR_NAME
from outcomeeng.distribution.build import PLUGINS_DIR_NAME
from outcomeeng.distribution.distribute import CLAUDE_DIST_RELATIVE

REPO_ROOT: Final = Path(__file__).resolve().parents[3]
DISTRIBUTE_WORKFLOW: Final = (
    REPO_ROOT / ".github" / "workflows" / "distribute-skills.yml"
)
PROJECT_METADATA: Final = REPO_ROOT / "pyproject.toml"
SOURCE_PLUGINS_PATH: Final = f"src/{PLUGINS_DIR_NAME}/**"


def _workflow() -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        yaml.load(DISTRIBUTE_WORKFLOW.read_text(), Loader=yaml.BaseLoader),
    )


def _push_paths(workflow: dict[str, Any]) -> set[str]:
    on_section = workflow["on"]
    return set(cast("list[str]", on_section["push"]["paths"]))


def _distribution_python_version(workflow: dict[str, Any]) -> str:
    setup_step = next(
        step
        for step in workflow["jobs"]["distribute"]["steps"]
        if step.get("name") == "Set up Python"
    )
    return cast("str", setup_step["with"]["python-version"])


def _requires_python_version() -> str:
    metadata = tomllib.loads(PROJECT_METADATA.read_text())
    requires_python = cast("str", metadata["project"]["requires-python"])
    return requires_python.removeprefix(">=")


def test_distribution_workflow_triggers_from_runtime_and_source_paths() -> None:
    paths = _push_paths(_workflow())

    assert f"{CLAUDE_DIST_RELATIVE}/**" in paths
    assert SOURCE_PLUGINS_PATH in paths
    assert not any(path.startswith(f"{PLUGINS_DIR_NAME}/") for path in paths)
    assert f"{DIST_DIR_NAME}/codex/**" not in paths


def test_distribution_workflow_python_matches_project_metadata() -> None:
    workflow_version = _distribution_python_version(_workflow())

    assert workflow_version == _requires_python_version()
