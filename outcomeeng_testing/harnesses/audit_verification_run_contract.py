"""Harness for audit verification-run contract evidence."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
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
AUDIT_SUBJECT_PATH: Final = "file.txt"
IMPLEMENTATION_AUDIT_UNIT_ID: Final = "implementation:python:code"
IMPLEMENTATION_AUDIT_INPUT: Final = {
    "schema_version": 1,
    "request": {"kind": "implementation-audit-contract"},
}
IMPLEMENTATION_AUDIT_PRODUCER: Final = {
    "producerKind": "skill",
    "agentName": "implementation-auditor",
    "agentOwningPluginName": "spec-tree",
    "skillName": "audit-python-code",
    "skillOwningPluginName": "python",
    "invocationRole": "concern",
}
IMPLEMENTATION_AUDIT_RUN_DRIVER: Final = {
    "producerKind": "agent",
    "agentName": "implementation-auditor",
    "agentOwningPluginName": "spec-tree",
    "skillName": "audit-implementation",
    "skillOwningPluginName": "spec-tree",
    "invocationRole": "run-driver",
}
IMPLEMENTATION_AUDIT_SCOPE_UNIT: Final = {
    "unitId": IMPLEMENTATION_AUDIT_UNIT_ID,
    "auditClass": "implementation",
    "auditKind": "code",
    "subject": "partition:python",
    "coverageRequirement": "required",
    "coverageStatus": "audited",
    "priorContext": {
        "changedFilePartition": "python",
        "concernPartition": "code",
        "languagePartition": "python",
    },
    "expectedProducer": IMPLEMENTATION_AUDIT_PRODUCER,
    "recordedByRunDriver": IMPLEMENTATION_AUDIT_RUN_DRIVER,
}
IMPLEMENTATION_AUDIT_FINDING: Final = {
    "unitId": IMPLEMENTATION_AUDIT_UNIT_ID,
    "producerIdentity": IMPLEMENTATION_AUDIT_PRODUCER,
    "rule": "contract-probe",
    "severity": "blocking",
    "location": f"{AUDIT_SUBJECT_PATH}:1",
    "message": "verification-run compatibility probe",
    "evidence": {"observed": "probe", "expected": "accepted"},
}


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


def spx_audit_verification_run_lifecycle_accepts_implementation_payloads() -> bool:
    """Exercise the published verification-run contract used by audit skills."""
    with TemporaryDirectory() as temporary_directory:
        repository = Path(temporary_directory)
        _initialize_changeset_repository(repository)
        scope = _changeset_scope(repository)
        start_report = _run_spx_json(
            repository,
            (
                "verification",
                "run",
                "start",
                "--verification-type",
                "audit",
                "--scope-type",
                "changeset",
                "--scope",
                scope,
                "--input",
                "stdin",
            ),
            IMPLEMENTATION_AUDIT_INPUT,
        )
        run_token = _required_string(start_report, "runToken")
        scope_report = _run_spx_json(
            repository,
            _evidence_command("scope", scope, run_token, IMPLEMENTATION_AUDIT_UNIT_ID),
            _with_producer_provenance(IMPLEMENTATION_AUDIT_SCOPE_UNIT),
        )
        finding_report = _run_spx_json(
            repository,
            _evidence_command("finding", scope, run_token, "contract-finding"),
            _with_producer_provenance(IMPLEMENTATION_AUDIT_FINDING),
        )
        finish_report = _run_spx_json(
            repository,
            (
                "verification",
                "run",
                "finish",
                "--verification-type",
                "audit",
                "--scope-type",
                "changeset",
                "--scope",
                scope,
                "--run",
                run_token,
                "--terminal-status",
                "rejected",
            ),
        )
        render_report = _run_spx_json(
            repository,
            (
                "verification",
                "run",
                "render",
                "--verification-type",
                "audit",
                "--scope-type",
                "changeset",
                "--scope",
                scope,
                "--run",
                run_token,
            ),
        )

    scope_sequence = scope_report.get("sequence")
    finding_sequence = finding_report.get("sequence")
    observed = (
        isinstance(scope_sequence, int) and finding_sequence == scope_sequence + 1,
        finish_report.get("terminalStatus"),
        finish_report.get("sealed"),
        render_report.get("runToken"),
        render_report.get("findingCount"),
        render_report.get("sealed"),
        render_report.get("terminalStatus"),
    )
    expected = (True, "rejected", True, run_token, 1, True, "rejected")
    if observed != expected:
        raise AssertionError(
            f"verification-run projection mismatch: expected {expected!r}, "
            f"observed {observed!r}",
        )
    return True


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


def _initialize_changeset_repository(repository: Path) -> None:
    _run(repository, ("git", "init", "-q"))
    _run(repository, ("git", "config", "user.email", "test@example.com"))
    _run(repository, ("git", "config", "user.name", "Test User"))
    subject_path = repository / AUDIT_SUBJECT_PATH
    subject_path.write_text("before\n", encoding="utf-8")
    _run(repository, ("git", "add", AUDIT_SUBJECT_PATH))
    _run(repository, ("git", "commit", "-q", "-m", "initial"))
    subject_path.write_text("after\n", encoding="utf-8")
    _run(repository, ("git", "add", AUDIT_SUBJECT_PATH))
    _run(repository, ("git", "commit", "-q", "-m", "change"))


def _changeset_scope(repository: Path) -> str:
    head = _run(repository, ("git", "rev-parse", "HEAD")).stdout.strip()
    base = _run(repository, ("git", "rev-parse", "HEAD~1")).stdout.strip()
    return f"{base}..{head}"


def _evidence_command(
    evidence_kind: str,
    scope: str,
    run_token: str,
    idempotency_key: str,
) -> tuple[str, ...]:
    return (
        "verification",
        "run",
        evidence_kind,
        "add",
        "--verification-type",
        "audit",
        "--scope-type",
        "changeset",
        "--scope",
        scope,
        "--run",
        run_token,
        "--payload",
        "stdin",
        "--idempotency-key",
        idempotency_key,
    )


def _run_spx_json(
    repository: Path,
    arguments: tuple[str, ...],
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    input_text = None if payload is None else f"{json.dumps(payload)}\n"
    completed = _run(repository, ("spx", *arguments), input_text=input_text)
    parsed = json.loads(completed.stdout)
    if not isinstance(parsed, dict):
        raise TypeError("spx command did not return a JSON object")
    return parsed


def _with_producer_provenance(payload: Mapping[str, Any]) -> dict[str, Any]:
    workflow_pin = read_pinned_version(WORKFLOW_PATH.read_text(encoding="utf-8"))
    if workflow_pin is None:
        raise ValueError("CI workflow does not declare an SPX_VERSION pin")
    result = dict(payload)
    result["producerProvenance"] = {
        "agentOwningPluginVersion": _plugin_version("spec-tree"),
        "skillOwningPluginVersion": _plugin_version("python"),
        "toolVersion": workflow_pin,
    }
    return result


def _plugin_version(plugin_name: str) -> str:
    manifest_path = (
        REPO_ROOT / "src" / "plugins" / plugin_name / ".claude-plugin" / "plugin.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise TypeError(f"plugin manifest is not a JSON object: {manifest_path}")
    version = manifest.get("version")
    if not isinstance(version, str):
        raise TypeError(f"plugin manifest lacks string version: {manifest_path}")
    return version


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


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise TypeError(f"missing string field: {key}")
    return value
