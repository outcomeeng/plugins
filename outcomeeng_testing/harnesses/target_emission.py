"""Full-tree observations for target-emission evidence."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

import yaml

from outcomeeng.distribution.build import (
    AGENT_CAPABILITY_REGISTRY,
    EmissionProjection,
    CLAUDE_SKILL_DIR_TOKEN,
    DISABLE_MODEL_INVOCATION_FIELD,
    EmissionAction,
    IGNORED_SOURCE_DIRECTORY_NAMES,
    IGNORED_SOURCE_FILE_SUFFIXES,
    SHARED_FRAGMENT_FILENAME,
    SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE,
    IncludeDirective,
    build,
    format_directive,
    project_emissions,
    render_projected_emission_text,
    render_text,
)
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    BUILD_TARGET_VARIABLE,
    DIST_DIR_NAME,
    MARKDOWN_FILE_SUFFIX,
    PLUGINS_DIR_NAME,
    PLUGIN_SUBDIRS,
    REFERENCES_SUBDIR_NAME,
    SKILLS_SUBDIR_NAME,
    TEXT_FILE_SUFFIXES,
    RUNTIME_TOKEN_TOOL_KIND,
    RUNTIME_TOKEN_USE_SKILL_CAPABILITY,
    Target,
    format_runtime_token,
)
from outcomeeng.distribution.agents import READ_ONLY_TOOLS
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
# two directly. A converted agent is a derived artifact whose output is not its
# source's rendered text, so it is excluded.
_SOURCE_TEXT_ACTIONS = frozenset(
    {EmissionAction.RENDER, EmissionAction.COPY, EmissionAction.FAN_OUT}
)


@dataclass(frozen=True)
class TargetEmissionSnapshot:
    """Canonical source files and the outputs emitted from them."""

    source: PathSnapshot
    claude: PathSnapshot
    codex: PathSnapshot
    projection: EmissionProjection
    src_root: Path
    rendered_sources: dict[Target, dict[Path, str]]

    def target(self, target: Target) -> PathSnapshot:
        return self.claude if target is Target.CLAUDE else self.codex


def source_emission_counts() -> dict[Target, Counter[Path]]:
    """Return how many direct outputs each source produces, per target.

    A source normally produces one output per target tree. A per-plugin
    template produces one per plugin, so the count is a coverage observation
    rather than a verdict: the caller owns the predicate over it.

    Counts a source's own outputs — rendered, copied, or converted. A fanned-out
    shared fragment is a derived artifact attributed to a source it does not
    correspond one-to-one with, so counting it would conflate derivation with
    emission.
    """
    counted = {
        EmissionAction.RENDER,
        EmissionAction.COPY,
        EmissionAction.CONVERT_AGENT,
    }
    snapshot = _canonical_emission_snapshot()
    return {
        target: Counter(
            emission.source
            for emission in snapshot.projection.for_target(target)
            if emission.action in counted
        )
        for target in Target
    }


def projected_sources() -> tuple[Path, ...]:
    """Return every source the canonical projection emits from, including templates."""
    snapshot = _canonical_emission_snapshot()
    return tuple(
        sorted({emission.source for emission in snapshot.projection.emissions})
    )


@dataclass(frozen=True)
class ProjectedVersusEmitted:
    """One target's projected output inventory beside what the build wrote."""

    projected_paths: frozenset[Path]
    emitted_paths: frozenset[Path]
    projected_directories: frozenset[Path]
    emitted_directories: frozenset[Path]


def projected_versus_emitted() -> dict[Target, ProjectedVersusEmitted]:
    """Return each target's projected and emitted inventories, undecided.

    The caller compares them; this returns the two sets rather than their
    equality so the predicate stays in the test that links the assertion.
    """
    snapshot = _canonical_emission_snapshot()
    return {
        target: ProjectedVersusEmitted(
            projected_paths=frozenset(_projected_paths(snapshot.projection, target)),
            emitted_paths=frozenset(path for path, _content in snapshot.target(target)),
            projected_directories=frozenset(
                _projected_directories(snapshot.projection, target)
            ),
            emitted_directories=frozenset(_parent_directories(snapshot.target(target))),
        )
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
        for emission in snapshot.projection.for_target(target):
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

    Reads the committed tree rather than the projection, so the observation reflects
    what a consumer installs rather than what the build intended.
    """
    tree = REPOSITORY_ROOT / DIST_DIR_NAME / target.value
    capability = AGENT_CAPABILITY_REGISTRY[target.value]
    if capability.manifest_declares_agents:
        return tuple(sorted(tree.glob(f"*/{AGENTS_SUBDIR_NAME}/*")))
    return tuple(sorted(tree.glob(f"*/{SKILLS_SUBDIR_NAME}/*/{AGENTS_SUBDIR_NAME}/*")))


def agent_artifact_texts(target: Target) -> dict[Path, str]:
    """Read native agent artifacts without judging their content."""
    return {
        path: path.read_text(encoding="utf-8") for path in agent_artifact_paths(target)
    }


@dataclass(frozen=True)
class SyntheticInventory:
    """What the synthetic fixture covers, for the caller to judge."""

    covered_subdirs: frozenset[str]
    expected_subdirs: frozenset[str]
    covered_actions: frozenset[EmissionAction]
    source_paths: tuple[Path, ...]
    per_source_counts: dict[Target, Counter[Path]]
    projected_versus_emitted: dict[Target, ProjectedVersusEmitted]


def synthetic_inventory() -> SyntheticInventory:
    """Return the synthetic fixture's coverage observations, undecided."""
    snapshot = _synthetic_emission_snapshot()
    source_paths = tuple(path for path, _content in snapshot.source)
    plugins_root = snapshot.src_root / PLUGINS_DIR_NAME
    return SyntheticInventory(
        covered_subdirs=frozenset(
            path.parts[1] for path in source_paths if len(path.parts) > 2
        ),
        expected_subdirs=frozenset(PLUGIN_SUBDIRS),
        covered_actions=frozenset(
            emission.action for emission in snapshot.projection.emissions
        ),
        source_paths=source_paths,
        per_source_counts={
            target: Counter(
                emission.source.relative_to(plugins_root)
                for emission in snapshot.projection.for_target(target)
                if emission.action is not EmissionAction.FAN_OUT
                and emission.source.is_relative_to(plugins_root)
            )
            for target in Target
        },
        projected_versus_emitted={
            target: ProjectedVersusEmitted(
                projected_paths=frozenset(
                    _projected_paths(snapshot.projection, target)
                ),
                emitted_paths=frozenset(
                    path for path, _content in snapshot.target(target)
                ),
                projected_directories=frozenset(),
                emitted_directories=frozenset(),
            )
            for target in Target
        },
    )


@dataclass(frozen=True)
class TextEmission:
    """Rendered source and emitted output before the linked test judges them."""

    target: Target
    path: Path
    source: str
    output: str


@cache
def text_emissions() -> tuple[TextEmission, ...]:
    """Expose canonical, constructed and fan-out text without verdicts."""
    return tuple(
        TextEmission(target, path, source, outputs[path].decode("utf-8"))
        for snapshot in (_canonical_emission_snapshot(), _synthetic_emission_snapshot())
        for target in Target
        for outputs in (dict(snapshot.target(target)),)
        for path, source in snapshot.rendered_sources[target].items()
    )


@dataclass(frozen=True)
class EmittedText:
    target: Target
    path: Path
    text: str


@dataclass(frozen=True)
class OptionalToolEmission:
    """One built target's independently parsed optional-tool list."""

    target: Target
    tools: tuple[str, ...]
    text: str


def optional_tool_emissions() -> tuple[OptionalToolEmission, ...]:
    """Build an optional tool between stable list items for every target."""
    case = min(source_scenarios(), key=lambda scenario: scenario.skill_ref)
    stable_tools = tuple(sorted(READ_ONLY_TOOLS))
    token = format_runtime_token(
        RUNTIME_TOKEN_TOOL_KIND,
        RUNTIME_TOKEN_USE_SKILL_CAPABILITY,
    )
    items = (stable_tools[0], token, *stable_tools[1:])
    source = f"---\n{ALLOWED_TOOLS_FIELD}: {', '.join(items)}\n---\n"
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        builder = SrcTreeBuilder(root)
        builder.add_plugin(case.plugin, skills={case.skill: source})
        dist_root = root / DIST_DIR_NAME
        build(builder.src_root, dist_root)
        observations: list[OptionalToolEmission] = []
        for target in Target:
            text = (
                dist_root
                / target.value
                / case.plugin
                / SKILLS_SUBDIR_NAME
                / case.skill
                / "SKILL.md"
            ).read_text(encoding="utf-8")
            frontmatter = _yaml_frontmatter(text)
            value = frontmatter[ALLOWED_TOOLS_FIELD]
            if not isinstance(value, str):
                raise TypeError("allowed-tools: expected comma-delimited string")
            observations.append(
                OptionalToolEmission(
                    target=target,
                    tools=tuple(item.strip() for item in value.split(",")),
                    text=text,
                )
            )
    return tuple(observations)


def _yaml_frontmatter(text: str) -> Mapping[str, object]:
    frontmatter, separator, _body = text.removeprefix("---\n").partition("\n---")
    if not separator:
        raise ValueError("emitted text has no closing frontmatter fence")
    loaded = yaml.safe_load(frontmatter)
    if not isinstance(loaded, Mapping):
        raise TypeError("emitted frontmatter is not a mapping")
    return cast("Mapping[str, object]", loaded)


def emitted_texts() -> tuple[EmittedText, ...]:
    """Read every text output, including converted agent definitions."""
    return tuple(
        EmittedText(target, path, text)
        for snapshot in (_canonical_emission_snapshot(), _synthetic_emission_snapshot())
        for target in Target
        for path, text in _text_files(snapshot.target(target)).items()
    )


@dataclass(frozen=True)
class RepeatedIncludeObservation:
    case: SourceScenario
    counts: dict[Target, int]


def repeated_include_observations() -> tuple[RepeatedIncludeObservation, ...]:
    return tuple(_observe_repeated_include(case) for case in source_scenarios())


@dataclass(frozen=True)
class ScopedIncludeObservation:
    case: TargetScopedIncludeCase
    paths: dict[Target, frozenset[Path]]
    inactive_text: str


def scoped_include_observations() -> tuple[ScopedIncludeObservation, ...]:
    return tuple(
        _observe_scoped_include(case) for case in target_scoped_include_cases()
    )


def _observe_scoped_include(case: TargetScopedIncludeCase) -> ScopedIncludeObservation:
    inactive_text = _render_inactive_include(case)
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
        projection = project_emissions(builder.src_root)
    return ScopedIncludeObservation(
        case,
        {target: frozenset(_projected_paths(projection, target)) for target in Target},
        inactive_text,
    )


def _render_inactive_include(case: TargetScopedIncludeCase) -> str:
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
        return render_text(
            case.root_body,
            shared_root=builder.shared_root,
            variables={BUILD_TARGET_VARIABLE: nonmatching_target.value},
        )


@cache
def _canonical_emission_snapshot() -> TargetEmissionSnapshot:
    source = _authored_plugin_snapshot(CANONICAL_SOURCE_ROOT)
    projection = project_emissions(CANONICAL_SOURCE_ROOT)
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
        projection=projection,
        src_root=CANONICAL_SOURCE_ROOT,
        rendered_sources={
            target: _rendered_emissions(projection, CANONICAL_SOURCE_ROOT, target)
            for target in Target
        },
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


def _projected_paths(projection: EmissionProjection, target: Target) -> set[Path]:
    return {emission.relative_path for emission in projection.for_target(target)}


def _projected_directories(projection: EmissionProjection, target: Target) -> set[Path]:
    return {
        parent
        for path in _projected_paths(projection, target)
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
            f"{CLAUDE_SKILL_DIR_TOKEN} {SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE}",
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
        projection = project_emissions(builder.src_root)
        rendered_sources = {
            target: _rendered_emissions(projection, builder.src_root, target)
            for target in Target
        }
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
        projection=projection,
        src_root=builder.src_root,
        rendered_sources=rendered_sources,
    )


def _observe_repeated_include(case: SourceScenario) -> RepeatedIncludeObservation:
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
        projection = project_emissions(builder.src_root)
    counts = {
        target: sum(
            emission.source == reference_source
            for emission in projection.for_target(target)
        )
        for target in Target
    }
    return RepeatedIncludeObservation(case, counts)


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


def _rendered_emissions(
    projection: EmissionProjection,
    src_root: Path,
    target: Target,
) -> dict[Path, str]:
    return {
        emission.relative_path: render_projected_emission_text(
            emission,
            src_root=src_root,
        )
        for emission in projection.for_target(target)
        if emission.source.suffix in TEXT_FILE_SUFFIXES
        and emission.action in _SOURCE_TEXT_ACTIONS
    }


def _claude_reference(case: SourceScenario) -> str:
    return f"{CLAUDE_SKILL_DIR_TOKEN}/{case.outer_topic}{MARKDOWN_FILE_SUFFIX}"


def _frontmatter_source(case: SourceScenario) -> str:
    claude_fields = f"{DISABLE_MODEL_INVOCATION_FIELD}: true"
    portable_fields = "\n".join(
        f"{field}: {case.outer_topic}"
        for field in (ALLOWED_TOOLS_FIELD, ARGUMENT_HINT_FIELD)
    )
    return f"---\n{claude_fields}\n{portable_fields}\n---\n{case.fragment_body}"
