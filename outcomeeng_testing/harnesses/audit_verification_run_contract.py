"""Harness for audit verification-run contract evidence."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from typing import Final

from outcomeeng.validation.plugins import (
    IMPLEMENTATION_AUDIT_SKILL_RELATIVE_PATH,
    IMPLEMENTATION_AUDITOR_AGENT_RELATIVE_PATH,
    PLUGIN_SURFACE_ROOTS,
    RETIRED_IMPLEMENTATION_AUDITOR_RELATIVE_PATHS,
    check_implementation_auditor_wrapper,
    check_language_concern_skill_trios,
    check_retired_audit_scripts,
    language_audit_skill_relative_path,
    language_code_skill_relative_path,
    retired_language_audit_skill_relative_path,
)
from outcomeeng.validation.implementation_audit_contract import (
    IMPLEMENTATION_AUDIT_CLASS,
    AuditCoverageStatus,
    AuditTerminalStatus,
    COVERAGE_STATUS_FIELD,
    EVENT_DATA_FIELD,
    EVENT_PAYLOAD_FIELD,
    EVENT_TYPE_FIELD,
    LANGUAGE_AUDIT_CONCERNS,
    PRIOR_CONTEXT_FIELD,
    RUN_EVENTS_FIELD,
    RUN_FINDING_COUNT_FIELD,
    RUN_SEALED_FIELD,
    RUN_TERMINAL_STATUS_FIELD,
    RUN_TOKEN_FIELD,
    RetiredAuditScript,
    SPEC_TREE_PLUGIN_NAME,
    SUBJECT_FIELD,
    UNIT_ID_FIELD,
    VERIFICATION_FINDING_EVENT_TYPE,
    VERIFICATION_SCOPE_EVENT_TYPE,
    expected_verification_projection,
    ImplementationAuditConcern,
    implementation_audit_concern_skill_name,
    implementation_audit_finding_payload,
    implementation_audit_input_payload,
    implementation_audit_provenance,
    implementation_audit_scope_payload,
    implementation_audit_subject_unit_id,
)
from outcomeeng.distribution.orchestration import SOURCE_PLUGINS_DIR
from outcomeeng.validation.spx_version import (
    REQUIRED_SPX_VERSION,
    SPX_COMMAND,
    VERIFICATION_RUN_MINIMUM_SPX_COMMAND,
    VERIFICATION_RUN_MINIMUM_SPX_VERSION,
    is_satisfied,
    parse_version,
    read_pinned_version,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
WORKFLOW_PATH: Final = REPO_ROOT / ".github" / "workflows" / "check.yml"


@dataclass(frozen=True)
class ImplementationAuditVerificationProbe:
    """One source-derived scenario case for the SPX lifecycle harness."""

    language: str
    concern: ImplementationAuditConcern
    subject_path: str
    finding_key: str
    request_kind: str
    rule: str
    message: str
    observed: str
    expected: str
    finding_count: int
    terminal_status: AuditTerminalStatus


def implementation_audit_verification_probe(
    language: str,
) -> ImplementationAuditVerificationProbe:
    """Derive the declared lifecycle scenario from production contracts."""
    concern = ImplementationAuditConcern.CODE
    subject_path = str(language_code_skill_relative_path(language))
    finding_key = implementation_audit_subject_unit_id(
        language,
        concern,
        subject_path,
    )
    concern_skill = implementation_audit_concern_skill_name(language, concern)
    return ImplementationAuditVerificationProbe(
        language=language,
        concern=concern,
        subject_path=subject_path,
        finding_key=finding_key,
        request_kind=IMPLEMENTATION_AUDIT_CLASS,
        rule=concern_skill,
        message=concern_skill,
        observed=AuditCoverageStatus.AUDITED.value,
        expected=AuditTerminalStatus.REJECTED.value,
        finding_count=1,
        terminal_status=AuditTerminalStatus.REJECTED,
    )


def spx_floor_and_ci_pin_meet_verification_run_minimum() -> bool:
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


def spx_floor_rejects_version_below_verification_run_minimum() -> bool:
    """Exercise the version oracle against a source-derived below-floor version."""
    floor = parse_version(VERIFICATION_RUN_MINIMUM_SPX_VERSION)
    lower = ".".join(str(part) for part in (*floor[:-1], floor[-1] - 1))
    return not is_satisfied(lower, VERIFICATION_RUN_MINIMUM_SPX_VERSION)


def audited_scope_payload_carries_concern_evidence() -> bool:
    """Return whether audited scope preserves paths and concern completion."""
    language = _source_language_plugin_name()
    if language is None:
        return False
    probe = implementation_audit_verification_probe(language)
    payload = implementation_audit_scope_payload(
        probe.language,
        probe.concern,
        subject_path=probe.subject_path,
    )
    prior_context = payload.get(PRIOR_CONTEXT_FIELD)
    if not isinstance(prior_context, Mapping):
        return False
    return (
        payload.get(SUBJECT_FIELD) == probe.subject_path
        and payload.get(COVERAGE_STATUS_FIELD) == AuditCoverageStatus.AUDITED.value
        and prior_context.get("changedFilePartition") == probe.language
        and prior_context.get("concernPartition") == probe.concern.value
        and prior_context.get("languagePartition") == probe.language
    )


def audited_scope_payload_rejects_empty_subject_paths() -> bool:
    """Return whether audited scope rejects an empty inspected path set."""
    language = _source_language_plugin_name()
    if language is None:
        return False
    probe = implementation_audit_verification_probe(language)
    try:
        implementation_audit_scope_payload(
            probe.language,
            probe.concern,
            subject_path="",
        )
    except ValueError:
        return True
    return False


def audit_finding_payload_rejects_empty_subject_paths() -> bool:
    """Return whether an audit finding rejects an empty inspected path."""
    language = _source_language_plugin_name()
    if language is None:
        return False
    probe = implementation_audit_verification_probe(language)
    try:
        implementation_audit_finding_payload(
            probe.language,
            probe.concern,
            rule=probe.rule,
            subject_path="",
            message=probe.message,
            observed=probe.observed,
            expected=probe.expected,
        )
    except ValueError:
        return True
    return False


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


def implementation_audit_coverage_distinguishes_artifact_ownership() -> bool:
    """Return whether required coverage excludes non-implementation artifacts."""
    skill_path = (
        REPO_ROOT
        / SOURCE_PLUGINS_DIR
        / IMPLEMENTATION_AUDIT_SKILL_RELATIVE_PATH
        / "SKILL.md"
    )
    skill_text = skill_path.read_text(encoding="utf-8")
    coverage_model = skill_text.partition("<coverage_model>")[2].partition(
        "</coverage_model>",
    )[0]
    return all(
        clause in coverage_model
        for clause in (
            "Classify every changed path by implementation-audit ownership",
            "Implementation-owned artifacts are implementation code, linked tests",
            "Non-implementation artifacts include specs, decisions, coordination notes",
            "optional `not-applicable`",
            "never carries `unsupported` or `missing-skill`",
            "Reserve `unsupported` for an implementation-owned artifact",
        )
    )


def implementation_audit_scripts_are_absent_and_rejected() -> bool:
    """Return whether real trees are clean and every retired script is rejected."""
    if check_retired_audit_scripts(REPO_ROOT):
        return False

    return all(
        _retired_script_is_rejected(surface_root, retired_script.value)
        for surface_root in PLUGIN_SURFACE_ROOTS
        for retired_script in RetiredAuditScript
    )


def spx_audit_verification_run_lifecycle_accepts_implementation_payloads() -> bool:
    """Exercise the published verification-run contract used by audit skills."""
    return _spx_audit_verification_run_lifecycle_accepts_implementation_payloads(
        SPX_COMMAND
    )


def minimum_spx_release_accepts_implementation_audit_lifecycle() -> bool:
    """Exercise the implementation-audit lifecycle against the minimum release."""
    reported_version = _run(
        Path.cwd(),
        (*VERIFICATION_RUN_MINIMUM_SPX_COMMAND, "--version"),
    ).stdout.strip()
    return (
        reported_version == VERIFICATION_RUN_MINIMUM_SPX_VERSION
        and _spx_audit_verification_run_lifecycle_accepts_implementation_payloads(
            VERIFICATION_RUN_MINIMUM_SPX_COMMAND
        )
    )


def _spx_audit_verification_run_lifecycle_accepts_implementation_payloads(
    spx_command: tuple[str, ...],
) -> bool:
    language = _source_language_plugin_name()
    if language is None:
        return False
    probe = implementation_audit_verification_probe(language)
    with TemporaryDirectory() as temporary_directory:
        repository = Path(temporary_directory)
        _initialize_changeset_repository(repository, probe)
        scope = _changeset_scope(repository)
        unit_id = implementation_audit_subject_unit_id(
            probe.language,
            probe.concern,
            probe.subject_path,
        )
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
            implementation_audit_input_payload(probe.request_kind),
            spx_command=spx_command,
        )
        run_token = _required_string(start_report, RUN_TOKEN_FIELD)
        _run_spx_json(
            repository,
            _evidence_command("scope", scope, run_token, unit_id),
            _with_producer_provenance(
                implementation_audit_scope_payload(
                    probe.language,
                    probe.concern,
                    subject_path=probe.subject_path,
                ),
                language=probe.language,
            ),
            spx_command=spx_command,
        )
        _run_spx_json(
            repository,
            _evidence_command(
                "finding",
                scope,
                run_token,
                probe.finding_key,
            ),
            _with_producer_provenance(
                implementation_audit_finding_payload(
                    probe.language,
                    probe.concern,
                    rule=probe.rule,
                    subject_path=probe.subject_path,
                    message=probe.message,
                    observed=probe.observed,
                    expected=probe.expected,
                ),
                language=probe.language,
            ),
            spx_command=spx_command,
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
                probe.terminal_status.value,
            ),
            spx_command=spx_command,
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
            spx_command=spx_command,
        )

    observed = (
        finish_report.get(RUN_TERMINAL_STATUS_FIELD),
        finish_report.get(RUN_SEALED_FIELD),
        render_report.get(RUN_TOKEN_FIELD),
        render_report.get(RUN_FINDING_COUNT_FIELD),
        render_report.get(RUN_SEALED_FIELD),
        render_report.get(RUN_TERMINAL_STATUS_FIELD),
    )
    expected = expected_verification_projection(
        run_token,
        finding_count=probe.finding_count,
        terminal_status=probe.terminal_status,
    )[1:]
    if observed != expected:
        raise AssertionError(
            f"verification-run projection mismatch: expected {expected!r}, "
            f"observed {observed!r}",
        )
    _assert_rendered_scope_preserves_concern_evidence(
        render_report,
        unit_id=unit_id,
        subject_path=probe.subject_path,
        finding_count=probe.finding_count,
    )
    return True


def _assert_rendered_scope_preserves_concern_evidence(
    render_report: Mapping[str, object],
    *,
    unit_id: str,
    subject_path: str,
    finding_count: int,
) -> None:
    events = render_report.get(RUN_EVENTS_FIELD)
    if not isinstance(events, list):
        raise AssertionError("verification-run render omitted its event list")
    matching_scope_payloads: list[Mapping[str, object]] = []
    matching_finding_count = 0
    for event in events:
        if not isinstance(event, Mapping):
            continue
        data = event.get(EVENT_DATA_FIELD)
        if not isinstance(data, Mapping):
            continue
        payload = data.get(EVENT_PAYLOAD_FIELD)
        if not isinstance(payload, Mapping) or payload.get(UNIT_ID_FIELD) != unit_id:
            continue
        if event.get(EVENT_TYPE_FIELD) == VERIFICATION_SCOPE_EVENT_TYPE:
            matching_scope_payloads.append(payload)
        elif event.get(EVENT_TYPE_FIELD) == VERIFICATION_FINDING_EVENT_TYPE:
            matching_finding_count += 1
    expected_scope = {
        SUBJECT_FIELD: subject_path,
        COVERAGE_STATUS_FIELD: AuditCoverageStatus.AUDITED.value,
    }
    scope_matches = any(
        all(payload.get(key) == value for key, value in expected_scope.items())
        for payload in matching_scope_payloads
    )
    if not scope_matches or matching_finding_count != finding_count:
        raise AssertionError(
            f"rendered scope {unit_id!r} omitted preserved concern evidence: "
            f"expected scope {expected_scope!r} and {finding_count} findings, "
            f"observed {matching_scope_payloads!r} and {matching_finding_count}",
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


def _initialize_changeset_repository(
    repository: Path,
    probe: ImplementationAuditVerificationProbe,
) -> None:
    _run(repository, ("git", "init", "-q"))
    _run(repository, ("git", "config", "user.email", "test@example.com"))
    _run(repository, ("git", "config", "user.name", "Test User"))
    subject_path = repository / probe.subject_path
    subject_path.parent.mkdir(parents=True)
    subject_path.write_text("before\n", encoding="utf-8")
    _run(repository, ("git", "add", probe.subject_path))
    _run(repository, ("git", "commit", "-q", "-m", "initial"))
    subject_path.write_text("after\n", encoding="utf-8")
    _run(repository, ("git", "add", probe.subject_path))
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
    *,
    spx_command: tuple[str, ...] = SPX_COMMAND,
) -> dict[str, Any]:
    input_text = None if payload is None else f"{json.dumps(payload)}\n"
    completed = _run(repository, (*spx_command, *arguments), input_text=input_text)
    parsed = json.loads(completed.stdout)
    if not isinstance(parsed, dict):
        raise TypeError("spx command did not return a JSON object")
    return parsed


def _with_producer_provenance(
    payload: Mapping[str, Any],
    *,
    language: str,
) -> dict[str, Any]:
    workflow_pin = read_pinned_version(WORKFLOW_PATH.read_text(encoding="utf-8"))
    if workflow_pin is None:
        raise ValueError("CI workflow does not declare an SPX_VERSION pin")
    result = dict(payload)
    result["producerProvenance"] = implementation_audit_provenance(
        agent_plugin_version=_plugin_version(SPEC_TREE_PLUGIN_NAME),
        language_plugin_version=_plugin_version(language),
        tool_version=workflow_pin,
    )
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
