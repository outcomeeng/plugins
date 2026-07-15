"""Repository-owned audit contract checks."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, cast

from outcomeeng.validation.audit_artifacts import (
    AGENTS_DIR_NAME,
    IMPLEMENTATION_AUDITOR_FILENAME,
    IMPLEMENTATION_AUDIT_SKILL_NAME,
    LANGUAGE_AUDIT_CONCERNS,
    LANGUAGE_AUDIT_SKILL_TEMPLATE,
    LANGUAGE_CODE_SKILL_TEMPLATE,
    PLUGIN_SURFACE_PATHS,
    RETIRED_AUDIT_RUNTIME_FILENAMES,
    SKILL_FILENAME,
    SKILLS_DIR_NAME,
    SPEC_TREE_PLUGIN_NAME,
    check_audit_runtime_surface,
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

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
AUDIT_PAYLOAD_FIXTURE: Final = (
    REPO_ROOT
    / "outcomeeng_testing"
    / "fixtures"
    / "audit_verification_run_contract.json"
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


def audit_runtime_trees_exclude_retired_artifacts() -> bool:
    """Return whether every live audit runtime satisfies artifact rules."""
    return _all_live_surfaces_pass(check_audit_runtime_surface)


def spx_verification_run_accepts_implementation_audit_payloads() -> bool:
    """Exercise the SPX lifecycle used by implementation-audit orchestration."""
    language = _source_language()
    concern = LANGUAGE_AUDIT_CONCERNS[0]
    agent_name = Path(IMPLEMENTATION_AUDITOR_FILENAME).stem
    leaf_skill = LANGUAGE_AUDIT_SKILL_TEMPLATE.format(
        language=language,
        concern=concern,
    )
    subject = Path(__file__).name
    unit_id = f"{language}-{concern}"
    rule = spx_verification_run_accepts_implementation_audit_payloads.__name__
    scope_payload, finding_payload = _audit_payloads(
        {
            "{{UNIT_ID}}": unit_id,
            "{{LANGUAGE}}": language,
            "{{CONCERN}}": concern,
            "{{SUBJECT}}": subject,
            "{{AGENT_NAME}}": agent_name,
            "{{SPEC_TREE_PLUGIN}}": SPEC_TREE_PLUGIN_NAME,
            "{{LEAF_SKILL}}": leaf_skill,
            "{{DRIVER_SKILL}}": IMPLEMENTATION_AUDIT_SKILL_NAME,
            "{{SPEC_TREE_VERSION}}": _plugin_version(SPEC_TREE_PLUGIN_NAME),
            "{{LANGUAGE_VERSION}}": _plugin_version(language),
            "{{RULE}}": rule,
            "{{MESSAGE}}": (
                spx_verification_run_accepts_implementation_audit_payloads.__doc__
                or rule
            ),
        }
    )

    with TemporaryDirectory() as temporary_directory:
        repository = Path(temporary_directory)
        _initialize_changeset_repository(repository, subject)
        scope = _changeset_scope(repository)
        start_report = _run_spx(
            repository,
            ("start",),
            scope,
            payload={},
        )
        run_token = _required_string(start_report, "runToken")
        scope_report = _run_spx(
            repository,
            ("scope", "add"),
            scope,
            run_token=run_token,
            payload=scope_payload,
            idempotency_key=unit_id,
        )
        finding_report = _run_spx(
            repository,
            ("finding", "add"),
            scope,
            run_token=run_token,
            payload=finding_payload,
            idempotency_key=rule,
        )
        finish_report = _run_spx(
            repository,
            ("finish",),
            scope,
            run_token=run_token,
            terminal_status="rejected",
        )
        render_report = _run_spx(
            repository,
            ("render",),
            scope,
            run_token=run_token,
        )

    scope_sequence = scope_report.get("sequence")
    return (
        isinstance(scope_sequence, int)
        and finding_report.get("sequence") == scope_sequence + 1
        and finish_report.get("terminalStatus") == "rejected"
        and finish_report.get("sealed") is True
        and render_report.get("runToken") == run_token
        and render_report.get("findingCount") == 1
        and render_report.get("sealed") is True
        and render_report.get("terminalStatus") == "rejected"
    )


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


def audit_contract_rejects_retired_artifact_in_other_runtime() -> bool:
    """Return whether validation rejects retired files in another audit skill."""
    with _valid_surface() as surface:
        runtime_dir = surface / SPEC_TREE_PLUGIN_NAME / SKILLS_DIR_NAME / "audit-tests"
        _touch(runtime_dir / SKILL_FILENAME)
        _touch(runtime_dir / "scripts" / RETIRED_AUDIT_RUNTIME_FILENAMES[0])
        return bool(check_audit_runtime_surface(surface))


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


def _audit_payloads(bindings: Mapping[str, str]) -> tuple[dict[str, object], ...]:
    text = AUDIT_PAYLOAD_FIXTURE.read_text(encoding="utf-8")
    for placeholder, replacement in bindings.items():
        text = text.replace(placeholder, replacement)
    payloads = cast(object, json.loads(text))
    if not isinstance(payloads, list) or not all(
        isinstance(payload, dict) for payload in payloads
    ):
        raise TypeError("audit verification fixture is not an object array")
    return tuple(cast(dict[str, object], payload) for payload in payloads)


def _initialize_changeset_repository(repository: Path, subject: str) -> None:
    _run(repository, ("git", "init", "-q"))
    _run(repository, ("git", "config", "user.email", "audit@example.com"))
    _run(repository, ("git", "config", "user.name", "Audit Contract"))
    subject_path = repository / subject
    subject_path.write_text("", encoding="utf-8")
    _run(repository, ("git", "add", subject))
    _run(repository, ("git", "commit", "-q", "-m", "initial"))
    subject_path.write_text(__doc__ or subject, encoding="utf-8")
    _run(repository, ("git", "add", subject))
    _run(repository, ("git", "commit", "-q", "-m", "change"))


def _changeset_scope(repository: Path) -> str:
    base = _run(repository, ("git", "rev-parse", "HEAD~1")).stdout.strip()
    head = _run(repository, ("git", "rev-parse", "HEAD")).stdout.strip()
    return f"{base}..{head}"


def _run_spx(
    repository: Path,
    action: tuple[str, ...],
    scope: str,
    *,
    run_token: str | None = None,
    payload: Mapping[str, object] | None = None,
    idempotency_key: str | None = None,
    terminal_status: str | None = None,
) -> dict[str, object]:
    command = (
        "spx",
        "verification",
        "run",
        *action,
        "--verification-type",
        "audit",
        "--scope-type",
        "changeset",
        "--scope",
        scope,
    )
    if action == ("start",):
        command += ("--input", "stdin")
    if run_token is not None:
        command += ("--run", run_token)
    if idempotency_key is not None:
        command += ("--payload", "stdin", "--idempotency-key", idempotency_key)
    if terminal_status is not None:
        command += ("--terminal-status", terminal_status)
    input_text = None if payload is None else f"{json.dumps(payload)}\n"
    parsed = cast(
        object,
        json.loads(_run(repository, command, input_text).stdout),
    )
    if not isinstance(parsed, dict):
        raise TypeError("spx command did not return a JSON object")
    return cast(dict[str, object], parsed)


def _plugin_version(plugin_name: str) -> str:
    manifest_path = (
        REPO_ROOT
        / PLUGIN_SURFACE_PATHS[0]
        / plugin_name
        / ".claude-plugin"
        / "plugin.json"
    )
    manifest = cast(object, json.loads(manifest_path.read_text(encoding="utf-8")))
    if not isinstance(manifest, dict):
        raise TypeError(f"plugin manifest is not a JSON object: {manifest_path}")
    return _required_string(manifest, "version")


def _run(
    repository: Path,
    arguments: tuple[str, ...],
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=repository,
        input=input_text,
        text=True,
        check=True,
        capture_output=True,
    )


def _required_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise TypeError(f"missing string field: {key}")
    return value


def _preceding_patch_version(version: str) -> str:
    parts = [int(part) for part in version.split(".")]
    parts[-1] -= 1
    return ".".join(str(part) for part in parts)


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
