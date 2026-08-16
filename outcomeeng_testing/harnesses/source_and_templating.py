"""Resource lifecycle and observations for source-and-templating evidence."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, Iterator

from hypothesis import given, seed, settings
from hypothesis import strategies as st

from outcomeeng.distribution.build import (
    BLOCK_DELIMITER_END,
    BLOCK_DELIMITER_START,
    CLAUDE_SKILL_DIR_TOKEN,
    COMMENT_DELIMITER_END,
    COMMENT_DELIMITER_START,
    IMPLEMENTED,
    JINJA_CONTROL_KEYWORDS,
    SHARED_DIR_NAME,
    SHARED_FRAGMENT_FILENAME,
    SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE,
    VARIABLE_DELIMITER_END,
    VARIABLE_DELIMITER_START,
    CyclicIncludeError,
    Directive,
    DirectiveSyntaxError,
    IncludeDirective,
    RequireSkillDirective,
    SourceFormatError,
    build,
    EmissionAction,
    ProjectedEmission,
    emit_skill,
    expand_include,
    expand_require_skill,
    format_directive,
    make_jinja_environment,
    parse_directives,
    project_emissions,
    plugin_source_files,
    render_text,
    resolve_runtime_token,
    runtime_token_resolver_cases,
)
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    BUILD_TARGET_VARIABLE,
    DIST_DIR_NAME,
    MARKDOWN_FILE_SUFFIX,
    PLUGINS_DIR_NAME,
    REFERENCES_SUBDIR_NAME,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
)
from outcomeeng_testing.generators.source_and_templating import (
    RawDirectiveCase,
    SourceScenario,
    raw_directive_cases,
    source_scenarios,
    unrecognized_plugin_subdirectory_names,
)
from outcomeeng_testing.generators.directives import directives, standard_jinja_syntax
from outcomeeng_testing.generators.fragments import (
    fragment_bodies,
    include_chain_indices,
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


@dataclass(frozen=True)
class MissingFragmentCase:
    """One spec-declared missing-fragment scenario with harness-owned resources."""

    template: str
    shared_root: Path
    src_root: Path


@dataclass(frozen=True)
class RequiredSkillGuidanceObservation:
    """Rendered required-skill guidance and its source-owned runtime names."""

    skill_ref: str
    guidance: str
    runtime_names: tuple[str, ...]


def implementation_is_ready() -> bool:
    return IMPLEMENTED


def directive_roundtrip_property_holds() -> bool:
    run_replayable_property(
        _directive_roundtrip_property,
        seed_value=SOURCE_PROPERTY_SEED,
        replay_path=DIRECTIVE_PROPERTY_REPLAY_PATH,
    )
    return True


def standard_jinja_syntax_property_holds() -> bool:
    run_replayable_property(
        _standard_jinja_syntax_property,
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
        raise ValueError

    try:
        run_replayable_property(
            always_fails,
            seed_value=SOURCE_PROPERTY_SEED,
            replay_path=DIRECTIVE_PROPERTY_REPLAY_PATH,
        )
    except ValueError as error:
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
@given(text=standard_jinja_syntax())
def _standard_jinja_syntax_property(text: str) -> None:
    with TemporaryDirectory() as temporary_directory:
        shared_root = Path(temporary_directory)
        assert parse_directives(text) == ()
        assert render_text(text, shared_root=shared_root) == text


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
    body=inert_fragment_bodies(),
    indices=include_chain_indices(),
)
def _recursive_include_property(
    case: SourceScenario,
    body: str,
    indices: list[int],
) -> None:
    with TemporaryDirectory() as temporary_directory:
        builder = SrcTreeBuilder(Path(temporary_directory))
        topics = tuple(f"{case.outer_topic}-{index}" for index in indices)
        for position, topic in enumerate(topics):
            fragment = (
                body
                if position == len(topics) - 1
                else _include_text(case, topics[position + 1])
            )
            builder.add_shared_topic(case.scope, topic, fragment)
        rendered = render_text(
            _include_text(case, topics[0]),
            shared_root=builder.shared_root,
        )
        assert rendered == body


def unknown_directive_raises() -> bool:
    return _raises_directive_syntax(
        f"{BLOCK_DELIMITER_START} unknown_directive 'arg' {BLOCK_DELIMITER_END}"
    )


def missing_directive_argument_raises() -> bool:
    return _raises_directive_syntax(
        f"{BLOCK_DELIMITER_START} include {BLOCK_DELIMITER_END}"
    )


def custom_jinja_controls_have_no_directives() -> bool:
    return all(_bare_conditional_renders(case) for case in source_scenarios()) and all(
        parse_directives(f"{BLOCK_DELIMITER_START} {keyword} {BLOCK_DELIMITER_END}")
        == ()
        for keyword in JINJA_CONTROL_KEYWORDS
    )


def render_missing_fragment() -> None:
    with _missing_fragment_case() as case:
        render_text(case.template, shared_root=case.shared_root)


def project_missing_fragment() -> None:
    with _missing_fragment_case() as case:
        project_emissions(case.src_root)


@contextmanager
def _missing_fragment_case() -> Iterator[MissingFragmentCase]:
    case = min(source_scenarios(), key=lambda scenario: scenario.skill_ref)
    with TemporaryDirectory() as tmp:
        builder = SrcTreeBuilder(Path(tmp))
        builder.shared_root.mkdir(parents=True)
        template = format_directive(
            IncludeDirective(_fragment_path(case, case.cycle_topic))
        )
        builder.add_plugin(case.plugin, skills={case.skill: template})
        yield MissingFragmentCase(
            template=template,
            shared_root=builder.shared_root,
            src_root=builder.src_root,
        )


def nested_include_expands() -> bool:
    return all(_nested_include_expands(case) for case in source_scenarios())


def nested_require_skill_expands() -> bool:
    return all(_nested_require_expands(case) for case in source_scenarios())


def cyclic_includes_raise() -> bool:
    return all(_cyclic_includes_raise(case) for case in source_scenarios())


def bound_target_variable_renders_each_target() -> bool:
    template = f"target is {VARIABLE_DELIMITER_START} target {VARIABLE_DELIMITER_END}"
    return all(
        render_text(template, variables={BUILD_TARGET_VARIABLE: target.value})
        == f"target is {target.value}"
        for target in Target
    )


def well_formed_source_tree_builds() -> bool:
    return all(_well_formed_source_tree_builds(case) for case in source_scenarios())


def malformed_source_tree_is_rejected() -> bool:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        source_root = root / SOURCE_ROOT_NAME
        source_root.mkdir()
        try:
            project_emissions(source_root)
        except SourceFormatError as error:
            return str(source_root / PLUGINS_DIR_NAME) in str(error)
        return False


def ordinary_plugin_root_file_is_accepted() -> bool:
    return all(_ordinary_file_is_emitted(case) for case in source_scenarios())


def unrecognized_plugin_subdirectories_are_rejected() -> bool:
    return all(
        _unrecognized_plugin_subdirectory_is_rejected(name)
        for name in unrecognized_plugin_subdirectory_names()
    )


def shared_topic_without_fragment_is_rejected() -> bool:
    return all(_fragment_required(case) for case in source_scenarios())


def shared_topic_references_travel_with_fragment() -> bool:
    return all(_shared_topic_reference_travels(case) for case in source_scenarios())


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


def observe_required_skill_guidance() -> tuple[RequiredSkillGuidanceObservation, ...]:
    runtime_names = _runtime_specific_names()
    return tuple(
        RequiredSkillGuidanceObservation(
            skill_ref=case.skill_ref,
            guidance=expand_require_skill(RequireSkillDirective(case.skill_ref)),
            runtime_names=runtime_names,
        )
        for case in source_scenarios()
    )


def require_skill_neutrality_oracle_rejects_runtime_specific_guidance() -> bool:
    runtime_names = _runtime_specific_names()
    return all(
        not _require_guidance_is_neutral(
            " ".join((case.skill_ref, runtime_name)),
            skill_ref=case.skill_ref,
            runtime_names=runtime_names,
        )
        for case in source_scenarios()
        for runtime_name in runtime_names
    )


def require_skill_locality_oracle_rejects_inlined_content() -> bool:
    return all(
        not _require_guidance_keeps_sister_content_local(
            "\n".join(
                (
                    expand_require_skill(RequireSkillDirective(case.skill_ref)),
                    _skill_body(case),
                )
            ),
            sister_content=_skill_body(case),
        )
        for case in source_scenarios()
    )


def require_skill_renders_inline() -> bool:
    return all(_require_renders_inline(case) for case in source_scenarios())


def bare_conditional_renders_per_target() -> bool:
    return all(_bare_conditional_renders(case) for case in source_scenarios())


def skill_dir_escape_survives_jinja_pass() -> bool:
    return all(_skill_dir_escape_survives(case) for case in source_scenarios())


def observe_build_comment_outputs(
    case: SourceScenario,
) -> dict[str, tuple[str, str]]:
    """Return each target's rendered body plus the comment that body carried.

    The body carries no variable token and no control block, which is the shape
    the render pass short-circuits on.
    """
    comment = f"{COMMENT_DELIMITER_START} {case.scope}-marker {COMMENT_DELIMITER_END}"
    body = f"---\nname: {case.skill}\n---\n\n{case.fragment_body} {comment}\n"
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        builder = SrcTreeBuilder(root)
        builder.add_plugin(case.plugin, skills={case.skill: body})
        build(builder.src_root, root / "dist")
        reader = DistTreeReader(root)
        return {
            target.value: (
                reader.read_skill_body(case.plugin, case.skill, target=target),
                comment,
            )
            for target in Target
        }


def raw_directive_ships_literally() -> bool:
    return all(_raw_directive_ships_literally(case) for case in raw_directive_cases())


def require_skill_emits_identically_across_targets() -> bool:
    return all(_require_emits_identically(case) for case in source_scenarios())


def include_uses_fragment_file_contract() -> bool:
    return all(_include_uses_contract(case) for case in source_scenarios())


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


def _unrecognized_plugin_subdirectory_is_rejected(name: str) -> bool:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        case = source_scenarios()[0]
        builder = _source_tree(root, case)
        unexpected = builder.src_root / PLUGINS_DIR_NAME / case.plugin / name
        unexpected.mkdir()
        try:
            build(builder.src_root, root / DIST_DIR_NAME)
        except SourceFormatError as error:
            return str(unexpected.relative_to(builder.src_root)) in str(error)
        return False


def _well_formed_source_tree_builds(case: SourceScenario) -> bool:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        builder = SrcTreeBuilder(root)
        builder.add_shared_topic(case.scope, case.inner_topic, case.fragment_body)
        builder.add_plugin(
            case.plugin,
            skills={case.skill: _skill_body(case)},
            agents={case.outer_topic: case.fragment_body},
        )
        plugin_root = builder.src_root / PLUGINS_DIR_NAME / case.plugin
        authored_plugin_files = (
            plugin_root / SKILLS_SUBDIR_NAME / case.skill / SKILL_FILENAME,
            plugin_root
            / AGENTS_SUBDIR_NAME
            / f"{case.outer_topic}{MARKDOWN_FILE_SUFFIX}",
        )
        required_files = (
            *authored_plugin_files,
            builder.src_root
            / SHARED_DIR_NAME
            / case.scope
            / case.inner_topic
            / SHARED_FRAGMENT_FILENAME,
        )
        if not all(path.is_file() for path in required_files):
            return False
        source_inventory = frozenset(plugin_source_files(builder.src_root))
        if not frozenset(authored_plugin_files) <= source_inventory:
            return False
        projection = project_emissions(builder.src_root)
        projected_plugin_emissions = tuple(
            emission
            for emission in projection.emissions
            if emission.source in authored_plugin_files
        )
        if not all(
            any(emission.source == source for emission in projected_plugin_emissions)
            for source in authored_plugin_files
        ):
            return False
        build(builder.src_root, root / DIST_DIR_NAME)
        reader = DistTreeReader(root)
        return all(
            emission.relative_path in reader.list_all_files(emission.target)
            for emission in projected_plugin_emissions
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


def _runtime_specific_names() -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            resolve_runtime_token(
                coordinate.kind,
                coordinate.capability,
                coordinate.runtime,
            )
            for coordinate in runtime_token_resolver_cases()
        )
    )


def _require_guidance_is_neutral(
    guidance: str,
    *,
    skill_ref: str,
    runtime_names: tuple[str, ...],
) -> bool:
    prose = guidance.replace(skill_ref, "")
    return skill_ref in guidance and all(name not in prose for name in runtime_names)


def _require_guidance_keeps_sister_content_local(
    guidance: str,
    *,
    sister_content: str,
) -> bool:
    return sister_content not in guidance


def _require_renders_inline(case: SourceScenario) -> bool:
    directive = format_directive(RequireSkillDirective(case.skill_ref))
    with TemporaryDirectory() as tmp:
        builder = _source_tree(Path(tmp), case)
        rendered = render_text(directive, shared_root=builder.shared_root)
        return case.skill_ref in rendered and directive not in rendered


def _bare_conditional_renders(case: SourceScenario) -> bool:
    template = (
        f"{BLOCK_DELIMITER_START} if {BUILD_TARGET_VARIABLE} == '{Target.CLAUDE.value}' "
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
                variables={BUILD_TARGET_VARIABLE: target.value},
            )
            for target in Target
        }
        return (
            parse_directives(template) == ()
            and rendered == case.branch_payloads
            and all(BLOCK_DELIMITER_START not in body for body in rendered.values())
        )


def _skill_dir_escape_survives(case: SourceScenario) -> bool:
    escaped = f"Write `{CLAUDE_SKILL_DIR_TOKEN}/{case.skill}.md` {SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE}"
    body = (
        f"---\nname: {case.skill}\n---\n\n"
        f"{BLOCK_DELIMITER_START} if {BUILD_TARGET_VARIABLE} == '{Target.CLAUDE.value}' "
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


def _raw_directive_ships_literally(case: RawDirectiveCase) -> bool:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        builder = SrcTreeBuilder(root)
        if (
            render_text(case.template, shared_root=builder.shared_root)
            != case.directive
        ):
            return False
        builder.add_plugin(
            case.source.plugin,
            skills={case.source.skill: case.template},
        )
        project_emissions(builder.src_root)
        build(builder.src_root, root / DIST_DIR_NAME)
        reader = DistTreeReader(root)
        return all(
            reader.read_skill_body(
                case.source.plugin,
                case.source.skill,
                target=target,
            ).strip()
            == case.directive
            for target in Target
        )


def _require_emits_identically(case: SourceScenario) -> bool:
    directive = format_directive(RequireSkillDirective(case.skill_ref))
    caller_skill = case.outer_topic
    sister_content = _skill_body(case)
    caller_body = f"---\nname: {caller_skill}\n---\n\n{directive}\n"
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        builder = SrcTreeBuilder(root)
        builder.add_plugin(
            case.plugin,
            skills={caller_skill: caller_body, case.skill: sister_content},
        )
        source = (
            builder.src_root
            / PLUGINS_DIR_NAME
            / case.plugin
            / SKILLS_SUBDIR_NAME
            / caller_skill
            / SKILL_FILENAME
        )
        relative_path = source.relative_to(builder.src_root / PLUGINS_DIR_NAME)
        emitted = {}
        for target in Target:
            emit_skill(
                ProjectedEmission(
                    source=source,
                    target=target,
                    relative_path=relative_path,
                    action=EmissionAction.RENDER,
                ),
                dist_root=root / "dist",
                shared_root=builder.shared_root,
            )
            emitted[target] = (
                root
                / "dist"
                / target.value
                / case.plugin
                / SKILLS_SUBDIR_NAME
                / caller_skill
                / SKILL_FILENAME
            ).read_text(encoding="utf-8")
        return (
            emitted[Target.CLAUDE] == emitted[Target.CODEX]
            and case.skill_ref in emitted[Target.CLAUDE]
            and directive not in emitted[Target.CLAUDE]
            and all(
                _require_guidance_keeps_sister_content_local(
                    body,
                    sister_content=sister_content,
                )
                for body in emitted.values()
            )
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


def _shared_topic_reference_travels(case: SourceScenario) -> bool:
    inner_reference_name = f"{case.inner_topic}{MARKDOWN_FILE_SUFFIX}"
    outer_reference_name = f"{case.outer_topic}{MARKDOWN_FILE_SUFFIX}"
    reference_bodies = dict.fromkeys(
        (inner_reference_name, outer_reference_name),
        case.fragment_body,
    )
    include_body = _include_text(case, case.outer_topic)
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        builder = SrcTreeBuilder(root)
        builder.add_shared_topic(
            case.scope,
            case.inner_topic,
            case.fragment_body,
            references={inner_reference_name: reference_bodies[inner_reference_name]},
        )
        builder.add_shared_topic(
            case.scope,
            case.outer_topic,
            _include_text(case, case.inner_topic),
            references={outer_reference_name: reference_bodies[outer_reference_name]},
        )
        builder.add_plugin(
            case.plugin,
            skills={
                case.skill: f"{_skill_body(case)}\n{include_body}",
            },
        )
        build(builder.src_root, root / DIST_DIR_NAME)
        reader = DistTreeReader(root)
        relative_reference_roots = (
            Path(case.plugin)
            / SKILLS_SUBDIR_NAME
            / case.skill
            / REFERENCES_SUBDIR_NAME,
        )
        return all(
            (
                reader.target_root(target) / relative_reference_root / reference_name
            ).read_text(encoding="utf-8")
            == reference_body
            for target in Target
            for relative_reference_root in relative_reference_roots
            for reference_name, reference_body in reference_bodies.items()
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
