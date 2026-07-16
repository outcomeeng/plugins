"""Generated cases for the implementation-audit verification-run contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng import distribution, validation
from outcomeeng.validation.implementation_audit_contract import (
    ImplementationAuditConcern,
    implementation_audit_unit_id,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]


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
    """Derive duplicate-basename compatibility cases from real source paths."""
    concern = ImplementationAuditConcern.CODE
    subject_paths = tuple(
        _repository_relative_module_path(module_file)
        for module_file in (validation.__file__, distribution.__file__)
    )
    return tuple(
        _implementation_audit_verification_probe(
            language,
            concern,
            subject_path,
        )
        for subject_path in subject_paths
    )


def _repository_relative_module_path(module_file: str | None) -> str:
    """Return one imported module's repository-relative path."""
    if module_file is None:
        raise RuntimeError("imported module has no source path")
    return Path(module_file).resolve().relative_to(REPO_ROOT).as_posix()


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
