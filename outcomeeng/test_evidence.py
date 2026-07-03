"""Deterministic contracts for spec-tree test-evidence scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class AuditStatus(StrEnum):
    APPROVED = "APPROVED"
    REJECT = "REJECT"


class FindingCategory(StrEnum):
    COUPLING_PENDING = "coupling pending"
    COUPLING_SEVERED = "coupling severed"
    FIXTURE_LAUNDERING = "fixture laundering"
    LAUNDERED_INDIRECT = "laundered indirect"
    MISALIGNED = "misaligned"
    NO_COUPLING = "no coupling"
    NO_COVERAGE = "no coverage"
    POSITIVE_PATTERN = "positive pattern"
    PROSE_COUPLING = "prose-coupling"
    TEST_OWNED_DECLARATION = "test-owned declaration"
    UNFALSIFIABLE = "unfalsifiable"
    UNSOURCED_LITERAL = "unsourced literal"
    UNTESTABLE_SOURCE = "untestable source"


class LiteralOrigin(StrEnum):
    ALLOWLIST_OR_SOURCED = "allowlist-or-sourced"
    STATIC_FIXTURE = "static-fixture"
    LAUNDERED_INDIRECT = "laundered-indirect"
    UNSOURCED_NUMERIC = "unsourced-numeric"
    UNSOURCED_STRING = "unsourced-string"


class CouplingEvidence(StrEnum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    TRANSITIVE = "transitive"
    LAUNDERED_INDIRECT = "laundered indirect"
    FALSE = "false"
    PARTIAL = "partial"
    NONE = "none"
    SEVERED = "severed"
    PROSE = "prose"


MIN_COUPLING_TAXONOMY_CATEGORIES: Final = 8
COUPLING_TAXONOMY_CATEGORIES: Final = frozenset(
    (
        CouplingEvidence.DIRECT,
        CouplingEvidence.INDIRECT,
        CouplingEvidence.TRANSITIVE,
        CouplingEvidence.LAUNDERED_INDIRECT,
        CouplingEvidence.FALSE,
        CouplingEvidence.PARTIAL,
        CouplingEvidence.NONE,
        CouplingEvidence.PROSE,
    )
)


@dataclass(frozen=True)
class AuditCase:
    source_exposes_assertion: bool
    declarations: bool
    coupling: CouplingEvidence
    literal_origin: LiteralOrigin
    mutation_named: bool
    aligned: bool
    coverage_path: str
    positive_pattern: bool


@dataclass(frozen=True)
class CoverageTrace:
    code_path: str


@dataclass(frozen=True)
class AuditVerdict:
    status: AuditStatus
    finding_category: FindingCategory | None = None
    coverage_trace: CoverageTrace | None = None


def coupling_taxonomy_category_count() -> int:
    return len(COUPLING_TAXONOMY_CATEGORIES)


def audit_case_verdict(case: AuditCase) -> AuditVerdict:
    if not case.source_exposes_assertion:
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.UNTESTABLE_SOURCE,
        )
    if case.declarations:
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.TEST_OWNED_DECLARATION,
        )
    if case.coupling is CouplingEvidence.NONE:
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.NO_COUPLING,
        )
    if case.coupling is CouplingEvidence.SEVERED:
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.COUPLING_SEVERED,
        )
    if case.coupling is CouplingEvidence.PROSE:
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.PROSE_COUPLING,
        )
    if case.literal_origin is LiteralOrigin.UNSOURCED_NUMERIC:
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.UNSOURCED_LITERAL,
        )
    if case.literal_origin is LiteralOrigin.UNSOURCED_STRING:
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.UNSOURCED_LITERAL,
        )
    if case.literal_origin is LiteralOrigin.STATIC_FIXTURE:
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.FIXTURE_LAUNDERING,
        )
    if case.literal_origin is LiteralOrigin.LAUNDERED_INDIRECT:
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.LAUNDERED_INDIRECT,
        )
    if not case.mutation_named:
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.UNFALSIFIABLE,
        )
    if not case.aligned:
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.MISALIGNED,
        )
    if case.coverage_path == "":
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.NO_COVERAGE,
        )
    return AuditVerdict(
        status=AuditStatus.APPROVED,
        finding_category=FindingCategory.POSITIVE_PATTERN
        if case.positive_pattern
        else None,
        coverage_trace=CoverageTrace(code_path=case.coverage_path),
    )


def audit_case_after_testability(case: AuditCase) -> AuditVerdict:
    if case.source_exposes_assertion:
        return AuditVerdict(
            status=AuditStatus.APPROVED,
            finding_category=FindingCategory.COUPLING_PENDING,
        )
    return audit_case_verdict(case)
