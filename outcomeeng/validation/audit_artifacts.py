"""Validate audit artifacts across plugin surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from outcomeeng.distribution.build import (
    AGENT_CAPABILITY_REGISTRY,
    LIFECYCLE_TEMPLATE_NAME,
    agent_slug,
)
from outcomeeng.distribution.contracts import MARKDOWN_FILE_SUFFIX
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
IMPLEMENTATION_AUDITOR_STEM: Final = "implementation-auditor"
IMPLEMENTATION_AUDITOR_FILENAME: Final = f"{IMPLEMENTATION_AUDITOR_STEM}.md"
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
    surfaces = audit_contract_surfaces(root)
    expected_languages = tuple(
        sorted(
            {
                language
                for surface in surfaces
                for language in implementation_languages(surface)
            }
        )
    )
    for surface in surfaces:
        errors.extend(check_audit_runtime_surface(surface))
        errors.extend(check_wrapper_surface(surface))
        errors.extend(
            check_language_concern_surface(
                surface,
                expected_languages=expected_languages,
            )
        )
    return errors


def audit_contract_surfaces(root: Path) -> tuple[Path, ...]:
    """Return the audit surfaces declared by the repository layout."""
    present_surfaces = tuple(
        root / relative_surface
        for relative_surface in PLUGIN_SURFACE_PATHS
        if (root / relative_surface).is_dir()
    )
    if len(present_surfaces) > 1:
        return tuple(
            root / relative_surface for relative_surface in PLUGIN_SURFACE_PATHS
        )
    return present_surfaces


def agent_surface_paths(surface: Path) -> tuple[Path, ...]:
    """Return every agent artifact a plugin surface carries.

    A surface whose target declares agents in its plugin manifest keeps them as
    authored markdown under ``<plugin>/agents/``. A surface for a target whose
    manifest cannot declare agents carries converted artifacts inside each
    plugin's lifecycle skill instead, so the contract check follows the same
    per-target agent capability the build emits from.
    """
    capability = AGENT_CAPABILITY_REGISTRY.get(surface.name)
    if capability is None or capability.manifest_declares_agents:
        return tuple(surface.glob(f"*/{AGENTS_DIR_NAME}/*.md"))
    return tuple(
        surface.glob(f"*/{SKILLS_DIR_NAME}/*/{AGENTS_DIR_NAME}/*{capability.suffix}")
    )


def agent_artifact_name(surface: Path, plugin: str, agent_stem: str) -> str:
    """Return one agent's artifact filename on ``surface``."""
    capability = AGENT_CAPABILITY_REGISTRY.get(surface.name)
    if capability is None or capability.manifest_declares_agents:
        return f"{agent_stem}{MARKDOWN_FILE_SUFFIX}"
    return f"{agent_slug(plugin, agent_stem, capability=capability)}{capability.suffix}"


def agent_artifact_path(surface: Path, plugin: str, agent_stem: str) -> Path:
    """Return where ``surface`` carries one plugin agent."""
    capability = AGENT_CAPABILITY_REGISTRY.get(surface.name)
    filename = agent_artifact_name(surface, plugin, agent_stem)
    if capability is None or capability.manifest_declares_agents:
        return surface / plugin / AGENTS_DIR_NAME / filename
    return (
        surface
        / plugin
        / SKILLS_DIR_NAME
        / f"{plugin}-{LIFECYCLE_TEMPLATE_NAME}"
        / AGENTS_DIR_NAME
        / filename
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


def agent_owner(surface: Path, path: Path) -> tuple[str, str]:
    """Return the owning plugin and bare agent name for one agent artifact.

    A namespaced target carries the bare agent name as the filename stem. A flat
    target prefixes the plugin slug, so the prefix is stripped to recover the
    agent's own name — the value every wrapper rule is written against.
    """
    plugin = path.relative_to(surface).parts[0]
    capability = AGENT_CAPABILITY_REGISTRY.get(surface.name)
    stem = path.stem
    if capability is not None and not capability.manifest_declares_agents:
        prefix = f"{plugin}_"
        if stem.startswith(prefix):
            stem = stem[len(prefix) :]
    return plugin, stem


def check_wrapper_surface(surface: Path) -> list[str]:
    """Return implementation-wrapper violations for one plugin surface."""
    errors: list[str] = []
    wrapper_path = agent_artifact_path(
        surface, SPEC_TREE_PLUGIN_NAME, IMPLEMENTATION_AUDITOR_STEM
    )
    if not wrapper_path.is_file():
        errors.append(f"{wrapper_path}: wrapper missing")

    agent_paths = agent_surface_paths(surface)
    # Compare on the agent's own name rather than the artifact filename: a
    # target whose agent namespace is flat prefixes the plugin slug and uses its
    # own artifact suffix, so a filename comparison is inert on that surface and
    # would let a retired or language-specific wrapper through unseen.
    owners = {path: agent_owner(surface, path) for path in agent_paths}
    errors.extend(
        f"{path}: retired wrapper exists"
        for path, (_plugin, stem) in owners.items()
        if f"{stem}{MARKDOWN_FILE_SUFFIX}" in RETIRED_IMPLEMENTATION_AUDITOR_FILENAMES
    )
    language_names = frozenset(
        (
            *implementation_languages(surface),
            *(plugin for _path, (plugin, _stem) in owners.items()),
        )
    )
    errors.extend(
        f"{path}: language-specific auditor exists"
        for path, (_plugin, stem) in owners.items()
        if is_language_specific_auditor_filename(f"{stem}{MARKDOWN_FILE_SUFFIX}")
        or any(
            f"{stem}{MARKDOWN_FILE_SUFFIX}"
            in language_specific_auditor_filenames(language)
            for language in language_names
        )
    )
    return errors


def check_language_concern_surface(
    surface: Path,
    *,
    expected_languages: tuple[str, ...] | None = None,
) -> list[str]:
    """Return language concern-trio violations for one plugin surface."""
    errors: list[str] = []
    languages = (
        implementation_languages(surface)
        if expected_languages is None
        else expected_languages
    )
    for language in languages:
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
    """Return generic and language audit skill runtime directories."""
    skills_dir = surface / SPEC_TREE_PLUGIN_NAME / SKILLS_DIR_NAME
    runtime_directories = (
        {
            path
            for path in skills_dir.iterdir()
            if path.is_dir() and path.name.startswith(AUDIT_SKILL_PREFIX)
        }
        if skills_dir.is_dir()
        else set()
    )
    runtime_directories.update(
        skill_dir
        for language in implementation_languages(surface)
        for concern in LANGUAGE_AUDIT_CONCERNS
        if (
            skill_dir := (
                surface
                / language
                / SKILLS_DIR_NAME
                / LANGUAGE_AUDIT_SKILL_TEMPLATE.format(
                    language=language,
                    concern=concern,
                )
            )
        ).is_dir()
    )
    return tuple(sorted(runtime_directories))


def implementation_languages(surface: Path) -> tuple[str, ...]:
    """Return languages identified by their implementation skill surface."""
    if not surface.is_dir():
        return ()
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


def is_language_specific_auditor_filename(filename: str) -> bool:
    """Return whether ``filename`` structurally names a concern wrapper."""
    if not filename.endswith(".md"):
        return False
    stem = filename.removesuffix(".md")
    concerns = (*LANGUAGE_AUDIT_CONCERNS, "test")
    return any(
        (stem.endswith(f"-{concern}-auditor") and stem != f"{concern}-auditor")
        or (
            stem.startswith("audit-")
            and stem.endswith(f"-{concern}")
            and stem != f"audit-{concern}"
        )
        for concern in concerns
    )
