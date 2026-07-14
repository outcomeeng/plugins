"""Full-tree observations for target-emission evidence."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.build import (
    BLOCK_DELIMITER_START,
    BuildPlan,
    CLAUDE_ONLY_FRONTMATTER_FIELDS,
    CLAUDE_SKILL_DIR_TOKEN,
    CODEX_SKILL_DIR_TOKEN,
    COMMAND_FILE_SUFFIX,
    COMMANDS_SUBDIR_NAME,
    DISABLE_MODEL_INVOCATION_FIELD,
    EmissionAction,
    EXECUTION_TIME_INJECTION_TOKEN,
    IGNORED_SOURCE_DIRECTORY_NAMES,
    IGNORED_SOURCE_FILE_SUFFIXES,
    PLUGIN_SUBDIRS,
    SHARED_FRAGMENT_FILENAME,
    SKILL_FILENAME,
    SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE,
    IncludeDirective,
    build,
    format_directive,
    frontmatter_field_names,
    plan_emissions,
    rewrite_paths_for_target,
    strip_frontmatter_fields,
)
from outcomeeng.distribution.contracts import (
    DIST_DIR_NAME,
    PLUGINS_DIR_NAME,
    SKILLS_SUBDIR_NAME,
    TEXT_FILE_SUFFIXES,
    Target,
)
from outcomeeng.validation.skill_frontmatter import (
    ALLOWED_TOOLS_FIELD,
    ARGUMENT_HINT_FIELD,
)
from outcomeeng_testing.generators.source_and_templating import (
    SourceScenario,
    source_scenarios,
)
from outcomeeng_testing.harnesses.distribution import (
    CANONICAL_SOURCE_ROOT,
    snapshot_files,
)
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

type PathSnapshot = tuple[tuple[Path, bytes], ...]


@dataclass(frozen=True)
class TargetEmissionSnapshot:
    """Canonical source files and the outputs emitted from them."""

    source: PathSnapshot
    claude: PathSnapshot
    codex: PathSnapshot
    plan: BuildPlan

    def target(self, target: Target) -> PathSnapshot:
        return self.claude if target is Target.CLAUDE else self.codex


def every_source_file_emits_to_each_target() -> bool:
    snapshot = _canonical_emission_snapshot()
    expected = tuple(path for path, _content in snapshot.source)
    direct_outputs = {
        target: Counter(
            emission.relative_path
            for emission in snapshot.plan.for_target(target)
            if emission.action is not EmissionAction.FAN_OUT
        )
        for target in Target
    }
    return (
        bool(expected)
        and tuple(
            path.relative_to(CANONICAL_SOURCE_ROOT / PLUGINS_DIR_NAME)
            for path in snapshot.plan.plugin_sources
        )
        == expected
        and all(
            direct_outputs[target] == Counter({path: 1 for path in expected})
            and _planned_paths(snapshot.plan, target)
            == {path for path, _content in snapshot.target(target)}
            for target in Target
        )
        and _synthetic_inventory_is_complete()
    )


def target_trees_mirror_source_structure() -> bool:
    snapshot = _canonical_emission_snapshot()
    source_paths = {path for path, _content in snapshot.source}
    source_directories = _parent_directories(snapshot.source)
    return bool(source_paths) and all(
        source_paths <= {path for path, _content in snapshot.target(target)}
        and source_directories <= _parent_directories(snapshot.target(target))
        for target in Target
    )


def claude_output_preserves_skill_dir_token() -> bool:
    snapshot = _canonical_emission_snapshot()
    output_files = dict(snapshot.claude)
    relevant = {
        path: text
        for path, text in _text_files(snapshot.source).items()
        if CLAUDE_SKILL_DIR_TOKEN in text and BLOCK_DELIMITER_START not in text
    }
    failures = tuple(
        (
            path,
            text.count(CLAUDE_SKILL_DIR_TOKEN),
            _decode_text(output_files[path]).count(CLAUDE_SKILL_DIR_TOKEN),
        )
        for path, text in relevant.items()
        if _decode_text(output_files[path]).count(CLAUDE_SKILL_DIR_TOKEN)
        < text.count(CLAUDE_SKILL_DIR_TOKEN)
    )
    synthetic = _synthetic_skill_dir_translation_holds()
    if not relevant or failures or not synthetic:
        raise AssertionError(
            f"Claude skill-directory preservation mismatch: {failures=}, {synthetic=}"
        )
    return True


def codex_output_rewrites_skill_dir_token() -> bool:
    snapshot = _canonical_emission_snapshot()
    output_files = dict(snapshot.codex)
    relevant = {
        path: text
        for path, text in _text_files(snapshot.source).items()
        if _unescaped_skill_dir_count(text) and BLOCK_DELIMITER_START not in text
    }
    failures = tuple(
        (
            path,
            _escaped_skill_dir_count(text),
            _unescaped_skill_dir_count(text),
            _decode_text(output_files[path]).count(CLAUDE_SKILL_DIR_TOKEN),
            _decode_text(output_files[path]).count(CODEX_SKILL_DIR_TOKEN),
        )
        for path, text in relevant.items()
        if _decode_text(output_files[path]).count(CLAUDE_SKILL_DIR_TOKEN)
        != _escaped_skill_dir_count(text)
        or _decode_text(output_files[path]).count(CODEX_SKILL_DIR_TOKEN)
        < _unescaped_skill_dir_count(text)
    )
    synthetic = _synthetic_skill_dir_translation_holds()
    if not relevant or failures or not synthetic:
        raise AssertionError(
            f"Codex skill-directory rewrite mismatch: {failures=}, {synthetic=}"
        )
    return True


def skill_dir_escape_preserves_authoring_guidance() -> bool:
    snapshot = _canonical_emission_snapshot()
    source_files = _text_files(snapshot.source)
    relevant = {
        path: text
        for path, text in source_files.items()
        if SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE in text
    }
    claude_outputs = dict(snapshot.claude)
    codex_outputs = dict(snapshot.codex)
    return (
        bool(relevant)
        and all(
            _decode_text(claude_outputs[path]).count(CLAUDE_SKILL_DIR_TOKEN)
            >= _escaped_skill_dir_count(text) + _unescaped_skill_dir_count(text)
            and _decode_text(codex_outputs[path]).count(CLAUDE_SKILL_DIR_TOKEN)
            == _escaped_skill_dir_count(text)
            and SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE
            not in _decode_text(claude_outputs[path])
            and SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE
            not in _decode_text(codex_outputs[path])
            for path, text in relevant.items()
        )
        and _synthetic_skill_dir_translation_holds()
    )


def codex_skill_frontmatter_strips_claude_fields() -> bool:
    snapshot = _canonical_emission_snapshot()
    skill_sources = {
        path: text
        for path, text in _text_files(snapshot.source).items()
        if len(path.parts) > 2
        and path.parts[1] == SKILLS_SUBDIR_NAME
        and path.name == SKILL_FILENAME
    }
    canonical_holds = _frontmatter_contract_holds(
        skill_sources,
        claude_outputs=dict(snapshot.claude),
        codex_outputs=dict(snapshot.codex),
        required_portable_fields=frozenset((ALLOWED_TOOLS_FIELD, ARGUMENT_HINT_FIELD)),
        required_claude_only_fields=frozenset(),
    )
    synthetic = _synthetic_emission_snapshot()
    synthetic_skill_sources = {
        path: text
        for path, text in _text_files(synthetic.source).items()
        if len(path.parts) > 2
        and path.parts[1] == SKILLS_SUBDIR_NAME
        and path.name == SKILL_FILENAME
    }
    return canonical_holds and _frontmatter_contract_holds(
        synthetic_skill_sources,
        claude_outputs=dict(synthetic.claude),
        codex_outputs=dict(synthetic.codex),
        required_portable_fields=frozenset((ALLOWED_TOOLS_FIELD, ARGUMENT_HINT_FIELD)),
        required_claude_only_fields=frozenset((DISABLE_MODEL_INVOCATION_FIELD,)),
    )


def codex_command_frontmatter_strips_claude_fields() -> bool:
    return all(_command_frontmatter_translates(case) for case in source_scenarios())


def path_rewrite_is_idempotent() -> bool:
    return all(_path_rewrite_is_idempotent(case) for case in source_scenarios())


def frontmatter_strip_is_idempotent() -> bool:
    return all(_frontmatter_strip_is_idempotent(case) for case in source_scenarios())


def outputs_exclude_execution_time_injection() -> bool:
    token = EXECUTION_TIME_INJECTION_TOKEN.encode()
    snapshot = _canonical_emission_snapshot()
    return all(
        token not in content
        for target in Target
        for _path, content in snapshot.target(target)
    ) and all(
        token not in content
        for target in Target
        for _path, content in _synthetic_emission_snapshot().target(target)
    )


@cache
def _canonical_emission_snapshot() -> TargetEmissionSnapshot:
    source = _authored_plugin_snapshot(CANONICAL_SOURCE_ROOT)
    plan = plan_emissions(CANONICAL_SOURCE_ROOT)
    with TemporaryDirectory() as temporary_directory:
        dist_root = Path(temporary_directory) / DIST_DIR_NAME
        build(CANONICAL_SOURCE_ROOT, dist_root)
        outputs = {
            target: tuple(
                (Path(path), content)
                for path, content in snapshot_files(dist_root / target.value)
            )
            for target in Target
        }
    return TargetEmissionSnapshot(
        source=source,
        claude=outputs[Target.CLAUDE],
        codex=outputs[Target.CODEX],
        plan=plan,
    )


def _authored_plugin_snapshot(src_root: Path) -> PathSnapshot:
    plugins_root = src_root / PLUGINS_DIR_NAME
    return tuple(
        sorted(
            (path.relative_to(plugins_root), path.read_bytes())
            for path in plugins_root.rglob("*")
            if path.is_file()
            and not IGNORED_SOURCE_DIRECTORY_NAMES.intersection(
                path.relative_to(plugins_root).parts
            )
            and path.relative_to(plugins_root).suffix
            not in IGNORED_SOURCE_FILE_SUFFIXES
        )
    )


def _planned_paths(plan: BuildPlan, target: Target) -> set[Path]:
    return {emission.relative_path for emission in plan.for_target(target)}


@cache
def _synthetic_emission_snapshot() -> TargetEmissionSnapshot:
    case = min(source_scenarios(), key=lambda scenario: scenario.skill_ref)
    source_body = "\n".join(
        (
            _frontmatter_source(case),
            _claude_reference(case),
            f"{_claude_reference(case)} {SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE}",
            format_directive(
                IncludeDirective(
                    f"{case.scope}/{case.inner_topic}/{SHARED_FRAGMENT_FILENAME}"
                )
            ),
        )
    )
    artifact_filename = f"{case.cycle_topic}{COMMAND_FILE_SUFFIX}"
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory) / min(IGNORED_SOURCE_DIRECTORY_NAMES)
        builder = SrcTreeBuilder(root)
        builder.add_shared_topic(
            case.scope,
            case.inner_topic,
            case.fragment_body,
            references={f"{case.outer_topic}{COMMAND_FILE_SUFFIX}": case.fragment_body},
        )
        builder.add_plugin(
            case.plugin,
            skills={case.skill: source_body},
            commands={case.inner_topic: source_body},
            agents={case.outer_topic: source_body},
            artifacts={
                Path(artifact_filename): source_body.encode(),
                **{
                    Path(subdir, artifact_filename): source_body.encode()
                    for subdir in PLUGIN_SUBDIRS
                },
            },
        )
        plan = plan_emissions(builder.src_root)
        source = _authored_plugin_snapshot(builder.src_root)
        dist_root = root / DIST_DIR_NAME
        build(builder.src_root, dist_root)
        outputs = {
            target: tuple(
                (Path(path), content)
                for path, content in snapshot_files(dist_root / target.value)
            )
            for target in Target
        }
    return TargetEmissionSnapshot(
        source=source,
        claude=outputs[Target.CLAUDE],
        codex=outputs[Target.CODEX],
        plan=plan,
    )


def _synthetic_inventory_is_complete() -> bool:
    snapshot = _synthetic_emission_snapshot()
    source_paths = tuple(path for path, _content in snapshot.source)
    covered_subdirs = {path.parts[1] for path in source_paths if len(path.parts) > 2}
    direct_outputs = {
        target: Counter(
            emission.relative_path
            for emission in snapshot.plan.for_target(target)
            if emission.action is not EmissionAction.FAN_OUT
        )
        for target in Target
    }
    return (
        covered_subdirs == PLUGIN_SUBDIRS
        and any(len(path.parts) == 2 for path in source_paths)
        and any(
            emission.action is EmissionAction.FAN_OUT
            for emission in snapshot.plan.emissions
        )
        and all(
            direct_outputs[target] == Counter({path: 1 for path in source_paths})
            and _planned_paths(snapshot.plan, target)
            == {path for path, _content in snapshot.target(target)}
            for target in Target
        )
    )


def _synthetic_skill_dir_translation_holds() -> bool:
    snapshot = _synthetic_emission_snapshot()
    claude_outputs = dict(snapshot.claude)
    codex_outputs = dict(snapshot.codex)
    relevant = {
        path: text
        for path, text in _text_files(snapshot.source).items()
        if CLAUDE_SKILL_DIR_TOKEN in text
    }
    return bool(relevant) and all(
        _decode_text(claude_outputs[path]).count(CLAUDE_SKILL_DIR_TOKEN)
        == text.count(CLAUDE_SKILL_DIR_TOKEN)
        and _decode_text(codex_outputs[path]).count(CLAUDE_SKILL_DIR_TOKEN)
        == _escaped_skill_dir_count(text)
        and _decode_text(codex_outputs[path]).count(CODEX_SKILL_DIR_TOKEN)
        == _unescaped_skill_dir_count(text)
        and SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE not in _decode_text(claude_outputs[path])
        and SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE not in _decode_text(codex_outputs[path])
        for path, text in relevant.items()
    )


def _parent_directories(snapshot: PathSnapshot) -> set[Path]:
    return {
        parent
        for path, _content in snapshot
        for parent in path.parents
        if parent != Path()
    }


def _text_files(snapshot: PathSnapshot) -> dict[Path, str]:
    return {
        path: _decode_text(content)
        for path, content in snapshot
        if path.suffix in TEXT_FILE_SUFFIXES
    }


def _decode_text(content: bytes) -> str:
    return content.decode("utf-8")


def _unescaped_skill_dir_count(text: str) -> int:
    return sum(
        line.count(CLAUDE_SKILL_DIR_TOKEN)
        for line in text.splitlines()
        if SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE not in line
    )


def _escaped_skill_dir_count(text: str) -> int:
    return sum(
        line.count(CLAUDE_SKILL_DIR_TOKEN)
        for line in text.splitlines()
        if SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE in line
    )


def _frontmatter_contract_holds(
    sources: dict[Path, str],
    *,
    claude_outputs: dict[Path, bytes],
    codex_outputs: dict[Path, bytes],
    required_portable_fields: frozenset[str],
    required_claude_only_fields: frozenset[str],
) -> bool:
    portable_coverage = {field: False for field in required_portable_fields}
    claude_only_coverage = {field: False for field in required_claude_only_fields}
    for path in sources:
        claude_output = _decode_text(claude_outputs[path])
        codex_output = _decode_text(codex_outputs[path])
        claude_fields = frontmatter_field_names(claude_output)
        codex_fields = frontmatter_field_names(codex_output)
        for field in required_portable_fields:
            if field not in claude_fields:
                continue
            portable_coverage[field] = True
            if field not in codex_fields:
                raise AssertionError(
                    f"portable field {field!r} missing for {path}: "
                    f"{claude_fields=}, {codex_fields=}"
                )
        for field in required_claude_only_fields:
            if field not in claude_fields:
                continue
            claude_only_coverage[field] = True
            if field in codex_fields:
                raise AssertionError(
                    f"Claude-only field {field!r} translated incorrectly for {path}: "
                    f"{claude_fields=}, {codex_fields=}"
                )
    missing_portable = {
        field
        for field in required_portable_fields
        if not portable_coverage.get(field, False)
    }
    missing_claude_only = {
        field
        for field in required_claude_only_fields
        if not claude_only_coverage.get(field, False)
    }
    if missing_portable or missing_claude_only:
        raise AssertionError(
            "frontmatter coverage incomplete: "
            f"{missing_portable=}, {missing_claude_only=}"
        )
    return True


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
    reference = _claude_reference(case)
    once = rewrite_paths_for_target(reference, target=Target.CODEX)
    return rewrite_paths_for_target(once, target=Target.CODEX) == once


def _frontmatter_strip_is_idempotent(case: SourceScenario) -> bool:
    once = strip_frontmatter_fields(
        _frontmatter_source(case),
        fields=CLAUDE_ONLY_FRONTMATTER_FIELDS,
    )
    return strip_frontmatter_fields(once, fields=CLAUDE_ONLY_FRONTMATTER_FIELDS) == once


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
    return f"{CLAUDE_SKILL_DIR_TOKEN}/{case.outer_topic}{COMMAND_FILE_SUFFIX}"


def _frontmatter_source(case: SourceScenario) -> str:
    claude_fields = f"{DISABLE_MODEL_INVOCATION_FIELD}: true"
    portable_fields = "\n".join(
        f"{field}: {case.outer_topic}"
        for field in (ALLOWED_TOOLS_FIELD, ARGUMENT_HINT_FIELD)
    )
    return f"---\n{claude_fields}\n{portable_fields}\n---\n{case.fragment_body}"


def _frontmatter_translation_holds(claude_body: str, codex_body: str) -> bool:
    claude_fields = frontmatter_field_names(claude_body)
    codex_fields = frontmatter_field_names(codex_body)
    return (
        DISABLE_MODEL_INVOCATION_FIELD in claude_fields
        and DISABLE_MODEL_INVOCATION_FIELD not in codex_fields
    ) and all(
        field in claude_fields and field in codex_fields
        for field in (ALLOWED_TOOLS_FIELD, ARGUMENT_HINT_FIELD)
    )
