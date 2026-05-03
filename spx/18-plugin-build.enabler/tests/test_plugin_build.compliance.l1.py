"""Compliance tests for plugin-build parent enabler.

Verifies the cross-cutting traceability assertion:
every committed file under dist/ traces to a src/ ancestor through the build.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

_build_plugins = pytest.importorskip(
    "outcomeeng.scripts.build_plugins",
    reason="18-plugin-build.enabler is in spx/EXCLUDE pending implementation",
)
Target = _build_plugins.Target
build = _build_plugins.build

PLUGIN_NAME = "samplelang"
SKILL_NAME = "coding-samplelang"
SKILL_BODY = "# Coding Samplelang\n\nBody."

PLUGINS_SUBDIR = "plugins"
SKILLS_SUBDIR = "skills"
SKILL_FILENAME = "SKILL.md"
DIST_SUBDIR = "dist"


class TestDistTraceability:
    """ALWAYS: every committed file under dist/ traces to a src/ ancestor through the build."""

    def test_every_dist_file_path_corresponds_to_a_src_plugin_path(
        self, tmp_path: Path
    ) -> None:
        builder = SrcTreeBuilder(tmp_path)
        builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SKILL_BODY})

        dist_root = tmp_path / DIST_SUBDIR
        build(builder.src_root, dist_root)

        src_plugins_root = builder.src_root / PLUGINS_SUBDIR
        src_plugin_relative_paths = {
            f.relative_to(src_plugins_root)
            for f in src_plugins_root.rglob("*")
            if f.is_file()
        }

        for dist_file in dist_root.rglob("*"):
            if not dist_file.is_file():
                continue
            relative = dist_file.relative_to(dist_root)
            target_segment = relative.parts[0]
            assert target_segment in {Target.CLAUDE.value, Target.CODEX.value}, (
                f"dist file {dist_file} lives outside any runtime tree"
            )
            without_runtime = Path(*relative.parts[1:])
            assert without_runtime in src_plugin_relative_paths, (
                f"dist file {relative} has no corresponding src/plugins/ ancestor"
            )
