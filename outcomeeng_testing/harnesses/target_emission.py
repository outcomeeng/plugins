"""Full-tree observations for target-emission evidence."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.build import (
    AGENT_CAPABILITY_REGISTRY,
    PLACEMENT_MANIFEST_FILENAME,
    BuildPlan,
    CLAUDE_ONLY_FRONTMATTER_FIELDS,
    CLAUDE_SKILL_DIR_TOKEN,
    CODEX_SKILL_DIR_TOKEN,
    DISABLE_MODEL_INVOCATION_FIELD,
    EmissionAction,
    EXECUTION_TIME_INJECTION_END,
    EXECUTION_TIME_INJECTION_START,
    IGNORED_SOURCE_DIRECTORY_NAMES,
    IGNORED_SOURCE_FILE_SUFFIXES,
    SHARED_FRAGMENT_FILENAME,
    SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE,
    IncludeDirective,
    build,
    contains_execution_time_skill_content_injection,
    format_directive,
    frontmatter_field_names,
    plan_emissions,
    render_planned_emission_text,
    render_text,
    rewrite_paths_for_target,
    skill_dir_path_references,
    strip_frontmatter_fields,
)
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    BUILD_TARGET_VARIABLE,
    DIST_DIR_NAME,
    MARKDOWN_FILE_SUFFIX,
    PLUGINS_DIR_NAME,
    PLUGIN_SUBDIRS,
    REFERENCES_SUBDIR_NAME,
    SKILL_FILENAME,
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
    TargetScopedIncludeCase,
    source_scenarios,
    target_scoped_include_cases,
)
from outcomeeng_testing.harnesses.distribution import (
    CANONICAL_SOURCE_ROOT,
    REPOSITORY_ROOT,
    snapshot_files,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

type PathSnapshot = tuple[tuple[Path, bytes], ...]

# Actions whose output is the rendered source text, so a caller may compare the
# two directly. A converted agent and a placement manifest are derived artifacts
# whose output is not their source's rendered text, so they are excluded.
_SOURCE_TEXT_ACTIONS = frozenset({EmissionAction.RENDER, EmissionAction.COPY})


@dataclass(frozen=True)
class TargetEmissionSnapshot:
    """Canonical source files and the outputs emitted from them."""

    source: PathSnapshot
    claude: PathSnapshot
    codex: PathSnapshot
    plan: BuildPlan
    src_root: Path

    def target(self, target: Target) -> PathSnapshot:
        return self.claude if target is Target.CLAUDE else self.codex


def source_emission_counts() -> dict[Target, Counter[Path]]:
    """Return how many direct outputs each source produces, per target.

    A source normally produces one output per target tree. A per-plugin
    template produces one per plugin, so the count is a coverage observation
    rather than a verdict: the caller owns the predicate over it.
    """
    snapshot = _canonical_emission_snapshot()
    return {
        target: Counter(
            emission.source
            for emission in snapshot.plan.for_target(target)
            if emission.action is not EmissionAction.FAN_OUT
        )
        for target in Target
    }


def planned_sources() -> tuple[Path, ...]:
    """Return every source the canonical plan emits from, including templates."""
    snapshot = _canonical_emission_snapshot()
    return tuple(sorted({emission.source for emission in snapshot.plan.emissions}))


def planned_matches_emitted() -> dict[Target, bool]:
    """Return whether each target's planned paths equal what the build wrote."""
    snapshot = _canonical_emission_snapshot()
    return {
        target: _planned_paths(snapshot.plan, target)
        == {path for path, _content in snapshot.target(target)}
        and _planned_directories(snapshot.plan, target)
        == _parent_directories(snapshot.target(target))
        for target in Target
    }


def structure_deviations() -> dict[Target, tuple[Path, ...]]:
    """Return each target's outputs whose path is not its source's mirror.

    A deviation is expected only where the target's agent capability directs an
    artifact class elsewhere; the caller owns that predicate.
    """
    snapshot = _canonical_emission_snapshot()
    plugins_root = CANONICAL_SOURCE_ROOT / PLUGINS_DIR_NAME
    deviations: dict[Target, tuple[Path, ...]] = {}
    for target in Target:
        found: list[Path] = []
        for emission in snapshot.plan.for_target(target):
            if emission.action is EmissionAction.FAN_OUT:
                continue
            if not emission.source.is_relative_to(plugins_root):
                continue
            if emission.relative_path != emission.source.relative_to(plugins_root):
                found.append(emission.relative_path)
        deviations[target] = tuple(sorted(found))
    return deviations


def agent_artifact_paths(target: Target) -> tuple[Path, ...]:
    """Return every agent artifact one generated target tree carries.

    Reads the committed tree rather than the plan, so the observation reflects
    what a consumer installs rather than what the build intended.
    """
    tree = REPOSITORY_ROOT / DIST_DIR_NAME / target.value
    capability = AGENT_CAPABILITY_REGISTRY[target.value]
    if capability.manifest_declares_agents:
        return tuple(sorted(tree.glob(f"*/{AGENTS_SUBDIR_NAME}/*")))
    return tuple(
        sorted(
            path
            for path in tree.glob(f"*/{SKILLS_SUBDIR_NAME}/*/{AGENTS_SUBDIR_NAME}/*")
            if path.name != PLACEMENT_MANIFEST_FILENAME
        )
    )


def synthetic_inventory_is_complete() -> bool:
    """Return whether the synthetic fixture covers every emission behavior."""
    return _synthetic_inventory_is_complete()


def repeated_include_emits_shared_source_once() -> bool:
    failures = tuple(
        failure
        for case in source_scenarios()
        for failure in _repeated_include_failures(case)
    )
    if failures:
        raise AssertionError(f"repeated include emission mismatch: {failures}")
    return True


def claude_output_preserves_skill_dir_token() -> bool:
    snapshot = _canonical_emission_snapshot()
    output_files = dict(snapshot.claude)
    rendered_sources = _canonical_rendered_emissions(snapshot.plan, Target.CLAUDE)
    expected = {
        path: _skill_dir_reference_counter(text, CLAUDE_SKILL_DIR_TOKEN)
        for path, text in rendered_sources.items()
    }
    failures = tuple(
        (
            path,
            references,
            _skill_dir_reference_counter(
                _decode_text(output_files[path]),
                CLAUDE_SKILL_DIR_TOKEN,
            ),
        )
        for path, references in expected.items()
        if _skill_dir_reference_counter(
            _decode_text(output_files[path]),
            CLAUDE_SKILL_DIR_TOKEN,
        )
        != references
    )
    synthetic = (
        _synthetic_skill_dir_translation_holds()
        and _synthetic_fan_out_translation_holds()
    )
    if not any(expected.values()) or failures or not synthetic:
        raise AssertionError(
            f"Claude skill-directory preservation mismatch: {failures=}, {synthetic=}"
        )
    return True


def codex_output_rewrites_skill_dir_token() -> bool:
    snapshot = _canonical_emission_snapshot()
    output_files = dict(snapshot.codex)
    rendered_sources = _canonical_rendered_emissions(snapshot.plan, Target.CODEX)
    expected = {
        path: (
            _escaped_skill_dir_references(text),
            _translated_codex_references(_unescaped_skill_dir_references(text)),
        )
        for path, text in rendered_sources.items()
    }
    failures = tuple(
        (
            path,
            expected_claude,
            expected_codex,
            _skill_dir_reference_counter(
                _decode_text(output_files[path]),
                CLAUDE_SKILL_DIR_TOKEN,
            ),
            _skill_dir_reference_counter(
                _decode_text(output_files[path]),
                CODEX_SKILL_DIR_TOKEN,
            ),
        )
        for path, (expected_claude, expected_codex) in expected.items()
        if (
            _skill_dir_reference_counter(
                _decode_text(output_files[path]),
                CLAUDE_SKILL_DIR_TOKEN,
            )
            != expected_claude
            or _skill_dir_reference_counter(
                _decode_text(output_files[path]),
                CODEX_SKILL_DIR_TOKEN,
            )
            != expected_codex
            or _decode_text(output_files[path]).count(CLAUDE_SKILL_DIR_TOKEN)
            != _escaped_skill_dir_token_count(rendered_sources[path])
        )
    )
    synthetic = (
        _synthetic_skill_dir_translation_holds()
        and _synthetic_fan_out_translation_holds()
    )
    if (
        not any(
            expected_codex for _expected_claude, expected_codex in expected.values()
        )
        or failures
        or not synthetic
    ):
        raise AssertionError(
            f"Codex skill-directory rewrite mismatch: {failures=}, {synthetic=}"
        )
    return True


def skill_dir_escape_preserves_authoring_guidance() -> bool:
    snapshot = _canonical_emission_snapshot()
    claude_sources = _canonical_rendered_emissions(snapshot.plan, Target.CLAUDE)
    codex_sources = _canonical_rendered_emissions(snapshot.plan, Target.CODEX)
    claude_expected = {
        path: _escaped_skill_dir_references(text)
        for path, text in claude_sources.items()
    }
    codex_expected = {
        path: _escaped_skill_dir_references(text)
        for path, text in codex_sources.items()
    }
    relevant_paths = {
        path
        for expected in (claude_expected, codex_expected)
        for path, references in expected.items()
        if references
    }
    claude_outputs = dict(snapshot.claude)
    codex_outputs = dict(snapshot.codex)
    return (
        bool(relevant_paths)
        and all(
            claude_expected[path]
            <= _skill_dir_reference_counter(
                _decode_text(claude_outputs[path]),
                CLAUDE_SKILL_DIR_TOKEN,
            )
            and codex_expected[path]
            == _skill_dir_reference_counter(
                _decode_text(codex_outputs[path]),
                CLAUDE_SKILL_DIR_TOKEN,
            )
            and SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE
            not in _decode_text(claude_outputs[path])
            and SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE
            not in _decode_text(codex_outputs[path])
            for path in relevant_paths
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
    ) and _frontmatter_fields_are_absent(
        _text_files(snapshot.codex),
        forbidden_fields=frozenset(CLAUDE_ONLY_FRONTMATTER_FIELDS),
    )
    synthetic = _synthetic_emission_snapshot()
    synthetic_skill_sources = {
        path: text
        for path, text in _text_files(synthetic.source).items()
        if len(path.parts) > 2
        and path.parts[1] == SKILLS_SUBDIR_NAME
        and path.name == SKILL_FILENAME
    }
    return (
        canonical_holds
        and _frontmatter_contract_holds(
            synthetic_skill_sources,
            claude_outputs=dict(synthetic.claude),
            codex_outputs=dict(synthetic.codex),
            required_portable_fields=frozenset(
                (ALLOWED_TOOLS_FIELD, ARGUMENT_HINT_FIELD)
            ),
            required_claude_only_fields=frozenset((DISABLE_MODEL_INVOCATION_FIELD,)),
        )
        and _synthetic_fan_out_translation_holds()
    )


def target_scoped_includes_emit_only_to_matching_tree() -> bool:
    failures: list[str] = []
    for case in target_scoped_include_cases():
        if not _nonmatching_target_skips_absent_include(case):
            failures.append(
                f"{case.source.skill_ref}:{case.placement.value}:"
                f"{case.target.value}:resolved-dead-branch"
            )
        with TemporaryDirectory() as temporary_directory:
            builder = SrcTreeBuilder(Path(temporary_directory))
            builder.add_shared_topic(
                case.source.scope,
                case.source.inner_topic,
                case.source.fragment_body,
                references={case.reference_filename: case.source.fragment_body},
            )
            if case.outer_fragment_body is not None:
                builder.add_shared_topic(
                    case.source.scope,
                    case.source.outer_topic,
                    case.outer_fragment_body,
                )
            builder.add_plugin(
                case.source.plugin,
                skills={
                    case.source.skill: "\n".join(
                        (_frontmatter_source(case.source), case.root_body)
                    )
                },
            )
            plan = plan_emissions(builder.src_root)
        for target in Target:
            emitted = case.expected_relative_path in _planned_paths(plan, target)
            if emitted == (target is case.target):
                continue
            failures.append(
                f"{case.source.skill_ref}:{case.placement.value}:"
                f"{case.target.value}:{target.value}:{emitted}"
            )
    if failures:
        raise AssertionError(f"target-scoped include fan-out mismatch: {failures}")
    return True


def _nonmatching_target_skips_absent_include(case: TargetScopedIncludeCase) -> bool:
    nonmatching_target = next(target for target in Target if target is not case.target)
    with TemporaryDirectory() as temporary_directory:
        builder = SrcTreeBuilder(Path(temporary_directory))
        if case.outer_fragment_body is None:
            builder.shared_root.mkdir(parents=True)
        else:
            builder.add_shared_topic(
                case.source.scope,
                case.source.outer_topic,
                case.outer_fragment_body,
            )
        return (
            render_text(
                case.root_body,
                shared_root=builder.shared_root,
                variables={BUILD_TARGET_VARIABLE: nonmatching_target.value},
            )
            == ""
        )


def path_rewrite_is_idempotent() -> bool:
    return all(_path_rewrite_is_idempotent(case) for case in source_scenarios())


def frontmatter_strip_is_idempotent() -> bool:
    return all(_frontmatter_strip_is_idempotent(case) for case in source_scenarios())


def outputs_exclude_execution_time_injection() -> bool:
    snapshot = _canonical_emission_snapshot()
    return (
        _execution_time_injection_detector_covers_generated_commands()
        and all(
            not contains_execution_time_skill_content_injection(text)
            for target in Target
            for text in _text_files(snapshot.target(target)).values()
        )
        and all(
            not contains_execution_time_skill_content_injection(text)
            for target in Target
            for text in _text_files(
                _synthetic_emission_snapshot().target(target)
            ).values()
        )
    )


def _execution_time_injection_detector_covers_generated_commands() -> bool:
    return all(
        contains_execution_time_skill_content_injection(
            f"{EXECUTION_TIME_INJECTION_START}{command}{EXECUTION_TIME_INJECTION_END}"
        )
        and not contains_execution_time_skill_content_injection(command)
        for case in source_scenarios()
        for command in _execution_time_commands(case)
    )


def _execution_time_commands(case: SourceScenario) -> tuple[str, ...]:
    reference_name = f"{case.outer_topic}{MARKDOWN_FILE_SUFFIX}"
    sibling_paths = (
        f"../{case.skill}/{SKILL_FILENAME}",
        f"../{case.skill}/*",
        f"../{case.skill}/{REFERENCES_SUBDIR_NAME}/{reference_name}",
    )
    return (
        *(f"{case.inner_topic} {path}" for path in sibling_paths),
        *(
            f"{case.inner_topic} {skill_dir_token}/{path}"
            for skill_dir_token in (CLAUDE_SKILL_DIR_TOKEN, CODEX_SKILL_DIR_TOKEN)
            for path in sibling_paths
        ),
    )


@cache
def _canonical_emission_snapshot() -> TargetEmissionSnapshot:
    source = _authored_plugin_snapshot(CANONICAL_SOURCE_ROOT)
    plan = plan_emissions(CANONICAL_SOURCE_ROOT)
    dist_root = REPOSITORY_ROOT / DIST_DIR_NAME
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
        src_root=CANONICAL_SOURCE_ROOT,
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


def _planned_directories(plan: BuildPlan, target: Target) -> set[Path]:
    return {
        parent
        for path in _planned_paths(plan, target)
        for parent in path.parents
        if parent != Path()
    }


@cache
def _synthetic_emission_snapshot() -> TargetEmissionSnapshot:
    case = min(source_scenarios(), key=lambda scenario: scenario.skill_ref)
    fan_out_body = "\n".join((_frontmatter_source(case), _claude_reference(case)))
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
    artifact_filename = f"{case.cycle_topic}{MARKDOWN_FILE_SUFFIX}"
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory) / min(IGNORED_SOURCE_DIRECTORY_NAMES)
        builder = SrcTreeBuilder(root)
        builder.add_shared_topic(
            case.scope,
            case.inner_topic,
            case.fragment_body,
            references={f"{case.outer_topic}{MARKDOWN_FILE_SUFFIX}": fan_out_body},
        )
        builder.add_plugin(
            case.plugin,
            skills={case.skill: source_body},
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
        src_root=builder.src_root,
    )


def _synthetic_inventory_is_complete() -> bool:
    snapshot = _synthetic_emission_snapshot()
    source_paths = tuple(path for path, _content in snapshot.source)
    covered_subdirs = {path.parts[1] for path in source_paths if len(path.parts) > 2}
    plugins_root = snapshot.src_root / PLUGINS_DIR_NAME
    direct_outputs = {
        target: Counter(
            emission.source.relative_to(plugins_root)
            for emission in snapshot.plan.for_target(target)
            if emission.action is not EmissionAction.FAN_OUT
            and emission.source.is_relative_to(plugins_root)
        )
        for target in Target
    }
    covered_actions = {emission.action for emission in snapshot.plan.emissions}
    return (
        covered_subdirs == PLUGIN_SUBDIRS
        and any(len(path.parts) == 2 for path in source_paths)
        and {
            EmissionAction.FAN_OUT,
            EmissionAction.CONVERT_AGENT,
            EmissionAction.PLACEMENT_MANIFEST,
        }
        <= covered_actions
        and all(
            all(direct_outputs[target][path] >= 1 for path in source_paths)
            and _planned_paths(snapshot.plan, target)
            == {path for path, _content in snapshot.target(target)}
            for target in Target
        )
    )


def _repeated_include_failures(case: SourceScenario) -> tuple[str, ...]:
    reference_filename = f"{case.outer_topic}{MARKDOWN_FILE_SUFFIX}"
    directive = format_directive(
        IncludeDirective(f"{case.scope}/{case.inner_topic}/{SHARED_FRAGMENT_FILENAME}")
    )
    with TemporaryDirectory() as temporary_directory:
        builder = SrcTreeBuilder(Path(temporary_directory))
        builder.add_shared_topic(
            case.scope,
            case.inner_topic,
            case.fragment_body,
            references={reference_filename: case.fragment_body},
        )
        builder.add_plugin(
            case.plugin,
            skills={case.skill: "\n".join((directive, directive))},
        )
        reference_source = (
            builder.shared_root
            / case.scope
            / case.inner_topic
            / REFERENCES_SUBDIR_NAME
            / reference_filename
        ).resolve()
        plan = plan_emissions(builder.src_root)
    counts = {
        target: sum(
            emission.source == reference_source for emission in plan.for_target(target)
        )
        for target in Target
    }
    return tuple(
        f"{case.skill_ref}:{target.value}:{count}"
        for target, count in counts.items()
        if count != 1
    )


def _outputs_by_source_path(
    snapshot: TargetEmissionSnapshot,
    target: Target,
) -> dict[Path, bytes]:
    """Return one target's outputs keyed by their source's mirrored path.

    An agent artifact a target reads from elsewhere is keyed by the source path
    it came from, so a caller comparing source text to output text does not have
    to know where the capability registry directed it.
    """
    outputs = dict(snapshot.target(target))
    by_source: dict[Path, bytes] = {}
    plugins_root = snapshot.src_root / PLUGINS_DIR_NAME
    for emission in snapshot.plan.for_target(target):
        if emission.action not in _SOURCE_TEXT_ACTIONS:
            continue
        if emission.relative_path not in outputs:
            continue
        if not emission.source.is_relative_to(plugins_root):
            continue
        by_source[emission.source.relative_to(plugins_root)] = outputs[
            emission.relative_path
        ]
    return by_source


def _synthetic_skill_dir_translation_holds() -> bool:
    snapshot = _synthetic_emission_snapshot()
    claude_outputs = _outputs_by_source_path(snapshot, Target.CLAUDE)
    codex_outputs = _outputs_by_source_path(snapshot, Target.CODEX)
    relevant = {
        path: text
        for path, text in _text_files(snapshot.source).items()
        if CLAUDE_SKILL_DIR_TOKEN in text and path in codex_outputs
    }
    return bool(relevant) and all(
        _skill_dir_reference_counter(
            _decode_text(claude_outputs[path]),
            CLAUDE_SKILL_DIR_TOKEN,
        )
        == _skill_dir_reference_counter(text, CLAUDE_SKILL_DIR_TOKEN)
        and _skill_dir_reference_counter(
            _decode_text(codex_outputs[path]),
            CLAUDE_SKILL_DIR_TOKEN,
        )
        == _escaped_skill_dir_references(text)
        and _skill_dir_reference_counter(
            _decode_text(codex_outputs[path]),
            CODEX_SKILL_DIR_TOKEN,
        )
        == _translated_codex_references(_unescaped_skill_dir_references(text))
        and SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE not in _decode_text(claude_outputs[path])
        and SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE not in _decode_text(codex_outputs[path])
        for path, text in relevant.items()
    )


def _synthetic_fan_out_translation_holds() -> bool:
    snapshot = _synthetic_emission_snapshot()
    case = min(source_scenarios(), key=lambda scenario: scenario.skill_ref)
    expected_claude = Counter((_claude_reference(case),))
    expected_codex = _translated_codex_references(expected_claude)
    fan_out_paths = {
        emission.relative_path
        for emission in snapshot.plan.for_target(Target.CLAUDE)
        if emission.action is EmissionAction.FAN_OUT
    }
    claude_outputs = dict(snapshot.claude)
    codex_outputs = dict(snapshot.codex)
    return bool(fan_out_paths) and all(
        _skill_dir_reference_counter(
            (claude_body := _decode_text(claude_outputs[path])),
            CLAUDE_SKILL_DIR_TOKEN,
        )
        == expected_claude
        and _skill_dir_reference_counter(
            (codex_body := _decode_text(codex_outputs[path])),
            CLAUDE_SKILL_DIR_TOKEN,
        )
        == Counter()
        and _skill_dir_reference_counter(codex_body, CODEX_SKILL_DIR_TOKEN)
        == expected_codex
        and _frontmatter_translation_holds(claude_body, codex_body)
        for path in fan_out_paths
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


def _canonical_rendered_emissions(
    plan: BuildPlan,
    target: Target,
) -> dict[Path, str]:
    return {
        emission.relative_path: render_planned_emission_text(
            emission,
            src_root=CANONICAL_SOURCE_ROOT,
        )
        for emission in plan.for_target(target)
        if emission.source.suffix in TEXT_FILE_SUFFIXES
        and emission.action in _SOURCE_TEXT_ACTIONS
    }


def _skill_dir_reference_counter(text: str, token: str) -> Counter[str]:
    return Counter(skill_dir_path_references(text, token))


def _unescaped_skill_dir_references(text: str) -> Counter[str]:
    return Counter(
        reference
        for line in text.splitlines()
        if SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE not in line
        for reference in skill_dir_path_references(line, CLAUDE_SKILL_DIR_TOKEN)
    )


def _escaped_skill_dir_references(text: str) -> Counter[str]:
    return Counter(
        reference
        for line in text.splitlines()
        if SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE in line
        for reference in skill_dir_path_references(line, CLAUDE_SKILL_DIR_TOKEN)
    )


def _escaped_skill_dir_token_count(text: str) -> int:
    return sum(
        line.count(CLAUDE_SKILL_DIR_TOKEN)
        for line in text.splitlines()
        if SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE in line
    )


def _translated_codex_references(references: Counter[str]) -> Counter[str]:
    return Counter(
        {
            reference.replace(CLAUDE_SKILL_DIR_TOKEN, CODEX_SKILL_DIR_TOKEN, 1): count
            for reference, count in references.items()
        }
    )


def _frontmatter_contract_holds(
    sources: dict[Path, str],
    *,
    claude_outputs: dict[Path, bytes],
    codex_outputs: dict[Path, bytes],
    required_portable_fields: frozenset[str],
    required_claude_only_fields: frozenset[str],
) -> bool:
    portable_coverage = dict.fromkeys(required_portable_fields, False)
    claude_only_coverage = dict.fromkeys(required_claude_only_fields, False)
    for path in sources:
        claude_output = _decode_text(claude_outputs[path])
        codex_output = _decode_text(codex_outputs[path])
        claude_fields = frontmatter_field_names(claude_output)
        codex_fields = frontmatter_field_names(codex_output)
        _record_portable_field_coverage(
            path,
            required_fields=required_portable_fields,
            claude_fields=claude_fields,
            codex_fields=codex_fields,
            coverage=portable_coverage,
        )
        _record_claude_only_field_coverage(
            path,
            required_fields=required_claude_only_fields,
            claude_fields=claude_fields,
            codex_fields=codex_fields,
            coverage=claude_only_coverage,
        )
    missing_portable = _missing_frontmatter_fields(portable_coverage)
    missing_claude_only = _missing_frontmatter_fields(claude_only_coverage)
    if missing_portable or missing_claude_only:
        raise AssertionError(
            "frontmatter coverage incomplete: "
            f"{missing_portable=}, {missing_claude_only=}"
        )
    return True


def _record_portable_field_coverage(
    path: Path,
    *,
    required_fields: frozenset[str],
    claude_fields: frozenset[str],
    codex_fields: frozenset[str],
    coverage: dict[str, bool],
) -> None:
    for field in required_fields & claude_fields:
        coverage[field] = True
        if field not in codex_fields:
            raise AssertionError(
                f"portable field {field!r} missing for {path}: "
                f"{claude_fields=}, {codex_fields=}"
            )


def _record_claude_only_field_coverage(
    path: Path,
    *,
    required_fields: frozenset[str],
    claude_fields: frozenset[str],
    codex_fields: frozenset[str],
    coverage: dict[str, bool],
) -> None:
    for field in required_fields & claude_fields:
        coverage[field] = True
        if field in codex_fields:
            raise AssertionError(
                f"Claude-only field {field!r} translated incorrectly for {path}: "
                f"{claude_fields=}, {codex_fields=}"
            )


def _missing_frontmatter_fields(coverage: dict[str, bool]) -> frozenset[str]:
    return frozenset(field for field, covered in coverage.items() if not covered)


def _frontmatter_fields_are_absent(
    outputs: dict[Path, str],
    *,
    forbidden_fields: frozenset[str],
) -> bool:
    failures = tuple(
        (path, forbidden_fields & fields)
        for path, text in outputs.items()
        if forbidden_fields & (fields := frontmatter_field_names(text))
    )
    if failures:
        raise AssertionError(f"forbidden frontmatter fields emitted: {failures=}")
    return True


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


def _claude_reference(case: SourceScenario) -> str:
    return f"{CLAUDE_SKILL_DIR_TOKEN}/{case.outer_topic}{MARKDOWN_FILE_SUFFIX}"


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
