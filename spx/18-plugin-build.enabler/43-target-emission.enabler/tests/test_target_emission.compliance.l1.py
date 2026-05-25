"""Compliance evidence for per-runtime target emission."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.build import (
    CLAUDE_ONLY_FRONTMATTER_FIELDS,
    CLAUDE_SKILL_DIR_TOKEN,
    IMPLEMENTED,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
    Target,
    build,
    rewrite_paths_for_target,
    strip_frontmatter_fields,
)
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
SKILL_NAME = "example-skill"
COMMAND_NAME = "example-command"
CLAUDE_ONLY_FIELD = CLAUDE_ONLY_FRONTMATTER_FIELDS[0]
SKILL_RELATIVE_PATH = "references/guide.md"
CLAUDE_SKILL_REFERENCE = f"{CLAUDE_SKILL_DIR_TOKEN}/{SKILL_RELATIVE_PATH}"
SOURCE_SKILL = (
    "---\n"
    "name: example-skill\n"
    "description: Example skill.\n"
    f"{CLAUDE_ONLY_FIELD}: Read\n"
    "---\n"
    "\n"
    f"Read `{CLAUDE_SKILL_REFERENCE}`.\n"
)
SOURCE_COMMAND = "---\ndescription: Example command.\n---\n\nCommand body.\n"
FRONTMATTER_WITH_ALL_CLAUDE_FIELDS = (
    "---\n"
    "name: sample\n"
    "allowed-tools: Read\n"
    "disable-model-invocation: true\n"
    "argument-hint: [path]\n"
    "description: Keep me.\n"
    "---\n"
    "\n"
    "Body.\n"
)


def test_every_source_file_emits_to_both_runtime_trees(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(
        PLUGIN_NAME,
        skills={SKILL_NAME: SOURCE_SKILL},
        commands={COMMAND_NAME: SOURCE_COMMAND},
    )

    build(builder.src_root, tmp_path / "dist")

    reader = DistTreeReader(tmp_path)
    for target in Target:
        files = reader.list_all_files(target)
        assert (
            Path(PLUGIN_NAME, SKILLS_SUBDIR_NAME, SKILL_NAME, SKILL_FILENAME) in files
        )
        assert Path(PLUGIN_NAME, "commands", f"{COMMAND_NAME}.md") in files


def test_runtime_trees_mirror_source_structure(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SOURCE_SKILL})

    build(builder.src_root, tmp_path / "dist")

    reader = DistTreeReader(tmp_path)
    assert reader.list_plugins(Target.CLAUDE) == (PLUGIN_NAME,)
    assert reader.list_plugins(Target.CODEX) == (PLUGIN_NAME,)
    assert reader.list_skills(PLUGIN_NAME, target=Target.CLAUDE) == (SKILL_NAME,)
    assert reader.list_skills(PLUGIN_NAME, target=Target.CODEX) == (SKILL_NAME,)


def test_claude_output_preserves_skill_dir_token(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SOURCE_SKILL})

    build(builder.src_root, tmp_path / "dist")

    body = DistTreeReader(tmp_path).read_skill_body(
        PLUGIN_NAME,
        SKILL_NAME,
        target=Target.CLAUDE,
    )
    assert CLAUDE_SKILL_REFERENCE in body


def test_codex_output_rewrites_skill_dir_token_to_relative_path(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SOURCE_SKILL})

    build(builder.src_root, tmp_path / "dist")

    body = DistTreeReader(tmp_path).read_skill_body(
        PLUGIN_NAME,
        SKILL_NAME,
        target=Target.CODEX,
    )
    assert CLAUDE_SKILL_DIR_TOKEN not in body
    assert SKILL_RELATIVE_PATH in body


def test_codex_skill_frontmatter_strips_claude_only_fields(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(
        PLUGIN_NAME, skills={SKILL_NAME: FRONTMATTER_WITH_ALL_CLAUDE_FIELDS}
    )

    build(builder.src_root, tmp_path / "dist")

    codex_body = DistTreeReader(tmp_path).read_skill_body(
        PLUGIN_NAME,
        SKILL_NAME,
        target=Target.CODEX,
    )
    claude_body = DistTreeReader(tmp_path).read_skill_body(
        PLUGIN_NAME,
        SKILL_NAME,
        target=Target.CLAUDE,
    )
    for field in CLAUDE_ONLY_FRONTMATTER_FIELDS:
        assert f"{field}:" in claude_body
        assert f"{field}:" not in codex_body
    assert "description: Keep me." in codex_body


def test_path_rewrite_is_idempotent() -> None:
    once = rewrite_paths_for_target(CLAUDE_SKILL_REFERENCE, target=Target.CODEX)
    twice = rewrite_paths_for_target(once, target=Target.CODEX)

    assert once == twice


def test_frontmatter_strip_is_idempotent() -> None:
    once = strip_frontmatter_fields(
        FRONTMATTER_WITH_ALL_CLAUDE_FIELDS,
        fields=CLAUDE_ONLY_FRONTMATTER_FIELDS,
    )
    twice = strip_frontmatter_fields(once, fields=CLAUDE_ONLY_FRONTMATTER_FIELDS)

    assert once == twice


def test_outputs_do_not_contain_runtime_cat_injection(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SOURCE_SKILL})

    build(builder.src_root, tmp_path / "dist")

    reader = DistTreeReader(tmp_path)
    for target in Target:
        for relative_path in reader.list_all_files(target):
            body = (reader.runtime_root(target) / relative_path).read_text(
                encoding="utf-8"
            )
            assert "!`cat" not in body
