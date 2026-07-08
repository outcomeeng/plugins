"""Harness for audit verification-run contract evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from outcomeeng.validation.spx_version import (
    REQUIRED_SPX_VERSION,
    is_satisfied,
    read_pinned_version,
)


MINIMUM_VERIFICATION_RUN_SPX_VERSION: Final = "0.6.13"
WORKFLOW_PATH: Final = Path(".github/workflows/check.yml")
PLUGIN_SURFACES: Final = (
    Path("src/plugins"),
    Path("dist/claude"),
    Path("dist/codex"),
)
AUDIT_SKILL_SCRIPT_DIRS: Final = tuple(
    surface / "spec-tree" / "skills" / "audit" / "scripts"
    for surface in PLUGIN_SURFACES
)
SPEC_TREE_AGENT_DIRS: Final = tuple(
    surface / "spec-tree" / "agents" for surface in PLUGIN_SURFACES
)
RETIRED_IMPLEMENTATION_AUDITOR_PATHS: Final = (
    "auditor.md",
    "audit-orchestrator.md",
)
RETIRED_AUDIT_SKILL_TOKENS: Final = (
    "verdict.py",
    "aggregate_verdicts.py",
    "pass_results.py",
    "journal_emit.py",
    "audit_orchestrator.py",
)
LANGUAGE_CONCERN_SKILLS: Final = (
    (
        "python",
        ("audit-python-code", "audit-python-tests", "audit-python-architecture"),
    ),
    (
        "typescript",
        (
            "audit-typescript-code",
            "audit-typescript-tests",
            "audit-typescript-architecture",
        ),
    ),
    ("rust", ("audit-rust-code", "audit-rust-tests", "audit-rust-architecture")),
)


def spx_floor_provides_verification_run_lifecycle() -> bool:
    workflow_pin = read_pinned_version(WORKFLOW_PATH.read_text(encoding="utf-8"))
    return (
        is_satisfied(REQUIRED_SPX_VERSION, MINIMUM_VERIFICATION_RUN_SPX_VERSION)
        and workflow_pin is not None
        and is_satisfied(workflow_pin, MINIMUM_VERIFICATION_RUN_SPX_VERSION)
    )


def audit_skill_ships_no_verdict_toolchain_scripts() -> bool:
    return all(
        not (script_dir / retired_name).exists()
        for script_dir in AUDIT_SKILL_SCRIPT_DIRS
        for retired_name in RETIRED_AUDIT_SKILL_TOKENS
    )


def implementation_auditor_is_the_only_implementation_wrapper() -> bool:
    return all(
        (agent_dir / "implementation-auditor.md").is_file()
        for agent_dir in SPEC_TREE_AGENT_DIRS
    ) and not any(
        (agent_dir / retired_name).exists()
        for agent_dir in SPEC_TREE_AGENT_DIRS
        for retired_name in RETIRED_IMPLEMENTATION_AUDITOR_PATHS
    )


def language_concern_skill_trios_exist() -> bool:
    return all(
        _language_concern_skill_trio_exists(plugin_name, skill_names)
        for plugin_name, skill_names in LANGUAGE_CONCERN_SKILLS
    )


def _language_concern_skill_trio_exists(
    plugin_name: str, skill_names: tuple[str, str, str]
) -> bool:
    skill_paths = tuple(
        surface / plugin_name / "skills" / skill_name
        for surface in PLUGIN_SURFACES
        for skill_name in skill_names
    )
    old_skill_paths = tuple(
        surface / plugin_name / "skills" / skill_names[0].removesuffix("-code")
        for surface in PLUGIN_SURFACES
    )
    return all(
        (skill_path / "SKILL.md").is_file() for skill_path in skill_paths
    ) and not any(old_skill_path.exists() for old_skill_path in old_skill_paths)
