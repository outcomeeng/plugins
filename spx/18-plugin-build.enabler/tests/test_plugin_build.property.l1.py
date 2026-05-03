"""Property tests for plugin-build parent enabler.

Verifies build determinism and idempotence using Hypothesis-generated
src/ tree configurations.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import given, settings

from outcomeeng_testing.generators.source_tree import (
    SrcTreeConfig,
    materialize,
    src_tree_configs,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

_build_plugins = pytest.importorskip(
    "outcomeeng.scripts.build_plugins",
    reason="18-plugin-build.enabler is in spx/EXCLUDE pending implementation",
)
build = _build_plugins.build

DIST_SUBDIR = "dist"
SRC_SUBDIR = "src"

MAX_EXAMPLES = 20
DEADLINE_MS = 4000

settings_for_filesystem_property = settings(
    max_examples=MAX_EXAMPLES, deadline=DEADLINE_MS
)


def _read_all_files(root: Path) -> dict[str, bytes]:
    """Return a {relative_path: content_bytes} mapping for every file under root."""
    return {
        str(f.relative_to(root)): f.read_bytes() for f in root.rglob("*") if f.is_file()
    }


class TestBuildDeterminism:
    """PROPERTY: same src/ content always produces byte-identical dist/ outputs."""

    @given(src_tree_configs())
    @settings_for_filesystem_property
    def test_two_builds_of_the_same_input_produce_identical_output(
        self, config: SrcTreeConfig
    ) -> None:
        with TemporaryDirectory() as tmp_left, TemporaryDirectory() as tmp_right:
            left_root = Path(tmp_left)
            right_root = Path(tmp_right)

            materialize(config, SrcTreeBuilder(left_root))
            materialize(config, SrcTreeBuilder(right_root))

            left_dist = left_root / DIST_SUBDIR
            right_dist = right_root / DIST_SUBDIR
            build(left_root / SRC_SUBDIR, left_dist)
            build(right_root / SRC_SUBDIR, right_dist)

            assert _read_all_files(left_dist) == _read_all_files(right_dist)


class TestBuildIdempotence:
    """PROPERTY: running the build twice in succession produces no changes on the second run."""

    @given(src_tree_configs())
    @settings_for_filesystem_property
    def test_second_build_run_does_not_change_dist(self, config: SrcTreeConfig) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(config, SrcTreeBuilder(root))

            dist_root = root / DIST_SUBDIR
            build(root / SRC_SUBDIR, dist_root)
            first_pass = _read_all_files(dist_root)

            build(root / SRC_SUBDIR, dist_root)
            second_pass = _read_all_files(dist_root)

            assert first_pass == second_pass
