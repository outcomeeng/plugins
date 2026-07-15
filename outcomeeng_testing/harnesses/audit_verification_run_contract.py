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
    LANGUAGE_AUDIT_CONCERNS,
    LANGUAGE_AUDIT_SKILL_TEMPLATE,
    LANGUAGE_CODE_SKILL_TEMPLATE,
    PLUGIN_SURFACE_PATHS,
    RETIRED_AUDIT_RUNTIME_FILENAMES,
    RETIRED_IMPLEMENTATION_AUDITOR_FILENAMES,
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
from outcomeeng.validation.implementation_audit_contract import (
    RUN_FINDING_COUNT_FIELD,
    RUN_SEALED_FIELD,
    RUN_SEQUENCE_FIELD,
    RUN_TERMINAL_STATUS_FIELD,
    RUN_TOKEN_FIELD,
    AuditTerminalStatus,
    ImplementationAuditConcern,
    expected_verification_projection,
    implementation_audit_finding_payload,
    implementation_audit_input_payload,
    implementation_audit_provenance,
    implementation_audit_scope_payload,
    implementation_audit_unit_id,
)
from outcomeeng.validation.spx_version import (
    REQUIRED_SPX_VERSION,
    VERIFICATION_RUN_MINIMUM_SPX_VERSION,
    VERIFICATION_RUN_REQUIRED_COMMANDS,
    is_satisfied,
    parse_version,
    verification_run_floor_is_satisfied,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
SPX_RELEASE_FIXTURE: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "spx_verification_run_release.json"
)
SPX_VERIFICATION_RUN_HELP_FIXTURE: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "spx_verification_run_help.txt"
)


def spx_floor_provides_verification_run_lifecycle() -> bool:
    """Return whether the repository floor includes verification runs."""
    release = cast(
        object,
        json.loads(SPX_RELEASE_FIXTURE.read_text(encoding="utf-8")),
    )
    if not isinstance(release, dict):
        raise TypeError("SPX release fixture is not a JSON object")
    published_version = _required_string(release, "version")
    integrity = _required_string(release, "dist.integrity")
    tarball = _required_string(release, "dist.tarball")
    help_text = SPX_VERIFICATION_RUN_HELP_FIXTURE.read_text(encoding="utf-8")
    return (
        published_version == VERIFICATION_RUN_MINIMUM_SPX_VERSION
        and integrity.startswith("sha512-")
        and tarball.endswith(f"spx-{published_version}.tgz")
        and is_satisfied(REQUIRED_SPX_VERSION, published_version)
        and verification_run_floor_is_satisfied(REQUIRED_SPX_VERSION)
        and all(
            f"  {command}" in help_text
            for command in VERIFICATION_RUN_REQUIRED_COMMANDS
        )
    )


def audit_contract_rejects_below_verification_run_floor() -> bool:
    """Return whether validation rejects the version before the published floor."""
    minimum = parse_version(VERIFICATION_RUN_MINIMUM_SPX_VERSION)
    below_floor = ".".join(str(part) for part in (*minimum[:-1], minimum[-1] - 1))
    return not verification_run_floor_is_satisfied(below_floor)


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
    if not spx_floor_provides_verification_run_lifecycle():
        return False

    rule = spx_verification_run_accepts_implementation_audit_payloads.__name__
    terminal_status = AuditTerminalStatus.REJECTED

    with TemporaryDirectory() as temporary_directory:
        repository = Path(temporary_directory)
        scope, run_token, scope_report, finding_report = (
            _record_implementation_audit_finding(
                repository,
                rule,
                spx_verification_run_accepts_implementation_audit_payloads.__doc__
                or rule,
            )
        )
        finish_report = _run_spx(
            repository,
            ("finish",),
            scope,
            run_token=run_token,
            terminal_status=terminal_status.value,
        )
        render_report = _run_spx(
            repository,
            ("render",),
            scope,
            run_token=run_token,
        )

    scope_sequence = scope_report.get(RUN_SEQUENCE_FIELD)
    actual_projection = (
        isinstance(scope_sequence, int)
        and finding_report.get(RUN_SEQUENCE_FIELD) == scope_sequence + 1,
        finish_report.get(RUN_TERMINAL_STATUS_FIELD),
        finish_report.get(RUN_SEALED_FIELD),
        render_report.get(RUN_TOKEN_FIELD),
        render_report.get(RUN_FINDING_COUNT_FIELD),
        render_report.get(RUN_SEALED_FIELD),
        render_report.get(RUN_TERMINAL_STATUS_FIELD),
    )
    return actual_projection == expected_verification_projection(
        run_token,
        finding_count=1,
        terminal_status=terminal_status,
    )


def spx_verification_run_rejects_mismatched_terminal_status() -> bool:
    """Return whether SPX rejects approval after a blocking finding."""
    if not spx_floor_provides_verification_run_lifecycle():
        return False

    rule = spx_verification_run_rejects_mismatched_terminal_status.__name__

    with TemporaryDirectory() as temporary_directory:
        repository = Path(temporary_directory)
        scope, run_token, _, _ = _record_implementation_audit_finding(
            repository,
            rule,
            spx_verification_run_rejects_mismatched_terminal_status.__doc__ or rule,
        )
        try:
            _run_spx(
                repository,
                ("finish",),
                scope,
                run_token=run_token,
                terminal_status=AuditTerminalStatus.APPROVED.value,
            )
        except subprocess.CalledProcessError:
            return True

    return False


def audit_contract_rejects_language_specific_wrapper() -> bool:
    """Return whether validation rejects a language-specific wrapper."""
    with _valid_surface() as surface:
        language = _source_language()
        filename = sorted(language_specific_auditor_filenames(language))[0]
        _touch(surface / language / AGENTS_DIR_NAME / filename)
        return bool(check_wrapper_surface(surface))


def audit_contract_rejects_retired_implementation_wrappers() -> bool:
    """Return whether validation rejects every retired wrapper name."""
    return all(
        _retired_implementation_wrapper_is_rejected(filename)
        for filename in RETIRED_IMPLEMENTATION_AUDITOR_FILENAMES
    )


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


def _retired_implementation_wrapper_is_rejected(filename: str) -> bool:
    with _valid_surface() as surface:
        _touch(surface / SPEC_TREE_PLUGIN_NAME / AGENTS_DIR_NAME / filename)
        return bool(check_wrapper_surface(surface))


def _source_language() -> str:
    return implementation_languages(Path(".") / PLUGIN_SURFACE_PATHS[0])[0]


def _record_implementation_audit_finding(
    repository: Path,
    rule: str,
    message: str,
) -> tuple[str, str, dict[str, object], dict[str, object]]:
    language = _source_language()
    concern = ImplementationAuditConcern(LANGUAGE_AUDIT_CONCERNS[0])
    subject = Path(__file__).name
    provenance = implementation_audit_provenance(
        agent_plugin_version=_plugin_version(SPEC_TREE_PLUGIN_NAME),
        language_plugin_version=_plugin_version(language),
        tool_version=_spx_version(),
    )
    unit_id = implementation_audit_unit_id(language, concern)
    _initialize_changeset_repository(repository, subject)
    scope = _changeset_scope(repository)
    start_report = _run_spx(
        repository,
        ("start",),
        scope,
        payload=implementation_audit_input_payload(rule),
    )
    run_token = _required_string(start_report, RUN_TOKEN_FIELD)
    scope_report = _run_spx(
        repository,
        ("scope", "add"),
        scope,
        run_token=run_token,
        payload=implementation_audit_scope_payload(
            language,
            concern,
            subject_path=subject,
            producer_provenance=provenance,
        ),
        idempotency_key=unit_id,
    )
    finding_report = _run_spx(
        repository,
        ("finding", "add"),
        scope,
        run_token=run_token,
        payload=implementation_audit_finding_payload(
            language,
            concern,
            rule=rule,
            subject_path=subject,
            message=message,
            observed=subject,
            expected=subject,
            producer_provenance=provenance,
        ),
        idempotency_key=rule,
    )
    return scope, run_token, scope_report, finding_report


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


def _spx_version() -> str:
    return _run(REPO_ROOT, ("spx", "--version")).stdout.strip()


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


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
