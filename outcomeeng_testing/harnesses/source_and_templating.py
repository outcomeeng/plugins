"""Spec-derived observations for source-and-templating evidence."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

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
    CyclicIncludeError,
    DirectiveSyntaxError,
    IncludeDirective,
    RequireSkillDirective,
    SourceFormatError,
    build,
    emit_skill,
    expand_require_skill,
    format_directive,
    make_jinja_environment,
    parse_directives,
    render_text,
)
from outcomeeng.distribution.contracts import (
    INSTRUCTIONS_PLUGIN_NAME,
    SKILL_STANDARDS_NAME,
    SKILL_STANDARDS_REF,
    Target,
)
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

_SCOPE = "samplescope"
_INNER_TOPIC = "inner-topic"
_OUTER_TOPIC = "outer-topic"
_SKILL_TOPIC = "skill-topic"
_CYCLE_TOPIC_A = "cycle-topic-a"
_CYCLE_TOPIC_B = "cycle-topic-b"
_INNER_BODY = "Inner fragment body.\nSecond line.\n"
_SKILL_BODY = f"---\nname: {SKILL_STANDARDS_NAME}\n---\n\nBody"
_FRAGMENT_BODY = "Shared standards body."


def implementation_is_ready() -> bool:
    return IMPLEMENTED


def parse_empty_text_has_no_directives() -> bool:
    return parse_directives("") == ()


def parse_plain_prose_has_no_directives() -> bool:
    return parse_directives("# Heading\n\nJust prose, no directives.") == ()


def parse_single_include() -> bool:
    path = _fragment_path(_INNER_TOPIC)
    return parse_directives(format_directive(IncludeDirective(path))) == (
        IncludeDirective(path),
    )


def parse_include_inside_prose() -> bool:
    path = _fragment_path(_INNER_TOPIC)
    directive = format_directive(IncludeDirective(path))
    return parse_directives(f"Before.\n{directive}\nAfter.") == (
        IncludeDirective(path),
    )


def parse_single_require_skill() -> bool:
    directive = RequireSkillDirective(SKILL_STANDARDS_REF)
    return parse_directives(format_directive(directive)) == (directive,)


def parse_mixed_directives_in_source_order() -> bool:
    include = IncludeDirective(_fragment_path(_INNER_TOPIC))
    require = RequireSkillDirective(SKILL_STANDARDS_REF)
    text = f"{format_directive(include)}\n{format_directive(require)}"
    return parse_directives(text) == (include, require)


def parse_reversed_directives_in_source_order() -> bool:
    include = IncludeDirective(_fragment_path(_INNER_TOPIC))
    require = RequireSkillDirective(SKILL_STANDARDS_REF)
    text = f"{format_directive(require)}\n{format_directive(include)}"
    return parse_directives(text) == (require, include)


def standard_jinja_block_has_no_directives() -> bool:
    return parse_directives("Code: {% if user %} ... {% endif %}") == ()


def standard_jinja_variable_has_no_directives() -> bool:
    return parse_directives("Variable: {{ user.name }}") == ()


def unknown_directive_raises() -> bool:
    return _raises_directive_syntax(
        f"{BLOCK_DELIMITER_START} unknown_directive 'arg' {BLOCK_DELIMITER_END}"
    )


def missing_directive_argument_raises() -> bool:
    return _raises_directive_syntax(
        f"{BLOCK_DELIMITER_START} include {BLOCK_DELIMITER_END}"
    )


def custom_jinja_control_has_no_directives() -> bool:
    text = (
        f"{BLOCK_DELIMITER_START} if target == 'codex' {BLOCK_DELIMITER_END}"
        f"body{BLOCK_DELIMITER_START} endif {BLOCK_DELIMITER_END}"
    )
    return parse_directives(text) == ()


def nested_include_expands() -> bool:
    with TemporaryDirectory() as tmp:
        builder = SrcTreeBuilder(Path(tmp))
        builder.add_shared_topic(_SCOPE, _INNER_TOPIC, _INNER_BODY)
        builder.add_shared_topic(_SCOPE, _OUTER_TOPIC, _include_text(_INNER_TOPIC))
        return (
            render_text(_include_text(_OUTER_TOPIC), shared_root=builder.shared_root)
            == _INNER_BODY
        )


def nested_require_skill_expands() -> bool:
    with TemporaryDirectory() as tmp:
        builder = SrcTreeBuilder(Path(tmp))
        directive = format_directive(RequireSkillDirective(SKILL_STANDARDS_REF))
        builder.add_shared_topic(_SCOPE, _SKILL_TOPIC, directive)
        result = render_text(
            _include_text(_SKILL_TOPIC), shared_root=builder.shared_root
        )
        return (
            result == expand_require_skill(RequireSkillDirective(SKILL_STANDARDS_REF))
            and directive not in result
        )


def cyclic_includes_raise() -> bool:
    with TemporaryDirectory() as tmp:
        builder = SrcTreeBuilder(Path(tmp))
        builder.add_shared_topic(_SCOPE, _CYCLE_TOPIC_A, _include_text(_CYCLE_TOPIC_B))
        builder.add_shared_topic(_SCOPE, _CYCLE_TOPIC_B, _include_text(_CYCLE_TOPIC_A))
        try:
            render_text(_include_text(_CYCLE_TOPIC_A), shared_root=builder.shared_root)
        except CyclicIncludeError:
            return True
        return False


def bound_target_variable_renders_each_target() -> bool:
    template = f"target is {VARIABLE_DELIMITER_START} target {VARIABLE_DELIMITER_END}"
    return all(
        render_text(template, variables={"target": target.value})
        == f"target is {target.value}"
        for target in Target
    )


def well_formed_source_tree_builds() -> bool:
    with TemporaryDirectory() as tmp:
        builder = _source_tree(Path(tmp))
        build(builder.src_root, Path(tmp) / "dist")
        return True


def ordinary_plugin_root_file_is_ignored() -> bool:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        builder = _source_tree(root)
        (
            builder.src_root / PLUGINS_DIR_NAME / INSTRUCTIONS_PLUGIN_NAME / ".DS_Store"
        ).write_text("ignored by git", encoding="utf-8")
        build(builder.src_root, root / "dist")
        reader = DistTreeReader(root)
        return all(
            Path(INSTRUCTIONS_PLUGIN_NAME) / ".DS_Store"
            not in reader.list_all_files(target)
            for target in Target
        )


def shared_topic_without_fragment_is_rejected() -> bool:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        builder = SrcTreeBuilder(root)
        builder.add_plugin(
            INSTRUCTIONS_PLUGIN_NAME,
            skills={SKILL_STANDARDS_NAME: _SKILL_BODY},
        )
        topic = builder.shared_root / INSTRUCTIONS_PLUGIN_NAME / SKILL_STANDARDS_NAME
        topic.mkdir(parents=True)
        (topic / "notes.md").write_text("No fragment exists here.", encoding="utf-8")
        try:
            build(builder.src_root, root / "dist")
        except SourceFormatError:
            return True
        return False


def jinja_environment_uses_custom_delimiters() -> bool:
    with TemporaryDirectory() as tmp:
        environment = make_jinja_environment(Path(tmp))
        return (
            environment.block_start_string == BLOCK_DELIMITER_START
            and environment.block_end_string == BLOCK_DELIMITER_END
            and environment.variable_start_string == VARIABLE_DELIMITER_START
            and environment.variable_end_string == VARIABLE_DELIMITER_END
            and environment.comment_start_string == COMMENT_DELIMITER_START
            and environment.comment_end_string == COMMENT_DELIMITER_END
        )


def standard_jinja_syntax_passes_through() -> bool:
    text = "{% if standard %}unchanged{{ standard }}{% endif %}"
    with TemporaryDirectory() as tmp:
        builder = _source_tree(Path(tmp))
        return render_text(text, shared_root=builder.shared_root) == text


def require_skill_expands_to_neutral_guidance() -> bool:
    rendered = expand_require_skill(RequireSkillDirective(SKILL_STANDARDS_REF))
    return (
        rendered == REQUIRE_SKILL_TEXT_TEMPLATE.format(skill_ref=SKILL_STANDARDS_REF)
        and SKILL_STANDARDS_REF in rendered
    )


def require_skill_renders_inline() -> bool:
    directive = format_directive(RequireSkillDirective(SKILL_STANDARDS_REF))
    with TemporaryDirectory() as tmp:
        builder = _source_tree(Path(tmp))
        rendered = render_text(directive, shared_root=builder.shared_root)
        return SKILL_STANDARDS_REF in rendered and directive not in rendered


def bare_conditional_renders_per_target() -> bool:
    template = (
        f"{BLOCK_DELIMITER_START} if target == 'claude' {BLOCK_DELIMITER_END}"
        "claude-only"
        f"{BLOCK_DELIMITER_START} else {BLOCK_DELIMITER_END}"
        "codex-only"
        f"{BLOCK_DELIMITER_START} endif {BLOCK_DELIMITER_END}"
    )
    with TemporaryDirectory() as tmp:
        builder = _source_tree(Path(tmp))
        rendered = {
            target: render_text(
                template,
                shared_root=builder.shared_root,
                variables={"target": target.value},
            )
            for target in Target
        }
        return (
            rendered[Target.CLAUDE] == "claude-only"
            and rendered[Target.CODEX] == "codex-only"
            and all(BLOCK_DELIMITER_START not in body for body in rendered.values())
        )


def skill_dir_escape_survives_jinja_pass() -> bool:
    escaped = (
        f"Write `{CLAUDE_SKILL_DIR_TOKEN}/x.md` {SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE}"
    )
    body = (
        f"---\nname: {SKILL_STANDARDS_NAME}\n---\n\n"
        f"{BLOCK_DELIMITER_START} if target == 'claude' {BLOCK_DELIMITER_END}"
        f"c{BLOCK_DELIMITER_START} endif {BLOCK_DELIMITER_END}\n{escaped}\n"
    )
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        builder = SrcTreeBuilder(root)
        builder.add_plugin(
            INSTRUCTIONS_PLUGIN_NAME,
            skills={SKILL_STANDARDS_NAME: body},
        )
        build(builder.src_root, root / "dist")
        reader = DistTreeReader(root)
        return all(
            CLAUDE_SKILL_DIR_TOKEN
            in reader.read_skill_body(
                INSTRUCTIONS_PLUGIN_NAME, SKILL_STANDARDS_NAME, target=target
            )
            and SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE
            not in reader.read_skill_body(
                INSTRUCTIONS_PLUGIN_NAME, SKILL_STANDARDS_NAME, target=target
            )
            for target in Target
        )


def require_skill_emits_identically_across_targets() -> bool:
    directive = format_directive(RequireSkillDirective(SKILL_STANDARDS_REF))
    body = f"---\nname: {SKILL_STANDARDS_NAME}\n---\n\nBefore.\n{directive}\nAfter.\n"
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        builder = SrcTreeBuilder(root)
        builder.add_plugin(
            INSTRUCTIONS_PLUGIN_NAME,
            skills={SKILL_STANDARDS_NAME: body},
        )
        source = (
            builder.src_root
            / PLUGINS_DIR_NAME
            / INSTRUCTIONS_PLUGIN_NAME
            / SKILLS_SUBDIR_NAME
            / SKILL_STANDARDS_NAME
            / SKILL_FILENAME
        )
        emitted = {}
        for target in Target:
            emit_skill(
                source,
                target=target,
                dist_root=root / "dist",
                shared_root=builder.shared_root,
            )
            emitted[target] = (
                root
                / "dist"
                / target.value
                / INSTRUCTIONS_PLUGIN_NAME
                / SKILLS_SUBDIR_NAME
                / SKILL_STANDARDS_NAME
                / SKILL_FILENAME
            ).read_text(encoding="utf-8")
        return (
            emitted[Target.CLAUDE] == emitted[Target.CODEX]
            and SKILL_STANDARDS_REF in emitted[Target.CLAUDE]
            and directive not in emitted[Target.CLAUDE]
        )


def include_uses_fragment_file_contract() -> bool:
    with TemporaryDirectory() as tmp:
        builder = _source_tree(Path(tmp))
        include = IncludeDirective(
            _fragment_path(SKILL_STANDARDS_NAME, scope=INSTRUCTIONS_PLUGIN_NAME)
        )
        return (
            render_text(format_directive(include), shared_root=builder.shared_root)
            == _FRAGMENT_BODY
        )


def _source_tree(root: Path) -> SrcTreeBuilder:
    builder = SrcTreeBuilder(root)
    builder.add_plugin(
        INSTRUCTIONS_PLUGIN_NAME,
        skills={SKILL_STANDARDS_NAME: _SKILL_BODY},
    )
    builder.add_shared_topic(
        INSTRUCTIONS_PLUGIN_NAME, SKILL_STANDARDS_NAME, _FRAGMENT_BODY
    )
    return builder


def _fragment_path(topic: str, *, scope: str = _SCOPE) -> str:
    return f"{scope}/{topic}/{SHARED_FRAGMENT_FILENAME}"


def _include_text(topic: str) -> str:
    return format_directive(IncludeDirective(_fragment_path(topic)))


def _raises_directive_syntax(text: str) -> bool:
    try:
        parse_directives(text)
    except DirectiveSyntaxError:
        return True
    return False
