"""Resource lifecycle and observations for distribution evidence."""

from __future__ import annotations

import tempfile
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from hypothesis import given, seed, settings
import yaml

from outcomeeng.distribution.contracts import (
    CLAUDE_DIST_RELATIVE,
    COLLECTED_SKILL_DIR_NAME_FIELD,
    COLLECTED_SKILL_SOURCE_FIELD,
    DIRECTIVE_DESCRIPTION_BOUNDARY,
    DIRECTIVE_DESCRIPTION_PREFIX,
    DISTRIBUTION_WORKFLOW_RELATIVE,
    FRONTMATTER_DELIMITER,
    GIT_METADATA_DIR_NAME,
    MINIMUM_VERSION_PREFIX,
    PROJECT_FIELD,
    PROJECT_METADATA_RELATIVE,
    PROJECT_REQUIRES_PYTHON_FIELD,
    RECURSIVE_GLOB,
    REFERENCES_SUBDIR_NAME,
    SENTENCE_TERMINATOR,
    SKILL_DESCRIPTION_FIELD,
    SKILL_FILENAME,
    SKILL_NAME_FIELD,
    SKILLS_SUBDIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
    WORKFLOW_DISTRIBUTION_JOB,
    WORKFLOW_JOBS_FIELD,
    WORKFLOW_ON_FIELD,
    WORKFLOW_PATHS_FIELD,
    WORKFLOW_PUSH_FIELD,
    WORKFLOW_PYTHON_VERSION_FIELD,
    WORKFLOW_SETUP_PYTHON_STEP,
    WORKFLOW_STEP_NAME_FIELD,
    WORKFLOW_STEPS_FIELD,
    WORKFLOW_WITH_FIELD,
)
from outcomeeng.distribution.distribute import (
    clean_description,
    clear_repo_contents,
    collect_skills,
    copy_skill,
)
from outcomeeng.distribution.orchestration import (
    CODEX_DISTRIBUTION_PATH,
    DISTRIBUTION_RUNTIME_PATH,
    DISTRIBUTION_SOURCE_PATH,
    RETIRED_DISTRIBUTION_SOURCE_PREFIX,
    Workflow,
    distribution_python_version_matches_project,
    distribution_workflow_paths_match_contract,
)
from outcomeeng_testing.generators.distribution import (
    DistributionScenario,
    distribution_scenarios,
    plugin_skill_mapping_strategy,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SOURCE_ROOT = REPOSITORY_ROOT / SOURCE_ROOT_NAME

DISTRIBUTION_PROPERTY_EXAMPLES: Final = 50
DISTRIBUTION_PROPERTY_SEED: Final = 20260714
DISTRIBUTION_PROPERTY_REPLAY_PATH: Final = (
    "just test spx/32-distribution.enabler/tests/test_distribute_skills.property.l1.py"
)


@dataclass(frozen=True)
class CollectedSkill:
    """One collected skill projected onto its source-owned metadata fields."""

    source: Path
    name: str
    description: str
    dir_name: str


@dataclass(frozen=True)
class SkillCollectionObservation:
    """Skills created for one scenario and the collection result over them."""

    scenario: DistributionScenario
    sources: Mapping[str, Path]
    collected: tuple[CollectedSkill, ...]


@dataclass(frozen=True)
class DescriptionCleaningObservation:
    """The directive-framed action and the description cleaning returned."""

    action: str
    cleaned: str


@dataclass(frozen=True)
class TargetCleanupObservation:
    """Entries left after cleanup and the metadata content before and after."""

    remaining_entries: tuple[str, ...]
    written_metadata_content: str
    preserved_metadata_content: str


@dataclass(frozen=True)
class SkillCopyObservation:
    """Names supplied to a skill copy and every entry it produced, links included."""

    regular_reference: str
    valid_link_reference: str
    broken_link_reference: str
    copied_paths: frozenset[Path]


@dataclass(frozen=True)
class WorkflowContractObservation:
    """Production contract results for the committed workflow and its variants."""

    committed_result: bool
    violating_results: tuple[bool, ...]


@dataclass(frozen=True)
class SkillCollectionUnionCase:
    """One generated plugin-to-skill mapping and the skill names collected."""

    plugin_skills: Mapping[str, tuple[str, ...]]
    collected_dir_names: tuple[str, ...]


def observe_skill_collection() -> SkillCollectionObservation:
    """Collect two generated skills of one plugin from a temporary tree."""
    scenario = distribution_scenarios()[0]
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        sources = {
            skill_name: _create_skill(root, scenario, skill_name)
            for skill_name in (scenario.skill, scenario.alternate_skill)
        }
        result = collect_skills([scenario.plugin], monorepo_root=root)
        return SkillCollectionObservation(
            scenario=scenario,
            sources=sources,
            collected=_collected_skills(result),
        )


def observe_plugin_without_skills() -> tuple[CollectedSkill, ...]:
    """Collect from a plugin directory that has no skills directory."""
    scenario = distribution_scenarios()[0]
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        (root / CLAUDE_DIST_RELATIVE / scenario.plugin).mkdir(parents=True)
        return _collected_skills(collect_skills([scenario.plugin], monorepo_root=root))


def observe_skill_without_manifest() -> tuple[CollectedSkill, ...]:
    """Collect from a skill directory that has no skill manifest."""
    scenario = distribution_scenarios()[0]
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        _skill_root(root, scenario.plugin, scenario.skill).mkdir(parents=True)
        return _collected_skills(collect_skills([scenario.plugin], monorepo_root=root))


def observe_directive_description_cleaning() -> DescriptionCleaningObservation:
    """Clean a description framed by the source-owned directive markers."""
    action = distribution_scenarios()[0].action
    description = (
        f"{DIRECTIVE_DESCRIPTION_PREFIX}{action}"
        f"{DIRECTIVE_DESCRIPTION_BOUNDARY} {action}{SENTENCE_TERMINATOR}"
    )
    return DescriptionCleaningObservation(
        action=action,
        cleaned=clean_description(description),
    )


def observe_target_cleanup() -> TargetCleanupObservation:
    """Clear a target holding metadata, an ordinary file, and a directory."""
    scenario = distribution_scenarios()[0]
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        metadata_file = root / GIT_METADATA_DIR_NAME / scenario.skill
        metadata_file.parent.mkdir()
        metadata_file.write_text(scenario.content)
        (root / scenario.alternate_skill).write_text(scenario.content)
        ordinary_directory = root / scenario.plugin
        ordinary_directory.mkdir()
        (ordinary_directory / scenario.skill).write_text(scenario.content)
        clear_repo_contents(root)
        return TargetCleanupObservation(
            remaining_entries=tuple(sorted(entry.name for entry in root.iterdir())),
            written_metadata_content=scenario.content,
            preserved_metadata_content=(
                metadata_file.read_text() if metadata_file.is_file() else ""
            ),
        )


def observe_skill_copy_with_links() -> SkillCopyObservation:
    """Copy a skill whose references hold a file, a valid link, and a broken link."""
    scenario = distribution_scenarios()[0]
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        source = _create_skill(root, scenario, scenario.skill)
        references = source / REFERENCES_SUBDIR_NAME
        references.mkdir()
        regular = references / scenario.alternate_skill
        regular.write_text(scenario.content)
        valid_link = references / scenario.plugin
        valid_link.symlink_to(regular)
        broken_link = references / scenario.action
        broken_link.symlink_to(references / scenario.action / scenario.skill)
        destination = root / Target.CODEX.value
        destination.mkdir()
        copy_skill(
            {
                COLLECTED_SKILL_SOURCE_FIELD: source,
                COLLECTED_SKILL_DIR_NAME_FIELD: scenario.skill,
            },
            destination,
        )
        copied = destination / scenario.skill
        return SkillCopyObservation(
            regular_reference=regular.name,
            valid_link_reference=valid_link.name,
            broken_link_reference=broken_link.name,
            copied_paths=frozenset(
                path.relative_to(copied) for path in copied.rglob("*")
            ),
        )


def exercise_skill_collection_union(
    assert_case: Callable[[SkillCollectionUnionCase], None],
) -> None:
    """Supply generated multi-plugin collections to the evidence file's predicate."""

    @seed(DISTRIBUTION_PROPERTY_SEED)
    @settings(
        max_examples=DISTRIBUTION_PROPERTY_EXAMPLES,
        deadline=None,
        print_blob=True,
    )
    @given(plugin_skills=plugin_skill_mapping_strategy())
    def run_cases(plugin_skills: dict[str, tuple[str, ...]]) -> None:
        assert_case(_observe_skill_collection_union(plugin_skills))

    run_replayable_property(
        run_cases,
        seed_value=DISTRIBUTION_PROPERTY_SEED,
        replay_path=DISTRIBUTION_PROPERTY_REPLAY_PATH,
    )


def observe_distribution_workflow_paths() -> WorkflowContractObservation:
    """Apply the path contract to the committed workflow and violating variants."""
    paths = _push_paths(_workflow())
    retired_source_path = f"{RETIRED_DISTRIBUTION_SOURCE_PREFIX}{RECURSIVE_GLOB}"
    violating_variants = (
        paths - {DISTRIBUTION_RUNTIME_PATH},
        paths - {DISTRIBUTION_SOURCE_PATH},
        paths | {retired_source_path},
        paths | {CODEX_DISTRIBUTION_PATH},
    )
    return WorkflowContractObservation(
        committed_result=distribution_workflow_paths_match_contract(paths),
        violating_results=tuple(
            distribution_workflow_paths_match_contract(variant)
            for variant in violating_variants
        ),
    )


def observe_distribution_workflow_python() -> WorkflowContractObservation:
    """Apply the Python-version contract to the workflow and a derived mismatch."""
    requires_python = _requires_python_specifier()
    workflow_version = _distribution_python_version(_workflow())
    violating_version = f"{MINIMUM_VERSION_PREFIX}{workflow_version}"
    return WorkflowContractObservation(
        committed_result=distribution_python_version_matches_project(
            workflow_version,
            requires_python,
        ),
        violating_results=(
            distribution_python_version_matches_project(
                violating_version,
                requires_python,
            ),
        ),
    )


def _observe_skill_collection_union(
    plugin_skills: dict[str, tuple[str, ...]],
) -> SkillCollectionUnionCase:
    scenario = distribution_scenarios()[0]
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        for plugin_name, skill_names in plugin_skills.items():
            for skill_name in skill_names:
                _create_skill(
                    root,
                    scenario,
                    skill_name,
                    plugin_name=plugin_name,
                )
        result = collect_skills(list(plugin_skills), monorepo_root=root)
        return SkillCollectionUnionCase(
            plugin_skills=plugin_skills,
            collected_dir_names=tuple(
                cast("str", skill[COLLECTED_SKILL_DIR_NAME_FIELD]) for skill in result
            ),
        )


def _collected_skills(result: list[dict[str, object]]) -> tuple[CollectedSkill, ...]:
    return tuple(
        CollectedSkill(
            source=cast("Path", skill[COLLECTED_SKILL_SOURCE_FIELD]),
            name=cast("str", skill[SKILL_NAME_FIELD]),
            description=cast("str", skill[SKILL_DESCRIPTION_FIELD]),
            dir_name=cast("str", skill[COLLECTED_SKILL_DIR_NAME_FIELD]),
        )
        for skill in result
    )


def _create_skill(
    root: Path,
    scenario: DistributionScenario,
    skill_name: str,
    *,
    plugin_name: str | None = None,
) -> Path:
    skill_root = _skill_root(root, plugin_name or scenario.plugin, skill_name)
    skill_root.mkdir(parents=True)
    frontmatter = yaml.safe_dump(
        {
            SKILL_NAME_FIELD: skill_name,
            SKILL_DESCRIPTION_FIELD: scenario.action,
        },
        sort_keys=True,
    )
    (skill_root / SKILL_FILENAME).write_text(
        f"{FRONTMATTER_DELIMITER}\n{frontmatter}{FRONTMATTER_DELIMITER}\n"
        f"{scenario.content}"
    )
    return skill_root


def _skill_root(root: Path, plugin_name: str, skill_name: str) -> Path:
    return root / CLAUDE_DIST_RELATIVE / plugin_name / SKILLS_SUBDIR_NAME / skill_name


def _workflow() -> Workflow:
    return cast(
        "Workflow",
        yaml.load(
            (REPOSITORY_ROOT / DISTRIBUTION_WORKFLOW_RELATIVE).read_text(),
            Loader=yaml.BaseLoader,
        ),
    )


def _push_paths(workflow: Workflow) -> set[str]:
    on_section = cast(Workflow, workflow[WORKFLOW_ON_FIELD])
    push_section = cast(Workflow, on_section[WORKFLOW_PUSH_FIELD])
    return set(cast(list[str], push_section[WORKFLOW_PATHS_FIELD]))


def _distribution_python_version(workflow: Workflow) -> str:
    jobs = cast(Workflow, workflow[WORKFLOW_JOBS_FIELD])
    distribution = cast(Workflow, jobs[WORKFLOW_DISTRIBUTION_JOB])
    steps = cast(list[Workflow], distribution[WORKFLOW_STEPS_FIELD])
    setup_step = next(
        step
        for step in steps
        if step.get(WORKFLOW_STEP_NAME_FIELD) == WORKFLOW_SETUP_PYTHON_STEP
    )
    setup = cast(Workflow, setup_step[WORKFLOW_WITH_FIELD])
    return cast(str, setup[WORKFLOW_PYTHON_VERSION_FIELD])


def _requires_python_specifier() -> str:
    metadata = tomllib.loads((REPOSITORY_ROOT / PROJECT_METADATA_RELATIVE).read_text())
    project = cast(Workflow, metadata[PROJECT_FIELD])
    return cast(str, project[PROJECT_REQUIRES_PYTHON_FIELD])
