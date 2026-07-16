"""Generated cases for the implementation-audit verification-run contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from outcomeeng.validation import audit_artifacts, implementation_audit_contract

from outcomeeng.validation.implementation_audit_contract import (
    ImplementationAuditConcern,
    implementation_audit_unit_id,
)


@dataclass(frozen=True)
class ImplementationAuditVerificationProbe:
    """One source-derived compatibility probe for the SPX lifecycle."""

    language: str
    concern: ImplementationAuditConcern
    subject_path: str
    unit_id: str


def implementation_audit_verification_probes(
    language: str,
) -> tuple[ImplementationAuditVerificationProbe, ...]:
    """Derive distinct compatibility cases from real source subject paths."""
    concern = ImplementationAuditConcern.CODE
    subject_paths = (
        Path(implementation_audit_contract.__file__).name,
        Path(audit_artifacts.__file__).name,
    )
    return tuple(
        _implementation_audit_verification_probe(
            language,
            concern,
            subject_path,
        )
        for subject_path in subject_paths
    )


def _implementation_audit_verification_probe(
    language: str,
    concern: ImplementationAuditConcern,
    subject_path: str,
) -> ImplementationAuditVerificationProbe:
    unit_id = implementation_audit_unit_id(
        language,
        concern,
        subject_path=subject_path,
    )
    return ImplementationAuditVerificationProbe(
        language=language,
        concern=concern,
        subject_path=subject_path,
        unit_id=unit_id,
    )
