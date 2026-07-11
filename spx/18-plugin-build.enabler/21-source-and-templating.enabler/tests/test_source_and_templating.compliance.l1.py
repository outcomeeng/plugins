"""Compliance evidence for source-tree and template directive contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.build import (
    BLOCK_DELIMITER_END,
    BLOCK_DELIMITER_START,
    CLAUDE_SKILL_DIR_TOKEN,
    COMMENT_DELIMITER_END,
    COMMENT_DELIMITER_START,
    IMPLEMENTED,
    PLUGINS_DIR_NAME,
    REQUIRE_SKILL_TEXT_TEMPLATE,
    SHARED_FRAGMENT_FILENAME,
    SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
    VARIABLE_DELIMITER_END,
    VARIABLE_DELIMITER_START,
    IncludeDirective,
    RequireSkillDirective,
    SourceFormatError,
    build,
    emit_skill,
    expand_require_skill,
    format_directive,
    make_jinja_environment,
    render_text,
)
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader
from outcomeeng_testing.harnesses.runtime_parameterization import (
    PLUGIN_NAME,
    SKILL_STANDARDS_REF,
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


SKILL_NAME = "create-skills"
FRAGMENT_TOPIC = "skill-standards"
FRAGMENT_BODY = "Shared standards body."
MISSING_FRAGMENT_BODY = "No fragment exists here."
SKILL_BODY = "---\nname: create-skills\n---\n\nBody"
STANDARD_JINJA_TEXT = "{% if standard %}unchanged{{ standard }}{% endif %}"


def test_build_accepts_well_formed_src_tree(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SKILL_BODY})
    builder.add_shared_topic(PLUGIN_NAME, FRAGMENT_TOPIC, FRAGMENT_BODY)

    build(builder.src_root, tmp_path / "dist")


def test_build_ignores_ordinary_files_under_plugin_root(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SKILL_BODY})
    builder.add_shared_topic(PLUGIN_NAME, FRAGMENT_TOPIC, FRAGMENT_BODY)
    dist_root = tmp_path / "dist"
    (builder.src_root / PLUGINS_DIR_NAME / PLUGIN_NAME / ".DS_Store").write_text(
        "ignored by git",
        encoding="utf-8",
    )

    build(builder.src_root, dist_root)

    reader = DistTreeReader(tmp_path)
    for target in Target:
        assert Path(PLUGIN_NAME) / ".DS_Store" not in reader.list_all_files(target)


def test_build_rejects_shared_topic_without_fragment(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: SKILL_BODY})
    topic_root = builder.shared_root / PLUGIN_NAME / FRAGMENT_TOPIC
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
    builder.add_shared_topic(PLUGIN_NAME, FRAGMENT_TOPIC, FRAGMENT_BODY)

    rendered = render_text(STANDARD_JINJA_TEXT, shared_root=builder.shared_root)

    assert rendered == STANDARD_JINJA_TEXT


def test_require_skill_expands_to_coding_agent_neutral_guidance() -> None:
    rendered = expand_require_skill(RequireSkillDirective(SKILL_STANDARDS_REF))

    assert rendered == REQUIRE_SKILL_TEXT_TEMPLATE.format(skill_ref=SKILL_STANDARDS_REF)
    assert SKILL_STANDARDS_REF in rendered


def test_require_skill_renders_inline(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_shared_topic(PLUGIN_NAME, FRAGMENT_TOPIC, FRAGMENT_BODY)
    directive = f"{BLOCK_DELIMITER_START} require_skill '{SKILL_STANDARDS_REF}' {BLOCK_DELIMITER_END}"

    rendered = render_text(directive, shared_root=builder.shared_root)

    assert SKILL_STANDARDS_REF in rendered
    assert directive not in rendered


def test_bare_conditional_block_renders_per_target(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_shared_topic(PLUGIN_NAME, FRAGMENT_TOPIC, FRAGMENT_BODY)
    # A conditional block with no {{! !}} variable token must still be evaluated,
    # not shipped verbatim.
    template = (
        f"{BLOCK_DELIMITER_START} if target == 'claude' {BLOCK_DELIMITER_END}"
        "claude-only"
        f"{BLOCK_DELIMITER_START} else {BLOCK_DELIMITER_END}"
        "codex-only"
        f"{BLOCK_DELIMITER_START} endif {BLOCK_DELIMITER_END}"
    )

    claude = render_text(
        template, shared_root=builder.shared_root, variables={"target": "claude"}
    )
    codex = render_text(
        template, shared_root=builder.shared_root, variables={"target": "codex"}
    )

    assert claude == "claude-only"
    assert codex == "codex-only"
    assert BLOCK_DELIMITER_START not in claude
    assert BLOCK_DELIMITER_START not in codex


def test_skill_dir_escape_survives_jinja_pass(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    # A skill body carrying BOTH a Jinja control block (which triggers the Jinja
    # pass) AND the skill-directory rewrite escape. The escape shares Jinja's
    # comment syntax, so it must be protected across the render and survive.
    escaped_line = (
        f"Write `{CLAUDE_SKILL_DIR_TOKEN}/x.md` {SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE}"
    )
    body = (
        "---\nname: create-skills\n---\n\n"
        f"{BLOCK_DELIMITER_START} if target == 'claude' {BLOCK_DELIMITER_END}"
        "c"
        f"{BLOCK_DELIMITER_START} endif {BLOCK_DELIMITER_END}\n"
        f"{escaped_line}\n"
    )
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: body})

    build(builder.src_root, tmp_path / "dist")

    reader = DistTreeReader(tmp_path)
    for target in Target:
        rendered = reader.read_skill_body(PLUGIN_NAME, SKILL_NAME, target=target)
        # The escape directive is consumed, and its CLAUDE_SKILL_DIR token is
        # preserved verbatim in both targets rather than stripped by the Jinja pass.
        assert CLAUDE_SKILL_DIR_TOKEN in rendered
        assert SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE not in rendered


def test_require_skill_expands_identically_across_targets(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    require_directive = format_directive(RequireSkillDirective(SKILL_STANDARDS_REF))
    skill_body = (
        f"---\nname: {SKILL_NAME}\n---\n\nBefore.\n{require_directive}\nAfter.\n"
    )
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: skill_body})
    src_path = (
        builder.src_root
        / PLUGINS_DIR_NAME
        / PLUGIN_NAME
        / SKILLS_SUBDIR_NAME
        / SKILL_NAME
        / SKILL_FILENAME
    )
    dist_root = tmp_path / "dist"

    emitted: dict[Target, str] = {}
    for target in Target:
        emit_skill(
            src_path,
            target=target,
            dist_root=dist_root,
            shared_root=builder.shared_root,
        )
        destination = (
            dist_root
            / target.value
            / PLUGIN_NAME
            / SKILLS_SUBDIR_NAME
            / SKILL_NAME
            / SKILL_FILENAME
        )
        emitted[target] = destination.read_text(encoding="utf-8")

    # Direct two-target byte comparison through the real emit pipeline: the
    # require_skill directive carries no ${CLAUDE_SKILL_DIR} token and no
    # Claude-only frontmatter, so both targets emit byte-identical files. The
    # comparison is against emit_skill's own output, not a test re-assembly of
    # its translation sequence.
    assert emitted[Target.CLAUDE] == emitted[Target.CODEX]
    assert SKILL_STANDARDS_REF in emitted[Target.CLAUDE]
    assert require_directive not in emitted[Target.CLAUDE]


def test_include_directive_uses_fragment_file_contract(tmp_path: Path) -> None:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_shared_topic(PLUGIN_NAME, FRAGMENT_TOPIC, FRAGMENT_BODY)
    include = IncludeDirective(
        f"{PLUGIN_NAME}/{FRAGMENT_TOPIC}/{SHARED_FRAGMENT_FILENAME}"
    )

    rendered = render_text(
        f"{BLOCK_DELIMITER_START} include '{include.path}' {BLOCK_DELIMITER_END}",
        shared_root=builder.shared_root,
    )

    assert rendered == FRAGMENT_BODY
