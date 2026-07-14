"""Resource lifecycle and observations for target-emission evidence."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.build import (
    CLAUDE_ONLY_FRONTMATTER_FIELDS,
    CLAUDE_SKILL_DIR_TOKEN,
    CODEX_SKILL_DIR_TOKEN,
    COMMAND_FILE_SUFFIX,
    COMMANDS_SUBDIR_NAME,
    EXECUTION_TIME_INJECTION_TOKEN,
    REFERENCES_SUBDIR_NAME,
    SHARED_FRAGMENT_FILENAME,
    SKILL_FILENAME,
    SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE,
    build,
    format_directive,
    rewrite_paths_for_target,
    strip_frontmatter_fields,
    IncludeDirective,
)
from outcomeeng.distribution.contracts import DIST_DIR_NAME, SKILLS_SUBDIR_NAME, Target
from outcomeeng.validation.skill_frontmatter import PORTABLE_CAPABILITY_FIELDS
from outcomeeng_testing.generators.source_and_templating import (
    SourceScenario,
    source_scenarios,
)
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder


def every_source_file_emits_to_each_target() -> bool:
    return all(_source_files_emit(case) for case in source_scenarios())


def target_trees_mirror_source_structure() -> bool:
    return all(_target_trees_mirror(case) for case in source_scenarios())


def claude_output_preserves_skill_dir_token() -> bool:
    return all(_claude_preserves_token(case) for case in source_scenarios())


def codex_output_rewrites_skill_dir_token() -> bool:
    return all(_codex_rewrites_token(case) for case in source_scenarios())


def skill_dir_escape_preserves_authoring_guidance() -> bool:
    return all(_escape_preserves_token(case) for case in source_scenarios())


def codex_skill_frontmatter_strips_claude_fields() -> bool:
    return all(_skill_frontmatter_translates(case) for case in source_scenarios())


def codex_command_frontmatter_strips_claude_fields() -> bool:
    return all(_command_frontmatter_translates(case) for case in source_scenarios())


def path_rewrite_is_idempotent() -> bool:
    return all(_path_rewrite_is_idempotent(case) for case in source_scenarios())


def frontmatter_strip_is_idempotent() -> bool:
    return all(_frontmatter_strip_is_idempotent(case) for case in source_scenarios())


def outputs_exclude_execution_time_injection() -> bool:
    return all(_outputs_exclude_injection(case) for case in source_scenarios())


def _source_files_emit(case: SourceScenario) -> bool:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        builder = SrcTreeBuilder(root)
        builder.add_plugin(
            case.plugin,
            skills={case.skill: case.fragment_body},
            commands={case.outer_topic: case.fragment_body},
        )
        build(builder.src_root, root / DIST_DIR_NAME)
        reader = DistTreeReader(root)
        expected_skill = Path(
            case.plugin,
            SKILLS_SUBDIR_NAME,
            case.skill,
            SKILL_FILENAME,
        )
        expected_command = Path(
            case.plugin,
            COMMANDS_SUBDIR_NAME,
            f"{case.outer_topic}{COMMAND_FILE_SUFFIX}",
        )
        return all(
            expected_skill in reader.list_all_files(target)
            and expected_command in reader.list_all_files(target)
            for target in Target
        )


def _target_trees_mirror(case: SourceScenario) -> bool:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        builder = SrcTreeBuilder(root)
        builder.add_plugin(case.plugin, skills={case.skill: case.fragment_body})
        build(builder.src_root, root / DIST_DIR_NAME)
        reader = DistTreeReader(root)
        return all(
            reader.list_plugins(target) == (case.plugin,)
            and reader.list_skills(case.plugin, target=target) == (case.skill,)
            for target in Target
        )


def _claude_preserves_token(case: SourceScenario) -> bool:
    reference = _claude_reference(case)
    body = _built_skill_body(case, reference, target=Target.CLAUDE)
    return reference in body


def _codex_rewrites_token(case: SourceScenario) -> bool:
    claude_reference = _claude_reference(case)
    codex_reference = claude_reference.replace(
        CLAUDE_SKILL_DIR_TOKEN,
        CODEX_SKILL_DIR_TOKEN,
    )
    body = _built_skill_body(case, claude_reference, target=Target.CODEX)
    return CLAUDE_SKILL_DIR_TOKEN not in body and codex_reference in body


def _escape_preserves_token(case: SourceScenario) -> bool:
    reference = _claude_reference(case)
    source = f"{reference} {SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE}"
    return all(
        reference in _built_skill_body(case, source, target=target)
        and SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE
        not in _built_skill_body(case, source, target=target)
        for target in Target
    )


def _skill_frontmatter_translates(case: SourceScenario) -> bool:
    source = _frontmatter_source(case)
    claude_body = _built_skill_body(case, source, target=Target.CLAUDE)
    codex_body = _built_skill_body(case, source, target=Target.CODEX)
    return _frontmatter_translation_holds(claude_body, codex_body)


def _command_frontmatter_translates(case: SourceScenario) -> bool:
    source = _frontmatter_source(case)
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        builder = SrcTreeBuilder(root)
        builder.add_plugin(case.plugin, commands={case.outer_topic: source})
        build(builder.src_root, root / DIST_DIR_NAME)
        reader = DistTreeReader(root)
        claude_body = _command_body(reader, case, target=Target.CLAUDE)
        codex_body = _command_body(reader, case, target=Target.CODEX)
        return _frontmatter_translation_holds(claude_body, codex_body)


def _path_rewrite_is_idempotent(case: SourceScenario) -> bool:
    once = rewrite_paths_for_target(_claude_reference(case), target=Target.CODEX)
    return rewrite_paths_for_target(once, target=Target.CODEX) == once


def _frontmatter_strip_is_idempotent(case: SourceScenario) -> bool:
    once = strip_frontmatter_fields(
        _frontmatter_source(case),
        fields=CLAUDE_ONLY_FRONTMATTER_FIELDS,
    )
    return strip_frontmatter_fields(once, fields=CLAUDE_ONLY_FRONTMATTER_FIELDS) == once


def _outputs_exclude_injection(case: SourceScenario) -> bool:
    reference_name = f"{case.outer_topic}{COMMAND_FILE_SUFFIX}"
    directive = format_directive(
        IncludeDirective(f"{case.scope}/{case.inner_topic}/{SHARED_FRAGMENT_FILENAME}")
    )
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        builder = SrcTreeBuilder(root)
        builder.add_shared_topic(
            case.scope,
            case.inner_topic,
            case.fragment_body,
            references={reference_name: case.fragment_body},
        )
        builder.add_plugin(case.plugin, skills={case.skill: directive})
        build(builder.src_root, root / DIST_DIR_NAME)
        reader = DistTreeReader(root)
        return all(
            all(
                EXECUTION_TIME_INJECTION_TOKEN
                not in (reader.target_root(target) / relative_path).read_text(
                    encoding="utf-8"
                )
                for relative_path in reader.list_all_files(target)
            )
            and (
                reader.target_root(target)
                / case.plugin
                / SKILLS_SUBDIR_NAME
                / case.skill
                / REFERENCES_SUBDIR_NAME
                / reference_name
            ).is_file()
            for target in Target
        )


def _built_skill_body(
    case: SourceScenario,
    source: str,
    *,
    target: Target,
) -> str:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        builder = SrcTreeBuilder(root)
        builder.add_plugin(case.plugin, skills={case.skill: source})
        build(builder.src_root, root / DIST_DIR_NAME)
        return DistTreeReader(root).read_skill_body(
            case.plugin,
            case.skill,
            target=target,
        )


def _command_body(
    reader: DistTreeReader,
    case: SourceScenario,
    *,
    target: Target,
) -> str:
    path = (
        reader.target_root(target)
        / case.plugin
        / COMMANDS_SUBDIR_NAME
        / f"{case.outer_topic}{COMMAND_FILE_SUFFIX}"
    )
    return path.read_text(encoding="utf-8")


def _claude_reference(case: SourceScenario) -> str:
    return f"{CLAUDE_SKILL_DIR_TOKEN}/{REFERENCES_SUBDIR_NAME}/{case.outer_topic}.md"


def _frontmatter_source(case: SourceScenario) -> str:
    claude_fields = "\n".join(
        f"{field}: true" for field in CLAUDE_ONLY_FRONTMATTER_FIELDS
    )
    portable_fields = "\n".join(
        f"{field}: {case.outer_topic}" for field in PORTABLE_CAPABILITY_FIELDS
    )
    return f"---\n{claude_fields}\n{portable_fields}\n---\n{case.fragment_body}"


def _frontmatter_translation_holds(claude_body: str, codex_body: str) -> bool:
    return all(
        f"{field}:" in claude_body and f"{field}:" not in codex_body
        for field in CLAUDE_ONLY_FRONTMATTER_FIELDS
    ) and all(
        f"{field}:" in claude_body and f"{field}:" in codex_body
        for field in PORTABLE_CAPABILITY_FIELDS
    )
