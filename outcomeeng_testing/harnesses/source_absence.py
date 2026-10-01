"""Source trees arranged around a skill or template directory with no manifest.

Each arrangement is a well-formed source tree carrying one authored skill,
plus one extra directory that holds no `SKILL.md`: either nothing, one file
a single ignore rule excludes, or one authored file. The returned record names the
extra directory and the authored skill's own manifest, whose emission shows
that validation accepted the tree. The linked tests own every predicate.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from outcomeeng.distribution.build import (
    IGNORED_SOURCE_DIRECTORY_NAMES,
    IGNORED_SOURCE_FILE_SUFFIXES,
    TEMPLATES_DIR_NAME,
)
from outcomeeng.distribution.contracts import (
    FRONTMATTER_DELIMITER,
    MARKDOWN_FILE_SUFFIX,
    PLUGINS_DIR_NAME,
    SKILL_FILENAME,
    SKILL_NAME_FIELD,
    SKILLS_SUBDIR_NAME,
)
from outcomeeng_testing.generators.source_and_templating import SourceScenario
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder


@dataclass(frozen=True)
class ExtraSkillDirectory:
    """A well-formed source tree plus one extra skill directory under a plugin.

    `authored_manifest` is the well-formed skill's own `SKILL.md`. Validation
    accepts the tree only when the extra directory is absent to it, so that
    file's emission is what distinguishes an accepted tree from a rejected one.
    """

    src_root: Path
    skill_root: Path
    authored_manifest: Path


@dataclass(frozen=True)
class ExtraTemplateDirectory:
    """A well-formed source tree plus one extra template directory."""

    src_root: Path
    template_root: Path
    authored_manifest: Path


class IgnoreRule(StrEnum):
    """Which rule of the authored-source predicate ignores the arranged file.

    Each rule alone ignores the file, so a validator that dropped either rule
    would see an authored file where the emission walk sees none.
    """

    DIRECTORY = "directory"
    SUFFIX = "suffix"


def arrange_cache_only_skill_directory(
    root: Path, case: SourceScenario, rule: IgnoreRule
) -> ExtraSkillDirectory:
    """Add a skill directory holding one file only `rule` ignores, no `SKILL.md`."""
    arranged = _extra_skill_directory(root, case)
    _write_ignored_file(arranged.skill_root, case, rule)
    return arranged


def arrange_empty_skill_directory(
    root: Path, case: SourceScenario
) -> ExtraSkillDirectory:
    """Add a skill directory holding no file at all."""
    return _extra_skill_directory(root, case)


def arrange_manifestless_skill_directory(
    root: Path, case: SourceScenario
) -> ExtraSkillDirectory:
    """Add a skill directory holding one authored file and no `SKILL.md`."""
    arranged = _extra_skill_directory(root, case)
    _write_authored_file(arranged.skill_root, case)
    return arranged


def arrange_cache_only_template_directory(
    root: Path, case: SourceScenario, rule: IgnoreRule
) -> ExtraTemplateDirectory:
    """Add a template directory holding one file only `rule` ignores."""
    arranged = _extra_template_directory(root, case)
    _write_ignored_file(arranged.template_root, case, rule)
    return arranged


def arrange_manifestless_template_directory(
    root: Path, case: SourceScenario
) -> ExtraTemplateDirectory:
    """Add a template directory holding one authored file and no `SKILL.md`."""
    arranged = _extra_template_directory(root, case)
    _write_authored_file(arranged.template_root, case)
    return arranged


def _extra_skill_directory(root: Path, case: SourceScenario) -> ExtraSkillDirectory:
    builder = _source_tree(root, case)
    skills_root = builder.src_root / PLUGINS_DIR_NAME / case.plugin / SKILLS_SUBDIR_NAME
    skill_root = skills_root / case.outer_topic
    skill_root.mkdir()
    return ExtraSkillDirectory(
        src_root=builder.src_root,
        skill_root=skill_root,
        authored_manifest=skills_root / case.skill / SKILL_FILENAME,
    )


def _extra_template_directory(
    root: Path, case: SourceScenario
) -> ExtraTemplateDirectory:
    builder = _source_tree(root, case)
    templates_root = builder.src_root / TEMPLATES_DIR_NAME
    authored_manifest = templates_root / case.skill / SKILL_FILENAME
    authored_manifest.parent.mkdir(parents=True)
    authored_manifest.write_text(_skill_body(case), encoding="utf-8")
    template_root = templates_root / case.outer_topic
    template_root.mkdir()
    return ExtraTemplateDirectory(
        src_root=builder.src_root,
        template_root=template_root,
        authored_manifest=authored_manifest,
    )


def _source_tree(root: Path, case: SourceScenario) -> SrcTreeBuilder:
    builder = SrcTreeBuilder(root)
    builder.add_plugin(case.plugin, skills={case.skill: _skill_body(case)})
    return builder


def _skill_body(case: SourceScenario) -> str:
    return (
        f"{FRONTMATTER_DELIMITER}\n{SKILL_NAME_FIELD}: {case.skill}\n"
        f"{FRONTMATTER_DELIMITER}\n\n{case.fragment_body}"
    )


def _write_ignored_file(
    directory: Path, case: SourceScenario, rule: IgnoreRule
) -> None:
    if rule is IgnoreRule.DIRECTORY:
        cache_dir = directory / next(iter(sorted(IGNORED_SOURCE_DIRECTORY_NAMES)))
        cache_dir.mkdir()
        _write_authored_file(cache_dir, case)
        return
    (directory / f"{case.skill}{IGNORED_SOURCE_FILE_SUFFIXES[0]}").write_bytes(b"")


def _write_authored_file(directory: Path, case: SourceScenario) -> None:
    (directory / f"{case.outer_topic}{MARKDOWN_FILE_SUFFIX}").write_text(
        case.fragment_body, encoding="utf-8"
    )


__all__ = [
    "ExtraSkillDirectory",
    "ExtraTemplateDirectory",
    "IgnoreRule",
    "arrange_cache_only_skill_directory",
    "arrange_cache_only_template_directory",
    "arrange_empty_skill_directory",
    "arrange_manifestless_skill_directory",
    "arrange_manifestless_template_directory",
]
