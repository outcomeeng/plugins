"""Repository-owned implementation-audit contract checks."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.validation.audit_artifacts import (
    AGENTS_DIR_NAME,
    IMPLEMENTATION_AUDITOR_FILENAME,
    LANGUAGE_AUDIT_CONCERNS,
    LANGUAGE_AUDIT_SKILL_TEMPLATE,
    LANGUAGE_CODE_SKILL_TEMPLATE,
    PLUGIN_SURFACE_PATHS,
    SKILL_FILENAME,
    SKILLS_DIR_NAME,
    SPEC_TREE_PLUGIN_NAME,
    check_language_concern_surface,
    check_runtime_surface,
    check_wrapper_surface,
    implementation_audit_runtime_directory,
    implementation_languages,
    language_specific_auditor_filenames,
)
from outcomeeng.validation.spx_version import (
    REQUIRED_SPX_VERSION,
    VERIFICATION_RUN_MINIMUM_SPX_VERSION,
    verification_run_floor_is_satisfied,
)


def spx_floor_provides_verification_run_lifecycle() -> bool:
    """Return whether the repository floor includes verification runs."""
    return verification_run_floor_is_satisfied(REQUIRED_SPX_VERSION)


def verification_run_floor_rejects_pre_capability_version() -> bool:
    """Return whether the floor validator rejects the preceding release."""
    return not verification_run_floor_is_satisfied(
        _preceding_patch_version(VERIFICATION_RUN_MINIMUM_SPX_VERSION)
    )


def implementation_auditor_is_the_only_implementation_wrapper() -> bool:
    """Return whether every live surface satisfies wrapper identity rules."""
    return _all_live_surfaces_pass(check_wrapper_surface)


def language_concern_skill_trios_exist() -> bool:
    """Return whether every live surface satisfies language trio rules."""
    return _all_live_surfaces_pass(check_language_concern_surface)


def implementation_audit_runtime_contains_only_skill() -> bool:
    """Return whether every live surface satisfies runtime shape rules."""
    return _all_live_surfaces_pass(check_runtime_surface)


def audit_contract_rejects_language_specific_wrapper() -> bool:
    """Return whether validation rejects a language-specific wrapper."""
    with _valid_surface() as surface:
        language = _source_language()
        filename = sorted(language_specific_auditor_filenames(language))[0]
        _touch(surface / language / AGENTS_DIR_NAME / filename)
        return bool(check_wrapper_surface(surface))


def audit_contract_rejects_incomplete_language_trio() -> bool:
    """Return whether validation rejects a missing language concern skill."""
    with _valid_surface() as surface:
        language = _source_language()
        concern = LANGUAGE_AUDIT_CONCERNS[-1]
        _language_concern_path(surface, language, concern).unlink()
        return bool(check_language_concern_surface(surface))


def audit_contract_rejects_extra_runtime_artifact() -> bool:
    """Return whether validation rejects an extra runtime artifact."""
    with _valid_surface() as surface:
        runtime_dir = implementation_audit_runtime_directory(surface)
        _touch(runtime_dir / f"{SKILL_FILENAME}.extra")
        return bool(check_runtime_surface(surface))


def audit_contract_rejects_missing_runtime_skill() -> bool:
    """Return whether validation rejects a missing runtime skill."""
    with _valid_surface() as surface:
        runtime_dir = implementation_audit_runtime_directory(surface)
        (runtime_dir / SKILL_FILENAME).unlink()
        return bool(check_runtime_surface(surface))


def _all_live_surfaces_pass(check: Callable[[Path], list[str]]) -> bool:
    return all(not check(Path(".") / relative) for relative in PLUGIN_SURFACE_PATHS)


@contextmanager
def _valid_surface() -> Iterator[Path]:
    with TemporaryDirectory() as temporary_directory:
        surface = Path(temporary_directory)
        language = _source_language()
        _touch(
            surface
            / language
            / SKILLS_DIR_NAME
            / LANGUAGE_CODE_SKILL_TEMPLATE.format(language=language)
            / SKILL_FILENAME
        )
        for concern in LANGUAGE_AUDIT_CONCERNS:
            _touch(_language_concern_path(surface, language, concern))
        _touch(
            surface
            / SPEC_TREE_PLUGIN_NAME
            / AGENTS_DIR_NAME
            / IMPLEMENTATION_AUDITOR_FILENAME
        )
        _touch(implementation_audit_runtime_directory(surface) / SKILL_FILENAME)
        yield surface


def _language_concern_path(surface: Path, language: str, concern: str) -> Path:
    return (
        surface
        / language
        / SKILLS_DIR_NAME
        / LANGUAGE_AUDIT_SKILL_TEMPLATE.format(language=language, concern=concern)
        / SKILL_FILENAME
    )


def _source_language() -> str:
    return implementation_languages(Path(".") / PLUGIN_SURFACE_PATHS[0])[0]


def _preceding_patch_version(version: str) -> str:
    parts = [int(part) for part in version.split(".")]
    parts[-1] -= 1
    return ".".join(str(part) for part in parts)


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
