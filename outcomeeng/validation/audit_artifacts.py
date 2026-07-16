"""Validate audit artifacts across plugin surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from outcomeeng.distribution.orchestration import (
    CLAUDE_DIST_PLUGINS_DIR,
    CODEX_DIST_PLUGINS_DIR,
    SOURCE_PLUGINS_DIR,
)

PLUGIN_SURFACE_PATHS: Final = (
    SOURCE_PLUGINS_DIR,
    CLAUDE_DIST_PLUGINS_DIR,
    CODEX_DIST_PLUGINS_DIR,
)
SPEC_TREE_PLUGIN_NAME: Final = "spec-tree"
SKILLS_DIR_NAME: Final = "skills"
AGENTS_DIR_NAME: Final = "agents"
SKILL_FILENAME: Final = "SKILL.md"
IMPLEMENTATION_AUDIT_SKILL_NAME: Final = "audit-implementation"
AUDIT_SKILL_PREFIX: Final = "audit-"
IMPLEMENTATION_AUDITOR_FILENAME: Final = "implementation-auditor.md"
RETIRED_IMPLEMENTATION_AUDITOR_FILENAMES: Final = (
    "auditor.md",
    "audit-orchestrator.md",
)
LANGUAGE_CODE_SKILL_TEMPLATE: Final = "code-{language}"
LANGUAGE_AUDIT_SKILL_TEMPLATE: Final = "audit-{language}-{concern}"
RETIRED_LANGUAGE_AUDIT_SKILL_TEMPLATE: Final = "audit-{language}"
LANGUAGE_AUDIT_CONCERNS: Final = ("code", "tests", "architecture")
RETIRED_AUDIT_RUNTIME_FILENAMES: Final = (
    "verdict.py",
    "aggregate_verdicts.py",
    "pass_results.py",
    "journal_emit.py",
    "audit_orchestrator.py",
)


def check_audit_artifact_contract(root: Path) -> list[str]:
    """Return implementation-audit contract violations under ``root``."""
    errors: list[str] = []
    for surface in audit_contract_surfaces(root):
        errors.extend(check_audit_runtime_surface(surface))
        errors.extend(check_wrapper_surface(surface))
        errors.extend(check_language_concern_surface(surface))
    return errors


def audit_contract_surfaces(root: Path) -> tuple[Path, ...]:
    """Return present plugin surfaces that expose the audit-owning plugin."""
    return tuple(
        root / relative_surface
        for relative_surface in PLUGIN_SURFACE_PATHS
        if (root / relative_surface / SPEC_TREE_PLUGIN_NAME).is_dir()
    )


def check_audit_runtime_surface(surface: Path) -> list[str]:
    """Return audit-runtime violations for one plugin surface."""
    errors = check_runtime_surface(surface)
    implementation_runtime = implementation_audit_runtime_directory(surface)
    for runtime_dir in audit_skill_runtime_directories(surface):
        if runtime_dir == implementation_runtime:
            continue
        errors.extend(
            f"{path}: retired audit runtime artifact"
            for path in runtime_dir.rglob("*")
            if path.is_file() and path.name in RETIRED_AUDIT_RUNTIME_FILENAMES
        )
    return errors


def check_runtime_surface(surface: Path) -> list[str]:
    """Return runtime-directory violations for one plugin surface."""
    runtime_dir = implementation_audit_runtime_directory(surface)
    if not runtime_dir.is_dir():
        return [f"{runtime_dir}: runtime directory missing"]
    entries = {
        entry.relative_to(runtime_dir).as_posix() for entry in runtime_dir.rglob("*")
    }
    if entries == {SKILL_FILENAME}:
        return []
    return [f"{runtime_dir}: expected only {SKILL_FILENAME}, found {sorted(entries)}"]


def check_wrapper_surface(surface: Path) -> list[str]:
    """Return implementation-wrapper violations for one plugin surface."""
    errors: list[str] = []
    agents_dir = surface / SPEC_TREE_PLUGIN_NAME / AGENTS_DIR_NAME
    wrapper_path = agents_dir / IMPLEMENTATION_AUDITOR_FILENAME
    if not wrapper_path.is_file():
        errors.append(f"{wrapper_path}: wrapper missing")
    for filename in RETIRED_IMPLEMENTATION_AUDITOR_FILENAMES:
        retired_path = agents_dir / filename
        if retired_path.exists():
            errors.append(f"{retired_path}: retired wrapper exists")

    agent_paths = tuple(surface.glob(f"*/{AGENTS_DIR_NAME}/*.md"))
    language_names = frozenset(
        (
            *implementation_languages(surface),
            *(path.parent.parent.name for path in agent_paths),
        )
    )
    errors.extend(
        f"{path}: language-specific auditor exists"
        for path in agent_paths
        if any(
            path.name in language_specific_auditor_filenames(language)
            for language in language_names
        )
    )
    return errors


def check_language_concern_surface(surface: Path) -> list[str]:
    """Return language concern-trio violations for one plugin surface."""
    errors: list[str] = []
    for language in implementation_languages(surface):
        retired_skill = (
            surface
            / language
            / SKILLS_DIR_NAME
            / RETIRED_LANGUAGE_AUDIT_SKILL_TEMPLATE.format(language=language)
        )
        if retired_skill.exists():
            errors.append(f"{retired_skill}: retired aggregate audit skill exists")
        for concern in LANGUAGE_AUDIT_CONCERNS:
            skill_path = (
                surface
                / language
                / SKILLS_DIR_NAME
                / LANGUAGE_AUDIT_SKILL_TEMPLATE.format(
                    language=language,
                    concern=concern,
                )
                / SKILL_FILENAME
            )
            if not skill_path.is_file():
                errors.append(f"{skill_path}: language concern skill missing")
    return errors


def implementation_audit_runtime_directory(surface: Path) -> Path:
    """Return the implementation-audit runtime directory for ``surface``."""
    return (
        surface
        / SPEC_TREE_PLUGIN_NAME
        / SKILLS_DIR_NAME
        / IMPLEMENTATION_AUDIT_SKILL_NAME
    )


def audit_skill_runtime_directories(surface: Path) -> tuple[Path, ...]:
    """Return spec-tree audit skill runtime directories for ``surface``."""
    skills_dir = surface / SPEC_TREE_PLUGIN_NAME / SKILLS_DIR_NAME
    if not skills_dir.is_dir():
        return ()
    return tuple(
        sorted(
            path
            for path in skills_dir.iterdir()
            if path.is_dir() and path.name.startswith(AUDIT_SKILL_PREFIX)
        )
    )


def implementation_languages(surface: Path) -> tuple[str, ...]:
    """Return languages identified by their implementation skill surface."""
    return tuple(
        sorted(
            plugin_dir.name
            for plugin_dir in surface.iterdir()
            if plugin_dir.is_dir()
            and (
                plugin_dir
                / SKILLS_DIR_NAME
                / LANGUAGE_CODE_SKILL_TEMPLATE.format(language=plugin_dir.name)
                / SKILL_FILENAME
            ).is_file()
        )
    )


def language_specific_auditor_filenames(language: str) -> frozenset[str]:
    """Return forbidden language-specific implementation wrapper filenames."""
    concerns = (*LANGUAGE_AUDIT_CONCERNS, "test")
    return frozenset(
        {
            f"{language}-auditor.md",
            f"{language}-audit-orchestrator.md",
            f"audit-{language}.md",
            *(f"{language}-{concern}-auditor.md" for concern in concerns),
            *(f"audit-{language}-{concern}.md" for concern in concerns),
        }
    )
