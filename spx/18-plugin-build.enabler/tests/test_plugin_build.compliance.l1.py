"""Compliance evidence for whole-pipeline build traceability."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.build import IMPLEMENTED, PLUGINS_DIR_NAME, build
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder


@pytest.fixture(autouse=True)
def _require_module_implemented() -> None:
    if not IMPLEMENTED:
        pytest.fail(
            "outcomeeng.distribution.build is a stub; implement it before "
            "running this test, or filter via `spx test passing` "
            "(node is listed in spx/EXCLUDE)"
        )


PLUGIN_NAME = "sample"
SKILL_NAME = "example"
SOURCE_SKILL = "---\nname: example\n---\n\nBody.\n"


def test_dist_files_trace_to_source_ancestor(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SOURCE_SKILL})

    build(builder.src_root, tmp_path / "dist")

    reader = DistTreeReader(tmp_path)
    for target in Target:
        for relative_path in reader.list_all_files(target):
            source_path = builder.src_root / PLUGINS_DIR_NAME / relative_path
            assert source_path.is_file()
