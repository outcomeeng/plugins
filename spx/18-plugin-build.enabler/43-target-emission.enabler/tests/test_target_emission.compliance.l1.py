"""Compliance tests for target-emission enabler.

Each test class verifies one ALWAYS/NEVER assertion from
spx/18-plugin-build.enabler/43-target-emission.enabler/target-emission.md.
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
COMMAND_NAME = "build"

DIST_SUBDIR = "dist"
SKILLS_SUBDIR = "skills"
COMMANDS_SUBDIR = "commands"
SKILL_FILENAME = "SKILL.md"
COMMAND_FILE_SUFFIX = ".md"

CLAUDE_SKILL_DIR_REFERENCE = "${CLAUDE_SKILL_DIR}/references/foo.md"
RELATIVE_REFERENCE_FRAGMENT = "references/foo.md"

PLAIN_SKILL_BODY = "# Coding Samplelang\n\nPlain skill body."
SKILL_BODY_WITH_PATH = (
    f"# Coding Samplelang\n\nSee {CLAUDE_SKILL_DIR_REFERENCE} for details."
)
SKILL_BODY_WITH_FRONTMATTER = (
    f"---\nname: {SKILL_NAME}\nallowed-tools: Read, Write\n---\n\n# Body."
)
SKILL_BODY_WITH_REQUIRE_DIRECTIVE = (
    "{!% require_skill 'develop:standardizing-skills' %!}\n\n"
    "# Coding Samplelang\n\nBody."
)
COMMAND_BODY = "# Build command\n\nInvokes the build."


def _claude_skill_path(dist_root: Path) -> Path:
    return (
        dist_root
        / Target.CLAUDE.value
        / PLUGIN_NAME
        / SKILLS_SUBDIR
        / SKILL_NAME
        / SKILL_FILENAME
    )


def _codex_skill_path(dist_root: Path) -> Path:
    return (
        dist_root
        / Target.CODEX.value
        / PLUGIN_NAME
        / SKILLS_SUBDIR
        / SKILL_NAME
        / SKILL_FILENAME
    )


class TestCoverageMapping:
    """ALWAYS: every src plugin source file produces exactly one output in each runtime tree."""

    def test_each_skill_produces_claude_and_codex_outputs(self, tmp_path: Path) -> None:
        builder = SrcTreeBuilder(tmp_path)
        builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: PLAIN_SKILL_BODY})

        dist_root = tmp_path / DIST_SUBDIR
        build(builder.src_root, dist_root)

        assert _claude_skill_path(dist_root).is_file()
        assert _codex_skill_path(dist_root).is_file()

    def test_command_produces_outputs_in_both_runtime_trees(
        self, tmp_path: Path
    ) -> None:
        builder = SrcTreeBuilder(tmp_path)
        builder.add_plugin(PLUGIN_NAME, commands={COMMAND_NAME: COMMAND_BODY})

        dist_root = tmp_path / DIST_SUBDIR
        build(builder.src_root, dist_root)

        for target in (Target.CLAUDE, Target.CODEX):
            command_output = (
                dist_root
                / target.value
                / PLUGIN_NAME
                / COMMANDS_SUBDIR
                / f"{COMMAND_NAME}{COMMAND_FILE_SUFFIX}"
            )
            assert command_output.is_file()


class TestSubtreeMirroring:
    """ALWAYS: dist/<runtime>/<plugin>/ mirrors src/plugins/<plugin>/ structure."""

    def test_runtime_subtree_mirrors_source_subtree(self, tmp_path: Path) -> None:
        builder = SrcTreeBuilder(tmp_path)
        builder.add_plugin(
            PLUGIN_NAME,
            skills={SKILL_NAME: PLAIN_SKILL_BODY},
            commands={COMMAND_NAME: COMMAND_BODY},
        )

        dist_root = tmp_path / DIST_SUBDIR
        build(builder.src_root, dist_root)

        for target in (Target.CLAUDE, Target.CODEX):
            runtime_root = dist_root / target.value / PLUGIN_NAME
            assert (
                runtime_root / SKILLS_SUBDIR / SKILL_NAME / SKILL_FILENAME
            ).is_file()
            assert (
                runtime_root / COMMANDS_SUBDIR / f"{COMMAND_NAME}{COMMAND_FILE_SUFFIX}"
            ).is_file()


class TestClaudeSkillDirPreservation:
    """ALWAYS: ${CLAUDE_SKILL_DIR}/... paths preserved verbatim in dist/claude/ output."""

    def test_claude_output_preserves_claude_skill_dir(self, tmp_path: Path) -> None:
        builder = SrcTreeBuilder(tmp_path)
        builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SKILL_BODY_WITH_PATH})

        dist_root = tmp_path / DIST_SUBDIR
        build(builder.src_root, dist_root)

        claude_content = _claude_skill_path(dist_root).read_text()
        assert CLAUDE_SKILL_DIR_REFERENCE in claude_content


class TestCodexSkillDirRewrite:
    """ALWAYS: ${CLAUDE_SKILL_DIR}/... paths rewritten to relative paths in dist/codex/ output."""

    def test_codex_output_rewrites_claude_skill_dir(self, tmp_path: Path) -> None:
        builder = SrcTreeBuilder(tmp_path)
        builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SKILL_BODY_WITH_PATH})

        dist_root = tmp_path / DIST_SUBDIR
        build(builder.src_root, dist_root)

        codex_content = _codex_skill_path(dist_root).read_text()
        assert "${CLAUDE_SKILL_DIR}" not in codex_content
        assert RELATIVE_REFERENCE_FRAGMENT in codex_content


class TestClaudeFrontmatterPreserved:
    """ALWAYS: Claude-only frontmatter appears in dist/claude/, absent from dist/codex/."""

    def test_allowed_tools_present_in_claude_output(self, tmp_path: Path) -> None:
        builder = SrcTreeBuilder(tmp_path)
        builder.add_plugin(
            PLUGIN_NAME, skills={SKILL_NAME: SKILL_BODY_WITH_FRONTMATTER}
        )

        dist_root = tmp_path / DIST_SUBDIR
        build(builder.src_root, dist_root)

        claude_content = _claude_skill_path(dist_root).read_text()
        assert "allowed-tools" in claude_content

    def test_allowed_tools_absent_from_codex_output(self, tmp_path: Path) -> None:
        builder = SrcTreeBuilder(tmp_path)
        builder.add_plugin(
            PLUGIN_NAME, skills={SKILL_NAME: SKILL_BODY_WITH_FRONTMATTER}
        )

        dist_root = tmp_path / DIST_SUBDIR
        build(builder.src_root, dist_root)

        codex_content = _codex_skill_path(dist_root).read_text()
        assert "allowed-tools" not in codex_content


class TestNoRuntimeInjection:
    """NEVER: built output contains runtime-injection syntax inlining sister-skill content."""

    def test_built_output_contains_no_cat_skill_injection(self, tmp_path: Path) -> None:
        builder = SrcTreeBuilder(tmp_path)
        builder.add_plugin(
            PLUGIN_NAME, skills={SKILL_NAME: SKILL_BODY_WITH_REQUIRE_DIRECTIVE}
        )

        dist_root = tmp_path / DIST_SUBDIR
        build(builder.src_root, dist_root)

        for target in (Target.CLAUDE, Target.CODEX):
            output = (
                dist_root
                / target.value
                / PLUGIN_NAME
                / SKILLS_SUBDIR
                / SKILL_NAME
                / SKILL_FILENAME
            ).read_text()
            assert "!`cat" not in output


class TestNoClaudeSkillDirInCodex:
    """NEVER: dist/codex/ output references ${CLAUDE_SKILL_DIR}."""

    def test_codex_output_does_not_reference_claude_skill_dir(
        self, tmp_path: Path
    ) -> None:
        builder = SrcTreeBuilder(tmp_path)
        builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SKILL_BODY_WITH_PATH})

        dist_root = tmp_path / DIST_SUBDIR
        build(builder.src_root, dist_root)

        codex_content = _codex_skill_path(dist_root).read_text()
        assert "${CLAUDE_SKILL_DIR}" not in codex_content
        assert "CLAUDE_SKILL_DIR" not in codex_content
