"""Harness for audit verification-run contract evidence."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from outcomeeng.validation.plugins import (
    IMPLEMENTATION_AUDIT_SKILL_RELATIVE_PATH,
    IMPLEMENTATION_AUDITOR_AGENT_RELATIVE_PATH,
    LANGUAGE_AUDIT_CONCERNS,
    PLUGIN_SURFACE_ROOTS,
    RETIRED_AUDIT_SCRIPT_FILENAMES,
    RETIRED_IMPLEMENTATION_AUDITOR_RELATIVE_PATHS,
    check_implementation_auditor_wrapper,
    check_language_concern_skill_trios,
    check_retired_audit_scripts,
    language_audit_skill_relative_path,
    language_code_skill_relative_path,
    retired_language_audit_skill_relative_path,
)
from outcomeeng.distribution.orchestration import SOURCE_PLUGINS_DIR
from outcomeeng.validation.spx_version import (
    REQUIRED_SPX_VERSION,
    VERIFICATION_RUN_MINIMUM_SPX_VERSION,
    is_satisfied,
    read_pinned_version,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
WORKFLOW_PATH: Final = REPO_ROOT / ".github" / "workflows" / "check.yml"


def spx_floor_provides_verification_run_lifecycle() -> bool:
    """Return whether the product floor and CI pin include verification runs."""
    workflow_pin = read_pinned_version(WORKFLOW_PATH.read_text(encoding="utf-8"))
    return (
        is_satisfied(
            REQUIRED_SPX_VERSION,
            VERIFICATION_RUN_MINIMUM_SPX_VERSION,
        )
        and workflow_pin is not None
        and is_satisfied(workflow_pin, REQUIRED_SPX_VERSION)
    )


def implementation_auditor_is_the_only_implementation_wrapper() -> bool:
    """Return whether wrapper topology is clean and violations are rejected."""
    if check_implementation_auditor_wrapper(REPO_ROOT):
        return False

    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        _create_valid_implementation_wrapper_topology(root)
        if check_implementation_auditor_wrapper(root):
            return False

        for surface_root in PLUGIN_SURFACE_ROOTS:
            wrapper_path = (
                root / surface_root / IMPLEMENTATION_AUDITOR_AGENT_RELATIVE_PATH
            )
            wrapper_path.unlink()
            if not check_implementation_auditor_wrapper(root):
                return False
            wrapper_path.touch()

            for retired_relative_path in RETIRED_IMPLEMENTATION_AUDITOR_RELATIVE_PATHS:
                retired_path = root / surface_root / retired_relative_path
                retired_path.touch()
                if not check_implementation_auditor_wrapper(root):
                    return False
                retired_path.unlink()

    return True


def language_concern_skill_trios_exist() -> bool:
    """Return whether concern trios are clean and violations are rejected."""
    if check_language_concern_skill_trios(REPO_ROOT):
        return False

    language = _source_language_plugin_name()
    if language is None:
        return False

    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        _create_valid_language_concern_topology(root, language)
        if check_language_concern_skill_trios(root):
            return False

        for surface_root in PLUGIN_SURFACE_ROOTS:
            for concern in LANGUAGE_AUDIT_CONCERNS:
                concern_path = (
                    root
                    / surface_root
                    / language_audit_skill_relative_path(language, concern)
                )
                concern_path.unlink()
                if not check_language_concern_skill_trios(root):
                    return False
                concern_path.touch()

            retired_path = (
                root
                / surface_root
                / retired_language_audit_skill_relative_path(language)
            )
            retired_path.mkdir()
            if not check_language_concern_skill_trios(root):
                return False
            retired_path.rmdir()

    return True


def implementation_audit_scripts_are_absent_and_rejected() -> bool:
    """Return whether real trees are clean and every retired script is rejected."""
    if check_retired_audit_scripts(REPO_ROOT):
        return False

    return all(
        _retired_script_is_rejected(surface_root, retired_name)
        for surface_root in PLUGIN_SURFACE_ROOTS
        for retired_name in RETIRED_AUDIT_SCRIPT_FILENAMES
    )


def _retired_script_is_rejected(surface_root: Path, retired_name: str) -> bool:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        retired_path = (
            root
            / surface_root
            / IMPLEMENTATION_AUDIT_SKILL_RELATIVE_PATH
            / retired_name
        )
        retired_path.parent.mkdir(parents=True)
        retired_path.touch()
        return bool(check_retired_audit_scripts(root))


def _create_valid_implementation_wrapper_topology(root: Path) -> None:
    for surface_root in PLUGIN_SURFACE_ROOTS:
        wrapper_path = root / surface_root / IMPLEMENTATION_AUDITOR_AGENT_RELATIVE_PATH
        wrapper_path.parent.mkdir(parents=True)
        wrapper_path.touch()


def _source_language_plugin_name() -> str | None:
    source_plugins_root = REPO_ROOT / SOURCE_PLUGINS_DIR
    for plugin_dir in sorted(source_plugins_root.iterdir()):
        language = plugin_dir.name
        if (
            source_plugins_root / language_code_skill_relative_path(language)
        ).is_file():
            return language
    return None


def _create_valid_language_concern_topology(root: Path, language: str) -> None:
    for surface_root in PLUGIN_SURFACE_ROOTS:
        plugins_root = root / surface_root
        code_skill_path = plugins_root / language_code_skill_relative_path(language)
        code_skill_path.parent.mkdir(parents=True)
        code_skill_path.touch()
        for concern in LANGUAGE_AUDIT_CONCERNS:
            concern_path = plugins_root / language_audit_skill_relative_path(
                language,
                concern,
            )
            concern_path.parent.mkdir(parents=True)
            concern_path.touch()
