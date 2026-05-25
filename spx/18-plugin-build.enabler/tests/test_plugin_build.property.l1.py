"""Property evidence for build determinism and idempotence."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.build import IMPLEMENTED, build
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


def test_same_source_produces_byte_identical_outputs(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    for root in (first_root, second_root):
        builder = SrcTreeBuilder(root)
        builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SOURCE_SKILL})
        build(builder.src_root, root / "dist")

    assert _snapshot(first_root / "dist") == _snapshot(second_root / "dist")


def test_running_build_twice_produces_no_second_pass_change(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SOURCE_SKILL})

    build(builder.src_root, tmp_path / "dist")
    first = _snapshot(tmp_path / "dist")
    build(builder.src_root, tmp_path / "dist")

    assert _snapshot(tmp_path / "dist") == first


def _snapshot(root: Path) -> tuple[tuple[str, bytes], ...]:
    return tuple(
        sorted(
            (str(path.relative_to(root)), path.read_bytes())
            for path in root.rglob("*")
            if path.is_file()
        )
    )
