"""Harness for audit verification-run contract evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from outcomeeng.validation.spx_version import REQUIRED_SPX_VERSION, is_satisfied


MINIMUM_VERIFICATION_RUN_SPX_VERSION: Final = "0.6.13"
WORKFLOW_PATH: Final = Path(".github/workflows/check.yml")
AUDIT_SKILL_SCRIPT_DIR: Final = Path("src/plugins/spec-tree/skills/audit/scripts")
IMPLEMENTATION_AUDITOR_PATH: Final = Path(
    "src/plugins/spec-tree/agents/implementation-auditor.md"
)
RETIRED_IMPLEMENTATION_AUDITOR_PATHS: Final = (
    Path("src/plugins/spec-tree/agents/auditor.md"),
    Path("src/plugins/spec-tree/agents/audit-orchestrator.md"),
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
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    return (
        is_satisfied(REQUIRED_SPX_VERSION, MINIMUM_VERIFICATION_RUN_SPX_VERSION)
        and f'SPX_VERSION: "{MINIMUM_VERIFICATION_RUN_SPX_VERSION}"' in workflow
    )


def audit_skill_ships_no_verdict_toolchain_scripts() -> bool:
    return all(
        not (AUDIT_SKILL_SCRIPT_DIR / retired_name).exists()
        for retired_name in RETIRED_AUDIT_SKILL_TOKENS
    )


def implementation_auditor_is_the_only_implementation_wrapper() -> bool:
    return (
        IMPLEMENTATION_AUDITOR_PATH.is_file()
        and "name: implementation-auditor"
        in IMPLEMENTATION_AUDITOR_PATH.read_text(encoding="utf-8")
        and all(
            not retired_path.exists()
            for retired_path in RETIRED_IMPLEMENTATION_AUDITOR_PATHS
        )
    )


def language_concern_skill_trios_exist() -> bool:
    return all(
        _language_concern_skill_trio_exists(plugin_name, skill_names)
        for plugin_name, skill_names in LANGUAGE_CONCERN_SKILLS
    )


def _language_concern_skill_trio_exists(
    plugin_name: str, skill_names: tuple[str, str, str]
) -> bool:
    skill_paths = [
        Path("src/plugins") / plugin_name / "skills" / skill_name
        for skill_name in skill_names
    ]
    code_skill_name = skill_names[0]
    code_skill_source = (skill_paths[0] / "SKILL.md").read_text(encoding="utf-8")
    old_skill_path = (
        Path("src/plugins")
        / plugin_name
        / "skills"
        / code_skill_name.removesuffix("-code")
    )
    return (
        all(skill_path.is_dir() for skill_path in skill_paths)
        and f"name: {code_skill_name}" in code_skill_source
        and f'"skill": "{code_skill_name}"' in code_skill_source
        and not old_skill_path.exists()
    )
