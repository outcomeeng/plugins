"""Resource lifecycle and observations for source-and-templating evidence."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from hypothesis import given, seed, settings
from hypothesis import strategies as st

from outcomeeng.distribution.build import (
    BLOCK_DELIMITER_END,
    BLOCK_DELIMITER_START,
    CLAUDE_SKILL_DIR_TOKEN,
    COMMENT_DELIMITER_END,
    COMMENT_DELIMITER_START,
    IMPLEMENTED,
    SHARED_FRAGMENT_FILENAME,
    SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE,
    SKILL_FILENAME,
    VARIABLE_DELIMITER_END,
    VARIABLE_DELIMITER_START,
    CyclicIncludeError,
    Directive,
    DirectiveSyntaxError,
    IncludeDirective,
    IncludeResolutionError,
    RequireSkillDirective,
    SourceFormatError,
    build,
    emit_skill,
    expand_include,
    expand_require_skill,
    format_directive,
    make_jinja_environment,
    parse_directives,
    render_text,
)
from outcomeeng.distribution.contracts import (
    PLUGINS_DIR_NAME,
    REQUIRE_SKILL_GUIDANCE_TEMPLATE,
    SKILLS_SUBDIR_NAME,
    Target,
)
from outcomeeng_testing.generators.source_and_templating import (
    SourceScenario,
    source_scenarios,
)
from outcomeeng_testing.generators.directives import directives
from outcomeeng_testing.generators.fragments import (
    fragment_bodies,
    include_chain_depths,
    inert_fragment_bodies,
)
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

SOURCE_PROPERTY_EXAMPLES: Final = 20
SOURCE_PROPERTY_SEED: Final = 20260714
DIRECTIVE_PROPERTY_REPLAY_PATH: Final = (
    "just test spx/18-plugin-build.enabler/21-source-and-templating.enabler/tests/"
    "test_parse_directives.property.l1.py"
)
INCLUDE_PROPERTY_REPLAY_PATH: Final = (
    "just test spx/18-plugin-build.enabler/21-source-and-templating.enabler/tests/"
    "test_expand_include.property.l1.py"
)
RENDER_PROPERTY_REPLAY_PATH: Final = (
    "just test spx/18-plugin-build.enabler/21-source-and-templating.enabler/tests/"
    "test_render_text.property.l1.py"
)


def implementation_is_ready() -> bool:
    return IMPLEMENTED


def directive_roundtrip_property_holds() -> bool:
    run_replayable_property(
        _directive_roundtrip_property,
        seed_value=SOURCE_PROPERTY_SEED,
        replay_path=DIRECTIVE_PROPERTY_REPLAY_PATH,
    )
    return True


def include_body_property_holds() -> bool:
    run_replayable_property(
        _include_body_property,
        seed_value=SOURCE_PROPERTY_SEED,
        replay_path=INCLUDE_PROPERTY_REPLAY_PATH,
    )
    return True


def rendered_include_property_holds() -> bool:
    run_replayable_property(
        _rendered_include_property,
        seed_value=SOURCE_PROPERTY_SEED,
        replay_path=RENDER_PROPERTY_REPLAY_PATH,
    )
    return True


def recursive_include_property_holds() -> bool:
    run_replayable_property(
        _recursive_include_property,
        seed_value=SOURCE_PROPERTY_SEED,
        replay_path=RENDER_PROPERTY_REPLAY_PATH,
    )
    return True


def property_failure_notes_include_seed_and_replay() -> bool:
    def always_fails() -> None:
        raise AssertionError

    try:
        run_replayable_property(
            always_fails,
            seed_value=SOURCE_PROPERTY_SEED,
            replay_path=DIRECTIVE_PROPERTY_REPLAY_PATH,
        )
    except AssertionError as error:
        notes = getattr(error, "__notes__", ())
        return (
            f"Hypothesis seed: {SOURCE_PROPERTY_SEED}" in notes
            and f"Replay path: {DIRECTIVE_PROPERTY_REPLAY_PATH}" in notes
        )
    return False


@seed(SOURCE_PROPERTY_SEED)
@settings(
    max_examples=SOURCE_PROPERTY_EXAMPLES,
    deadline=None,
    print_blob=True,
)
@given(directive=directives())
def _directive_roundtrip_property(directive: Directive) -> None:
    assert parse_directives(format_directive(directive)) == (directive,)


@seed(SOURCE_PROPERTY_SEED)
@settings(
    max_examples=SOURCE_PROPERTY_EXAMPLES,
    deadline=None,
    print_blob=True,
)
@given(case=st.sampled_from(source_scenarios()), body=fragment_bodies())
def _include_body_property(case: SourceScenario, body: str) -> None:
    with TemporaryDirectory() as temporary_directory:
        builder = SrcTreeBuilder(Path(temporary_directory))
        builder.add_shared_topic(case.scope, case.inner_topic, body)
        directive = IncludeDirective(_fragment_path(case, case.inner_topic))
        assert expand_include(directive, shared_root=builder.shared_root) == body


@seed(SOURCE_PROPERTY_SEED)
@settings(
    max_examples=SOURCE_PROPERTY_EXAMPLES,
    deadline=None,
    print_blob=True,
)
@given(
    case=st.sampled_from(source_scenarios()),
    prefix=inert_fragment_bodies(),
    body=inert_fragment_bodies(),
    suffix=inert_fragment_bodies(),
)
def _rendered_include_property(
    case: SourceScenario,
    prefix: str,
    body: str,
    suffix: str,
) -> None:
    with TemporaryDirectory() as temporary_directory:
        builder = SrcTreeBuilder(Path(temporary_directory))
        builder.add_shared_topic(case.scope, case.inner_topic, body)
        directive = _include_text(case, case.inner_topic)
        template = "\n".join((prefix, directive, suffix))
        expected = "\n".join((prefix, body, suffix))
        assert render_text(template, shared_root=builder.shared_root) == expected


@seed(SOURCE_PROPERTY_SEED)
@settings(
    max_examples=SOURCE_PROPERTY_EXAMPLES,
    deadline=None,
    print_blob=True,
)
@given(
    case=st.sampled_from(source_scenarios()),
    depth=include_chain_depths(),
)
def _recursive_include_property(case: SourceScenario, depth: int) -> None:
    with TemporaryDirectory() as temporary_directory:
        builder = SrcTreeBuilder(Path(temporary_directory))
        topics = [f"{case.outer_topic}-{index}" for index in range(depth)]
        for index, topic in enumerate(topics):
            body = (
                case.fragment_body
                if index == depth - 1
                else _include_text(case, topics[index + 1])
            )
            builder.add_shared_topic(case.scope, topic, body)
        rendered = render_text(
            _include_text(case, topics[0]),
            shared_root=builder.shared_root,
        )
        assert rendered == case.fragment_body


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


def missing_fragment_raises() -> bool:
    return all(_missing_fragment_raises(case) for case in source_scenarios())


def nested_include_expands() -> bool:
    return all(_nested_include_expands(case) for case in source_scenarios())


def nested_require_skill_expands() -> bool:
    return all(_nested_require_expands(case) for case in source_scenarios())


def cyclic_includes_raise() -> bool:
    return all(_cyclic_includes_raise(case) for case in source_scenarios())


def bound_target_variable_renders_each_target() -> bool:
    template = f"target is {VARIABLE_DELIMITER_START} target {VARIABLE_DELIMITER_END}"
    return all(
        render_text(template, variables={"target": target.value})
        == f"target is {target.value}"
        for target in Target
    )


def well_formed_source_tree_builds() -> bool:
    repository_root = Path(__file__).parents[2]
    with TemporaryDirectory() as tmp:
        build(repository_root / "src", Path(tmp) / "dist")
    return True


def ordinary_plugin_root_file_is_accepted() -> bool:
    return all(_ordinary_file_is_emitted(case) for case in source_scenarios())


def shared_topic_without_fragment_is_rejected() -> bool:
    return all(_fragment_required(case) for case in source_scenarios())


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
    return all(_standard_jinja_passes(case) for case in source_scenarios())


def require_skill_expands_to_neutral_guidance() -> bool:
    return all(_require_expands_neutrally(case) for case in source_scenarios())


def require_skill_renders_inline() -> bool:
    return all(_require_renders_inline(case) for case in source_scenarios())


def bare_conditional_renders_per_target() -> bool:
    return all(_bare_conditional_renders(case) for case in source_scenarios())


def skill_dir_escape_survives_jinja_pass() -> bool:
    return all(_skill_dir_escape_survives(case) for case in source_scenarios())


def require_skill_emits_identically_across_targets() -> bool:
    return all(_require_emits_identically(case) for case in source_scenarios())


def include_uses_fragment_file_contract() -> bool:
    return all(_include_uses_contract(case) for case in source_scenarios())


def _missing_fragment_raises(case: SourceScenario) -> bool:
    with TemporaryDirectory() as tmp:
        builder = SrcTreeBuilder(Path(tmp))
        builder.shared_root.mkdir(parents=True)
        missing = _fragment_path(case, case.cycle_topic)
        try:
            expand_include(IncludeDirective(missing), shared_root=builder.shared_root)
        except IncludeResolutionError:
            return True
        return False


def _nested_include_expands(case: SourceScenario) -> bool:
    with TemporaryDirectory() as tmp:
        builder = SrcTreeBuilder(Path(tmp))
        builder.add_shared_topic(case.scope, case.inner_topic, case.fragment_body)
        builder.add_shared_topic(
            case.scope, case.outer_topic, _include_text(case, case.inner_topic)
        )
        return (
            render_text(
                _include_text(case, case.outer_topic), shared_root=builder.shared_root
            )
            == case.fragment_body
        )


def _nested_require_expands(case: SourceScenario) -> bool:
    with TemporaryDirectory() as tmp:
        builder = SrcTreeBuilder(Path(tmp))
        directive = format_directive(RequireSkillDirective(case.skill_ref))
        builder.add_shared_topic(case.scope, case.inner_topic, directive)
        result = render_text(
            _include_text(case, case.inner_topic), shared_root=builder.shared_root
        )
        return (
            result == expand_require_skill(RequireSkillDirective(case.skill_ref))
            and directive not in result
        )


def _cyclic_includes_raise(case: SourceScenario) -> bool:
    with TemporaryDirectory() as tmp:
        builder = SrcTreeBuilder(Path(tmp))
        builder.add_shared_topic(
            case.scope, case.inner_topic, _include_text(case, case.cycle_topic)
        )
        builder.add_shared_topic(
            case.scope, case.cycle_topic, _include_text(case, case.inner_topic)
        )
        try:
            render_text(
                _include_text(case, case.inner_topic), shared_root=builder.shared_root
            )
        except CyclicIncludeError:
            return True
        return False


def _ordinary_file_is_emitted(case: SourceScenario) -> bool:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        builder = _source_tree(root, case)
        filename = f".{case.skill}"
        (builder.src_root / PLUGINS_DIR_NAME / case.plugin / filename).write_text(
            case.fragment_body, encoding="utf-8"
        )
        build(builder.src_root, root / "dist")
        reader = DistTreeReader(root)
        return all(
            Path(case.plugin) / filename in reader.list_all_files(target)
            for target in Target
        )


def _fragment_required(case: SourceScenario) -> bool:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        builder = SrcTreeBuilder(root)
        builder.add_plugin(case.plugin, skills={case.skill: _skill_body(case)})
        topic = builder.shared_root / case.plugin / case.inner_topic
        topic.mkdir(parents=True)
        (topic / f"{case.outer_topic}.md").write_text(
            case.fragment_body, encoding="utf-8"
        )
        try:
            build(builder.src_root, root / "dist")
        except SourceFormatError:
            return True
        return False


def _standard_jinja_passes(case: SourceScenario) -> bool:
    text = f"{{% if {case.skill} %}}{case.fragment_body}{{{{ {case.skill} }}}}{{% endif %}}"
    with TemporaryDirectory() as tmp:
        builder = _source_tree(Path(tmp), case)
        return render_text(text, shared_root=builder.shared_root) == text


def _require_expands_neutrally(case: SourceScenario) -> bool:
    rendered = expand_require_skill(RequireSkillDirective(case.skill_ref))
    return (
        rendered == REQUIRE_SKILL_GUIDANCE_TEMPLATE.format(skill_ref=case.skill_ref)
        and case.skill_ref in rendered
    )


def _require_renders_inline(case: SourceScenario) -> bool:
    directive = format_directive(RequireSkillDirective(case.skill_ref))
    with TemporaryDirectory() as tmp:
        builder = _source_tree(Path(tmp), case)
        rendered = render_text(directive, shared_root=builder.shared_root)
        return case.skill_ref in rendered and directive not in rendered


def _bare_conditional_renders(case: SourceScenario) -> bool:
    template = (
        f"{BLOCK_DELIMITER_START} if target == '{Target.CLAUDE.value}' "
        f"{BLOCK_DELIMITER_END}{case.branch_payloads[Target.CLAUDE]}"
        f"{BLOCK_DELIMITER_START} else {BLOCK_DELIMITER_END}"
        f"{case.branch_payloads[Target.CODEX]}"
        f"{BLOCK_DELIMITER_START} endif {BLOCK_DELIMITER_END}"
    )
    with TemporaryDirectory() as tmp:
        builder = _source_tree(Path(tmp), case)
        rendered = {
            target: render_text(
                template,
                shared_root=builder.shared_root,
                variables={"target": target.value},
            )
            for target in Target
        }
        return rendered == case.branch_payloads and all(
            BLOCK_DELIMITER_START not in body for body in rendered.values()
        )


def _skill_dir_escape_survives(case: SourceScenario) -> bool:
    escaped = f"Write `{CLAUDE_SKILL_DIR_TOKEN}/{case.skill}.md` {SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE}"
    body = (
        f"---\nname: {case.skill}\n---\n\n"
        f"{BLOCK_DELIMITER_START} if target == '{Target.CLAUDE.value}' "
        f"{BLOCK_DELIMITER_END}"
        f"{case.fragment_body}{BLOCK_DELIMITER_START} endif {BLOCK_DELIMITER_END}\n"
        f"{escaped}\n"
    )
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        builder = SrcTreeBuilder(root)
        builder.add_plugin(case.plugin, skills={case.skill: body})
        build(builder.src_root, root / "dist")
        reader = DistTreeReader(root)
        return all(
            CLAUDE_SKILL_DIR_TOKEN
            in reader.read_skill_body(case.plugin, case.skill, target=target)
            and SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE
            not in reader.read_skill_body(case.plugin, case.skill, target=target)
            for target in Target
        )


def _require_emits_identically(case: SourceScenario) -> bool:
    directive = format_directive(RequireSkillDirective(case.skill_ref))
    body = f"---\nname: {case.skill}\n---\n\n{case.fragment_body}{directive}\n"
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        builder = SrcTreeBuilder(root)
        builder.add_plugin(case.plugin, skills={case.skill: body})
        source = (
            builder.src_root
            / PLUGINS_DIR_NAME
            / case.plugin
            / SKILLS_SUBDIR_NAME
            / case.skill
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
                / case.plugin
                / SKILLS_SUBDIR_NAME
                / case.skill
                / SKILL_FILENAME
            ).read_text(encoding="utf-8")
        return (
            emitted[Target.CLAUDE] == emitted[Target.CODEX]
            and case.skill_ref in emitted[Target.CLAUDE]
            and directive not in emitted[Target.CLAUDE]
        )


def _include_uses_contract(case: SourceScenario) -> bool:
    with TemporaryDirectory() as tmp:
        builder = _source_tree(Path(tmp), case)
        include = IncludeDirective(
            _fragment_path(case, case.inner_topic, scope=case.plugin)
        )
        return (
            render_text(format_directive(include), shared_root=builder.shared_root)
            == case.fragment_body
        )


def _source_tree(root: Path, case: SourceScenario) -> SrcTreeBuilder:
    builder = SrcTreeBuilder(root)
    builder.add_plugin(case.plugin, skills={case.skill: _skill_body(case)})
    builder.add_shared_topic(case.plugin, case.inner_topic, case.fragment_body)
    return builder


def _skill_body(case: SourceScenario) -> str:
    return f"---\nname: {case.skill}\n---\n\n{case.fragment_body}"


def _fragment_path(
    case: SourceScenario, topic: str, *, scope: str | None = None
) -> str:
    return f"{scope or case.scope}/{topic}/{SHARED_FRAGMENT_FILENAME}"


def _include_text(case: SourceScenario, topic: str) -> str:
    return format_directive(IncludeDirective(_fragment_path(case, topic)))


def _raises_directive_syntax(text: str) -> bool:
    try:
        parse_directives(text)
    except DirectiveSyntaxError:
        return True
    return False
