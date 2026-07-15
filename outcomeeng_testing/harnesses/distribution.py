"""Resource lifecycle and observations for distribution evidence."""

from __future__ import annotations

import tempfile
import tomllib
from collections import Counter
from pathlib import Path
from typing import Final, cast

from hypothesis import given, seed, settings
import yaml  # type: ignore[import-untyped]

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
type FileSnapshot = tuple[tuple[str, bytes], ...]

DISTRIBUTION_PROPERTY_EXAMPLES: Final = 50
DISTRIBUTION_PROPERTY_SEED: Final = 20260714
DISTRIBUTION_PROPERTY_REPLAY_PATH: Final = (
    "just test spx/32-distribution.enabler/tests/test_distribute_skills.property.l1.py"
)


def snapshot_files(root: Path) -> FileSnapshot:
    """Return a stable relative-path and byte-content snapshot below ``root``."""
    return tuple(
        sorted(
            (str(path.relative_to(root)), path.read_bytes())
            for path in root.rglob("*")
            if path.is_file()
        )
    )


def skill_collection_returns_complete_metadata() -> bool:
    """Exercise collection through generated plugin and skill identities."""
    scenario = distribution_scenarios()[0]
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        first_source = _create_skill(root, scenario, scenario.skill)
        second_source = _create_skill(root, scenario, scenario.alternate_skill)
        result = collect_skills([scenario.plugin], monorepo_root=root)
        expected = {
            (
                source,
                skill_name,
                scenario.action,
                skill_name,
            )
            for source, skill_name in (
                (first_source, scenario.skill),
                (second_source, scenario.alternate_skill),
            )
        }
        actual = {
            (
                cast("Path", skill[COLLECTED_SKILL_SOURCE_FIELD]),
                cast("str", skill[SKILL_NAME_FIELD]),
                cast("str", skill[SKILL_DESCRIPTION_FIELD]),
                cast("str", skill[COLLECTED_SKILL_DIR_NAME_FIELD]),
            )
            for skill in result
        }
        return actual == expected


def plugin_without_skills_is_skipped() -> bool:
    """Return whether a plugin without a skills directory contributes nothing."""
    scenario = distribution_scenarios()[0]
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        (root / CLAUDE_DIST_RELATIVE / scenario.plugin).mkdir(parents=True)
        return collect_skills([scenario.plugin], monorepo_root=root) == []


def skill_without_manifest_is_skipped() -> bool:
    """Return whether a skill directory without its manifest is skipped."""
    scenario = distribution_scenarios()[0]
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        _skill_root(root, scenario.plugin, scenario.skill).mkdir(parents=True)
        return collect_skills([scenario.plugin], monorepo_root=root) == []


def directive_description_is_cleaned() -> bool:
    """Return whether source-owned directive framing is removed."""
    action = distribution_scenarios()[0].action
    description = (
        f"{DIRECTIVE_DESCRIPTION_PREFIX}{action}"
        f"{DIRECTIVE_DESCRIPTION_BOUNDARY} {action}{SENTENCE_TERMINATOR}"
    )
    return clean_description(description) == action


def target_cleanup_preserves_only_git_metadata() -> bool:
    """Exercise recursive cleanup while retaining repository metadata."""
    scenario = distribution_scenarios()[0]
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        metadata_file = root / GIT_METADATA_DIR_NAME / scenario.skill
        metadata_file.parent.mkdir()
        metadata_file.write_text(scenario.content)
        ordinary_file = root / scenario.alternate_skill
        ordinary_file.write_text(scenario.content)
        ordinary_directory = root / scenario.plugin
        ordinary_directory.mkdir()
        (ordinary_directory / scenario.skill).write_text(scenario.content)
        clear_repo_contents(root)
        return tuple(root.iterdir()) == (metadata_file.parent,) and (
            metadata_file.read_text() == scenario.content
        )


def skill_copy_skips_broken_symlinks() -> bool:
    """Exercise copy behavior with regular, valid-link, and broken-link inputs."""
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
        return (
            (copied / SKILL_FILENAME).is_file()
            and (copied / REFERENCES_SUBDIR_NAME / regular.name).is_file()
            and (copied / REFERENCES_SUBDIR_NAME / valid_link.name).exists()
            and not (copied / REFERENCES_SUBDIR_NAME / broken_link.name).exists()
        )


def skill_collection_union_holds() -> bool:
    """Run the generated multi-plugin union property."""
    run_replayable_property(
        _generated_skill_collection_union_holds,
        seed_value=DISTRIBUTION_PROPERTY_SEED,
        replay_path=DISTRIBUTION_PROPERTY_REPLAY_PATH,
    )
    return True


def distribution_workflow_uses_runtime_and_source_paths() -> bool:
    """Exercise workflow path rules against conforming and violating variants."""
    paths = _push_paths(_workflow())
    retired_source_path = f"{RETIRED_DISTRIBUTION_SOURCE_PREFIX}{RECURSIVE_GLOB}"
    violating_variants = (
        paths - {DISTRIBUTION_RUNTIME_PATH},
        paths - {DISTRIBUTION_SOURCE_PATH},
        paths | {retired_source_path},
        paths | {CODEX_DISTRIBUTION_PATH},
    )
    return distribution_workflow_paths_match_contract(paths) and all(
        not distribution_workflow_paths_match_contract(variant)
        for variant in violating_variants
    )


def distribution_workflow_uses_project_python() -> bool:
    """Exercise Python-version alignment against a source-derived mismatch."""
    requires_python = _requires_python_specifier()
    workflow_version = _distribution_python_version(_workflow())
    violating_version = f"{MINIMUM_VERSION_PREFIX}{workflow_version}"
    return distribution_python_version_matches_project(
        workflow_version,
        requires_python,
    ) and not distribution_python_version_matches_project(
        violating_version,
        requires_python,
    )


@seed(DISTRIBUTION_PROPERTY_SEED)
@settings(
    max_examples=DISTRIBUTION_PROPERTY_EXAMPLES,
    deadline=None,
    print_blob=True,
)
@given(plugin_skills=plugin_skill_mapping_strategy())
def _generated_skill_collection_union_holds(
    plugin_skills: dict[str, tuple[str, ...]],
) -> None:
    scenario = distribution_scenarios()[0]
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        expected = Counter(
            skill_name
            for skill_names in plugin_skills.values()
            for skill_name in skill_names
        )
        for plugin_name, skill_names in plugin_skills.items():
            for skill_name in skill_names:
                _create_skill(
                    root,
                    scenario,
                    skill_name,
                    plugin_name=plugin_name,
                )
        result = collect_skills(list(plugin_skills), monorepo_root=root)
        actual = Counter(
            cast("str", skill[COLLECTED_SKILL_DIR_NAME_FIELD]) for skill in result
        )
        assert actual == expected


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
