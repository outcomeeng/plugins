"""Generated reference categories for portability evidence."""

from __future__ import annotations

from pathlib import Path

from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    MARKDOWN_FILE_SUFFIX,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
)
from outcomeeng.validation.reference_portability import (
    ILLUSTRATIVE_SPX_ROOT,
    INVALID_INDEX_PLACEHOLDER,
    MARKETPLACE_PLUGIN_SOURCE_ROOT,
    MARKETPLACE_REPOSITORY_SLUGS,
    MARKETPLACE_RUNTIME_ROOTS,
    MARKETPLACE_TOOLCHAIN_ROOTS,
    PLUGIN_LOCAL_ROOT_TOKENS,
    PORTABLE_SPX_DIRECTORIES,
    PORTABLE_SPX_FILES,
    RETIRED_SPX_GUIDE_NAMES,
    SPX_REFERENCE_ROOT,
)
from outcomeeng_testing.generators.source_and_templating import source_scenarios


def nonportable_references() -> tuple[str, ...]:
    """Compose one variable reference for every prohibited source category."""
    scenario = source_scenarios()[0]
    numeric_index = len(source_scenarios())
    numbered = (
        f"{SPX_REFERENCE_ROOT}/{numeric_index}-{scenario.plugin}.enabler/"
        f"{scenario.skill}{MARKDOWN_FILE_SUFFIX}"
    )
    placeholder = (
        f"{SPX_REFERENCE_ROOT}/{INVALID_INDEX_PLACEHOLDER}{scenario.plugin}.enabler"
    )
    retired_guides = tuple(
        f"{SPX_REFERENCE_ROOT}/{guide}" for guide in RETIRED_SPX_GUIDE_NAMES
    )
    source_reference = (
        f"{MARKETPLACE_PLUGIN_SOURCE_ROOT}/{scenario.plugin}/"
        f"{SKILLS_SUBDIR_NAME}/{scenario.skill}/{SKILL_FILENAME}"
    )
    runtime_references = tuple(
        f"{root}/{scenario.plugin}/{AGENTS_SUBDIR_NAME}/"
        f"{scenario.outer_topic}{MARKDOWN_FILE_SUFFIX}"
        for root in MARKETPLACE_RUNTIME_ROOTS
    )
    toolchain_references = tuple(
        f"{root}/{scenario.scope}/{scenario.skill}.py"
        for root in MARKETPLACE_TOOLCHAIN_ROOTS
    )
    repository_references = tuple(
        f"{slug}/{scenario.skill}{MARKDOWN_FILE_SUFFIX}"
        for slug in MARKETPLACE_REPOSITORY_SLUGS
    )
    absolute_runtime = str(Path.cwd() / runtime_references[0])
    return (
        numbered,
        placeholder,
        *retired_guides,
        source_reference,
        *runtime_references,
        *toolchain_references,
        *repository_references,
        absolute_runtime,
    )


def portable_references() -> tuple[str, ...]:
    """Compose variable references for every allowed source category."""
    scenario = source_scenarios()[0]
    placeholders = (
        f"{SPX_REFERENCE_ROOT}/{{{scenario.scope}}}/{{{scenario.skill}}}",
        f"{SPX_REFERENCE_ROOT}/<{scenario.outer_topic}>",
    )
    illustrative = (
        f"{SPX_REFERENCE_ROOT}/{ILLUSTRATIVE_SPX_ROOT}.enabler/{scenario.skill}.outcome"
    )
    universal_spx_files = tuple(
        f"{SPX_REFERENCE_ROOT}/{name}" for name in PORTABLE_SPX_FILES
    )
    universal_spx_directories = tuple(
        f"{SPX_REFERENCE_ROOT}/{root}/{scenario.skill}"
        for root in PORTABLE_SPX_DIRECTORIES
    )
    universal_source = (
        f"src/{scenario.skill}.ts",
        f"dist/{scenario.skill}.js",
        f".dist/{scenario.plugin}/{scenario.skill}{MARKDOWN_FILE_SUFFIX}",
    )
    plugin_local = tuple(
        f"{token}/{scenario.skill}{MARKDOWN_FILE_SUFFIX}"
        for token in PLUGIN_LOCAL_ROOT_TOKENS
    )
    return (
        *placeholders,
        illustrative,
        *universal_spx_files,
        *universal_spx_directories,
        *universal_source,
        *MARKETPLACE_REPOSITORY_SLUGS,
        *plugin_local,
    )
