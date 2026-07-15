"""Harness for audit verification-run contract evidence."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from outcomeeng.validation.plugins import (
    IMPLEMENTATION_AUDIT_SKILL_RELATIVE_PATH,
    PLUGIN_SURFACE_ROOTS,
    RETIRED_AUDIT_SCRIPT_FILENAMES,
    check_implementation_auditor_wrapper,
    check_language_concern_skill_trios,
    check_retired_audit_scripts,
)
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
    """Return whether every plugin surface carries only the current wrapper."""
    return not check_implementation_auditor_wrapper(REPO_ROOT)


def language_concern_skill_trios_exist() -> bool:
    """Return whether every language plugin carries all audit concern skills."""
    return not check_language_concern_skill_trios(REPO_ROOT)


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
