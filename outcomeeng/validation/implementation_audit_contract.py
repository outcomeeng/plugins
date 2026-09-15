"""Source-owned implementation-audit payload and projection contracts."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Final

SPEC_TREE_PLUGIN_NAME: Final = "spec-tree"
IMPLEMENTATION_AUDITOR_AGENT_NAME: Final = "implementation-auditor"
IMPLEMENTATION_AUDIT_SKILL_NAME: Final = "audit-implementation"
IMPLEMENTATION_AUDIT_CLASS: Final = "implementation"

RUN_TOKEN_FIELD: Final = "runToken"
RUN_SEQUENCE_FIELD: Final = "sequence"
RUN_TERMINAL_STATUS_FIELD: Final = "terminalStatus"
RUN_SEALED_FIELD: Final = "sealed"
RUN_FINDING_COUNT_FIELD: Final = "findingCount"
RUN_RESOLVED_SCOPE_FIELD: Final = "resolvedScope"


class ImplementationAuditConcern(StrEnum):
    """Concern partitions required for every implementation audit."""

    CODE = "code"
    TESTS = "tests"
    ARCHITECTURE = "architecture"


class ScopeUnitField(StrEnum):
    """Top-level fields of one SPX audit scope unit."""

    UNIT_ID = "unitId"
    AUDIT_CLASS = "auditClass"
    AUDIT_KIND = "auditKind"
    SUBJECT = "subject"
    COVERAGE_REQUIREMENT = "coverageRequirement"
    COVERAGE_STATUS = "coverageStatus"
    PRIOR_CONTEXT = "priorContext"
    EXPECTED_PRODUCER = "expectedProducer"
    RECORDED_BY_RUN_DRIVER = "recordedByRunDriver"
    PRODUCER_PROVENANCE = "producerProvenance"


class PriorContextField(StrEnum):
    """Fields of a scope unit's ``priorContext`` object."""

    CHANGED_FILE_PARTITION = "changedFilePartition"
    CONCERN_PARTITION = "concernPartition"
    LANGUAGE_PARTITION = "languagePartition"


class AuditCoverageRequirement(StrEnum):
    """Coverage requirement values accepted by SPX verification runs."""

    REQUIRED = "required"
    OPTIONAL = "optional"


class AuditCoverageStatus(StrEnum):
    """Coverage status values an implementation-audit unit may carry.

    ``AUDITED``, ``NOT_APPLICABLE``, ``UNSUPPORTED``, and ``MISSING_SKILL`` are
    the statuses a required unit may reach; ``SKIPPED`` is reserved for an
    optional unit. No unit carries ``incomplete`` — a required unit that reaches
    none of its four statuses stops the run with a blocked diagnostic instead of
    sealing.
    """

    AUDITED = "audited"
    NOT_APPLICABLE = "not-applicable"
    UNSUPPORTED = "unsupported"
    MISSING_SKILL = "missing-skill"
    SKIPPED = "skipped"


class AuditFindingSeverity(StrEnum):
    """Finding severity values accepted by SPX verification runs."""

    BLOCKING = "blocking"
    DEBT = "debt"


class AuditTerminalStatus(StrEnum):
    """Terminal statuses emitted by implementation-audit verification runs."""

    APPROVED = "approved"
    REJECTED = "rejected"


LANGUAGE_AUDIT_CONCERNS: Final = tuple(
    concern.value for concern in ImplementationAuditConcern
)


def implementation_audit_unit_id(
    language: str,
    concern: ImplementationAuditConcern,
    *,
    subject_path: str,
) -> str:
    """Return the stable identity for one subject and language concern."""
    return f"{IMPLEMENTATION_AUDIT_CLASS}:{language}:{concern.value}:{subject_path}"


def implementation_audit_finding_key(
    language: str,
    concern: ImplementationAuditConcern,
    *,
    subject_path: str,
    rule: str,
) -> str:
    """Return the stable identity for one finding on one subject and concern."""
    unit_id = implementation_audit_unit_id(
        language,
        concern,
        subject_path=subject_path,
    )
    return f"{unit_id}:{rule}"


def implementation_audit_producer_identity(
    language: str,
    concern: ImplementationAuditConcern,
) -> dict[str, object]:
    """Return the concern producer identity recorded in SPX evidence."""
    return {
        "producerKind": "skill",
        "agentName": IMPLEMENTATION_AUDITOR_AGENT_NAME,
        "agentOwningPluginName": SPEC_TREE_PLUGIN_NAME,
        "skillName": f"audit-{language}-{concern.value}",
        "skillOwningPluginName": language,
        "invocationRole": "leaf-skill",
    }


def implementation_audit_run_driver_identity() -> dict[str, object]:
    """Return the wrapper identity that records SPX evidence."""
    return {
        "producerKind": "agent",
        "agentName": IMPLEMENTATION_AUDITOR_AGENT_NAME,
        "agentOwningPluginName": SPEC_TREE_PLUGIN_NAME,
        "skillName": IMPLEMENTATION_AUDIT_SKILL_NAME,
        "skillOwningPluginName": SPEC_TREE_PLUGIN_NAME,
        "invocationRole": "run-driver",
    }


def implementation_audit_input_payload(request_kind: str) -> dict[str, object]:
    """Return one implementation-audit run-start input payload."""
    return {
        "schema_version": 1,
        "request": {"kind": request_kind},
    }


def implementation_audit_scope_payload(
    language: str,
    concern: ImplementationAuditConcern,
    *,
    subject_path: str,
    producer_provenance: Mapping[str, object],
) -> dict[str, object]:
    """Return one audited implementation coverage unit."""
    subject_path = _require_subject_path(subject_path)
    return {
        ScopeUnitField.UNIT_ID: implementation_audit_unit_id(
            language,
            concern,
            subject_path=subject_path,
        ),
        ScopeUnitField.AUDIT_CLASS: IMPLEMENTATION_AUDIT_CLASS,
        ScopeUnitField.AUDIT_KIND: concern.value,
        ScopeUnitField.SUBJECT: subject_path,
        ScopeUnitField.COVERAGE_REQUIREMENT: AuditCoverageRequirement.REQUIRED.value,
        ScopeUnitField.COVERAGE_STATUS: AuditCoverageStatus.AUDITED.value,
        ScopeUnitField.PRIOR_CONTEXT: {
            PriorContextField.CHANGED_FILE_PARTITION: subject_path,
            PriorContextField.CONCERN_PARTITION: concern.value,
            PriorContextField.LANGUAGE_PARTITION: language,
        },
        ScopeUnitField.EXPECTED_PRODUCER: implementation_audit_producer_identity(
            language,
            concern,
        ),
        ScopeUnitField.RECORDED_BY_RUN_DRIVER: implementation_audit_run_driver_identity(),
        ScopeUnitField.PRODUCER_PROVENANCE: dict(producer_provenance),
    }


ACCOUNTING_RECORD_KIND: Final = "coverage-gap"
# A unit key always carries a language segment; a record with no language
# partition renders it as this literal.
UNKNOWN_LANGUAGE_SEGMENT: Final = "unknown"


def implementation_audit_accounting_unit_id(*, subject_path: str) -> str:
    """Return the stable identity for one unclaimed path's accounting record."""
    return (
        f"{IMPLEMENTATION_AUDIT_CLASS}:{UNKNOWN_LANGUAGE_SEGMENT}:"
        f"{ACCOUNTING_RECORD_KIND}:{subject_path}"
    )


def implementation_audit_accounting_payload(*, subject_path: str) -> dict[str, object]:
    """Return the accounting record for a resolved path no language concern claimed.

    The record states that the path was considered and left to its
    artifact-type auditor: it claims no coverage, names no language, and never
    rejects a run. No leaf skill is expected to cover it, so the run driver's
    own identity stands as its expected producer, and no provenance is recorded.
    """
    subject_path = _require_subject_path(subject_path)
    return {
        ScopeUnitField.UNIT_ID: implementation_audit_accounting_unit_id(
            subject_path=subject_path
        ),
        ScopeUnitField.AUDIT_CLASS: IMPLEMENTATION_AUDIT_CLASS,
        ScopeUnitField.AUDIT_KIND: ACCOUNTING_RECORD_KIND,
        ScopeUnitField.SUBJECT: subject_path,
        ScopeUnitField.COVERAGE_REQUIREMENT: AuditCoverageRequirement.OPTIONAL.value,
        ScopeUnitField.COVERAGE_STATUS: AuditCoverageStatus.SKIPPED.value,
        ScopeUnitField.PRIOR_CONTEXT: {
            PriorContextField.CHANGED_FILE_PARTITION: subject_path,
            PriorContextField.CONCERN_PARTITION: ACCOUNTING_RECORD_KIND,
        },
        ScopeUnitField.EXPECTED_PRODUCER: implementation_audit_run_driver_identity(),
        ScopeUnitField.RECORDED_BY_RUN_DRIVER: implementation_audit_run_driver_identity(),
    }


def implementation_audit_finding_payload(
    language: str,
    concern: ImplementationAuditConcern,
    *,
    rule: str,
    subject_path: str,
    message: str,
    observed: str,
    expected: str,
    producer_provenance: Mapping[str, object],
) -> dict[str, object]:
    """Return one valid blocking implementation-audit finding."""
    subject_path = _require_subject_path(subject_path)
    return {
        "unitId": implementation_audit_unit_id(
            language,
            concern,
            subject_path=subject_path,
        ),
        "producerIdentity": implementation_audit_producer_identity(
            language,
            concern,
        ),
        "producerProvenance": dict(producer_provenance),
        "rule": rule,
        "severity": AuditFindingSeverity.BLOCKING.value,
        "location": f"{subject_path}:1",
        "message": message,
        "evidence": {"observed": observed, "expected": expected},
    }


def implementation_audit_provenance(
    *,
    agent_plugin_version: str,
    language_plugin_version: str,
    tool_version: str,
) -> dict[str, object]:
    """Return producer provenance accepted by SPX verification runs."""
    return {
        "agentOwningPluginVersion": agent_plugin_version,
        "skillOwningPluginVersion": language_plugin_version,
        "toolVersion": tool_version,
    }


def expected_verification_projection(
    run_token: str,
    *,
    finding_count: int,
    terminal_status: AuditTerminalStatus,
) -> tuple[object, ...]:
    """Return expected sealed-projection fields for one verification run."""
    return (
        terminal_status.value,
        True,
        run_token,
        finding_count,
        True,
        terminal_status.value,
    )


def _require_subject_path(subject_path: str) -> str:
    """Return a concrete audit subject or reject the empty boundary value."""
    if not subject_path:
        raise ValueError("implementation audit evidence requires a subject path")
    return subject_path
