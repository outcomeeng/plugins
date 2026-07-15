"""Generated cases for the implementation-audit verification-run contract."""

from __future__ import annotations

from dataclasses import dataclass

from outcomeeng.validation.implementation_audit_contract import (
    IMPLEMENTATION_AUDIT_CLASS,
    AuditCoverageStatus,
    AuditTerminalStatus,
    ImplementationAuditConcern,
    implementation_audit_concern_skill_name,
    implementation_audit_subject_unit_id,
)
from outcomeeng.validation.plugins import language_code_skill_relative_path


@dataclass(frozen=True)
class ImplementationAuditVerificationProbe:
    """One source-derived compatibility probe for the SPX lifecycle."""

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


def _source_owned_probe_values(
    language: str,
    concern: ImplementationAuditConcern,
    subject_path: str,
) -> tuple[str, str, str, str, str, str]:
    """Return SPX carrier values derived only from production contracts."""
    unit_id = implementation_audit_subject_unit_id(
        language,
        concern,
        subject_path,
    )
    concern_skill = implementation_audit_concern_skill_name(language, concern)
    return (
        unit_id,
        IMPLEMENTATION_AUDIT_CLASS,
        concern_skill,
        concern_skill,
        AuditCoverageStatus.AUDITED.value,
        AuditTerminalStatus.REJECTED.value,
    )


def implementation_audit_verification_probe(
    language: str,
) -> ImplementationAuditVerificationProbe:
    """Derive a compatibility case from one source-owned coverage unit."""
    concern = ImplementationAuditConcern.CODE
    subject_path = str(language_code_skill_relative_path(language))
    finding_key, request_kind, rule, message, observed, expected = (
        _source_owned_probe_values(language, concern, subject_path)
    )
    return ImplementationAuditVerificationProbe(
        language=language,
        concern=concern,
        subject_path=subject_path,
        finding_key=finding_key,
        request_kind=request_kind,
        rule=rule,
        message=message,
        observed=observed,
        expected=expected,
        finding_count=1,
        terminal_status=AuditTerminalStatus.REJECTED,
    )
