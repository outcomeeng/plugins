"""Generated cases for the implementation-audit verification-run contract."""

from __future__ import annotations

from dataclasses import dataclass

from outcomeeng.validation.implementation_audit_contract import (
    AuditTerminalStatus,
    ImplementationAuditConcern,
    implementation_audit_unit_id,
)


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


def implementation_audit_verification_probe(
    language: str,
) -> ImplementationAuditVerificationProbe:
    """Derive a compatibility case from one source-owned coverage unit."""
    concern = ImplementationAuditConcern.CODE
    unit_id = implementation_audit_unit_id(language, concern)
    return ImplementationAuditVerificationProbe(
        language=language,
        concern=concern,
        subject_path=f"{unit_id}.txt",
        finding_key=f"{unit_id}:finding",
        request_kind=f"{unit_id}:request",
        rule=f"{unit_id}:rule",
        message=f"{unit_id}:message",
        observed=f"{unit_id}:observed",
        expected=f"{unit_id}:expected",
        finding_count=1,
        terminal_status=AuditTerminalStatus.REJECTED,
    )
