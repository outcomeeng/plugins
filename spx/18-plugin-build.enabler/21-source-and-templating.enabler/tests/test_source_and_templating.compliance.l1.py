"""Compliance evidence for source-tree and template directive contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.build import (
    BLOCK_DELIMITER_END,
    BLOCK_DELIMITER_START,
    COMMENT_DELIMITER_END,
    COMMENT_DELIMITER_START,
    IMPLEMENTED,
    REQUIRE_SKILL_TEXT_TEMPLATE,
    SHARED_FRAGMENT_FILENAME,
    VARIABLE_DELIMITER_END,
    VARIABLE_DELIMITER_START,
    IncludeDirective,
    RequireSkillDirective,
    SourceFormatError,
    build,
    expand_require_skill,
    make_jinja_environment,
    render_text,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder


@pytest.fixture(autouse=True)
def _require_module_implemented() -> None:
    if not IMPLEMENTED:
        pytest.fail(
            "outcomeeng.distribution.build is a stub; implement it before "
            "running this test, or filter via `spx test passing` "
            "(node is listed in spx/EXCLUDE)"
        )


SKILL_REF = "develop:standardizing-skills"
PLUGIN_NAME = "develop"
SKILL_NAME = "creating-skills"
FRAGMENT_SCOPE = "develop"
FRAGMENT_TOPIC = "skill-standards"
FRAGMENT_BODY = "Shared standards body."
MISSING_FRAGMENT_BODY = "No fragment exists here."
SKILL_BODY = "---\nname: creating-skills\n---\n\nBody"
STANDARD_JINJA_TEXT = "{% if standard %}unchanged{{ standard }}{% endif %}"


def test_build_accepts_well_formed_src_tree(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SKILL_BODY})
    builder.add_shared_topic(FRAGMENT_SCOPE, FRAGMENT_TOPIC, FRAGMENT_BODY)

    build(builder.src_root, tmp_path / "dist")


def test_build_rejects_shared_topic_without_fragment(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SKILL_BODY})
    topic_root = builder.shared_root / FRAGMENT_SCOPE / FRAGMENT_TOPIC
    topic_root.mkdir(parents=True)
    (topic_root / "notes.md").write_text(MISSING_FRAGMENT_BODY, encoding="utf-8")

    with pytest.raises(SourceFormatError):
        build(builder.src_root, tmp_path / "dist")


def test_jinja_environment_uses_custom_delimiters(tmp_path: Path) -> None:
    environment = make_jinja_environment(tmp_path)

    assert environment.block_start_string == BLOCK_DELIMITER_START
    assert environment.block_end_string == BLOCK_DELIMITER_END
    assert environment.variable_start_string == VARIABLE_DELIMITER_START
    assert environment.variable_end_string == VARIABLE_DELIMITER_END
    assert environment.comment_start_string == COMMENT_DELIMITER_START
    assert environment.comment_end_string == COMMENT_DELIMITER_END


def test_standard_jinja_syntax_passes_through_rendering(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_shared_topic(FRAGMENT_SCOPE, FRAGMENT_TOPIC, FRAGMENT_BODY)

    rendered = render_text(STANDARD_JINJA_TEXT, shared_root=builder.shared_root)

    assert rendered == STANDARD_JINJA_TEXT


def test_require_skill_expands_to_runtime_neutral_guidance() -> None:
    rendered = expand_require_skill(RequireSkillDirective(SKILL_REF))

    assert rendered == REQUIRE_SKILL_TEXT_TEMPLATE.format(skill_ref=SKILL_REF)
    assert SKILL_REF in rendered


def test_require_skill_renders_inline(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_shared_topic(FRAGMENT_SCOPE, FRAGMENT_TOPIC, FRAGMENT_BODY)
    directive = (
        f"{BLOCK_DELIMITER_START} require_skill '{SKILL_REF}' {BLOCK_DELIMITER_END}"
    )

    rendered = render_text(directive, shared_root=builder.shared_root)

    assert SKILL_REF in rendered
    assert directive not in rendered


def test_include_directive_uses_fragment_file_contract(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_shared_topic(FRAGMENT_SCOPE, FRAGMENT_TOPIC, FRAGMENT_BODY)
    include = IncludeDirective(
        f"{FRAGMENT_SCOPE}/{FRAGMENT_TOPIC}/{SHARED_FRAGMENT_FILENAME}"
    )

    rendered = render_text(
        f"{BLOCK_DELIMITER_START} include '{include.path}' {BLOCK_DELIMITER_END}",
        shared_root=builder.shared_root,
    )

    assert rendered == FRAGMENT_BODY
