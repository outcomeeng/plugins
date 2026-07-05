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
    FALSE_COUPLING = "false coupling"
    FIXTURE_LAUNDERING = "fixture laundering"
    LAUNDERED_INDIRECT = "laundered indirect"
    MISALIGNED = "misaligned"
    NO_COUPLING = "no coupling"
    NO_COVERAGE = "no coverage"
    PARTIAL_COUPLING = "partial coupling"
    POSITIVE_PATTERN = "positive pattern"
    PROSE_COUPLING = "prose-coupling"
    TEST_OWNED_DECLARATION = "test-owned declaration"
    UNFALSIFIABLE = "unfalsifiable"
    UNSOURCED_LITERAL = "unsourced literal"
    UNTESTABLE_SOURCE = "untestable source"


class FindingTarget(StrEnum):
    SOURCE_FILE = "source file"
    TEST_FILE = "test file"


class RemediationOwner(StrEnum):
    EVAL_CASE_DATA = "eval case data"
    GENERATOR = "spec-governed generator"
    HARNESS = "spec-governed harness"
    INERT_FIXTURE = "inert whole-payload fixture"
    SOURCE_CONTRACT = "source contract"


class EvidenceCheck(StrEnum):
    COUPLING = "coupling"
    FALSIFIABILITY = "falsifiability"
    ALIGNMENT = "alignment"
    COVERAGE = "coverage"


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


MIN_COUPLING_TAXONOMY_CATEGORIES: Final = 9
COUPLING_TAXONOMY_CATEGORIES: Final = frozenset(
    (
        CouplingEvidence.DIRECT,
        CouplingEvidence.INDIRECT,
        CouplingEvidence.TRANSITIVE,
        CouplingEvidence.LAUNDERED_INDIRECT,
        CouplingEvidence.FALSE,
        CouplingEvidence.PARTIAL,
        CouplingEvidence.NONE,
        CouplingEvidence.SEVERED,
        CouplingEvidence.PROSE,
    )
)
UNTESTABLE_SOURCE_SKIPPED_CHECKS: Final = frozenset(
    (
        EvidenceCheck.COUPLING,
        EvidenceCheck.FALSIFIABILITY,
        EvidenceCheck.ALIGNMENT,
        EvidenceCheck.COVERAGE,
    )
)
TEST_OWNED_DECLARATION_REMEDIATION_OWNERS: Final = frozenset(
    (
        RemediationOwner.SOURCE_CONTRACT,
        RemediationOwner.HARNESS,
        RemediationOwner.GENERATOR,
        RemediationOwner.INERT_FIXTURE,
        RemediationOwner.EVAL_CASE_DATA,
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
    finding_target: FindingTarget | None = None
    remediation_owners: frozenset[RemediationOwner] = frozenset()
    skipped_checks: frozenset[EvidenceCheck] = frozenset()
    coverage_trace: CoverageTrace | None = None


def reject_test_file(category: FindingCategory) -> AuditVerdict:
    return AuditVerdict(
        status=AuditStatus.REJECT,
        finding_category=category,
        finding_target=FindingTarget.TEST_FILE,
    )


def coupling_taxonomy_category_count() -> int:
    return len(COUPLING_TAXONOMY_CATEGORIES)


def audit_case_verdict(case: AuditCase) -> AuditVerdict:
    if not case.source_exposes_assertion:
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.UNTESTABLE_SOURCE,
            finding_target=FindingTarget.SOURCE_FILE,
            skipped_checks=UNTESTABLE_SOURCE_SKIPPED_CHECKS,
        )
    if case.declarations:
        return AuditVerdict(
            status=AuditStatus.REJECT,
            finding_category=FindingCategory.TEST_OWNED_DECLARATION,
            finding_target=FindingTarget.TEST_FILE,
            remediation_owners=TEST_OWNED_DECLARATION_REMEDIATION_OWNERS,
        )
    if case.coupling is CouplingEvidence.NONE:
        return reject_test_file(FindingCategory.NO_COUPLING)
    if case.coupling is CouplingEvidence.SEVERED:
        return reject_test_file(FindingCategory.COUPLING_SEVERED)
    if case.coupling is CouplingEvidence.LAUNDERED_INDIRECT:
        return reject_test_file(FindingCategory.LAUNDERED_INDIRECT)
    if case.coupling is CouplingEvidence.FALSE:
        return reject_test_file(FindingCategory.FALSE_COUPLING)
    if case.coupling is CouplingEvidence.PARTIAL:
        return reject_test_file(FindingCategory.PARTIAL_COUPLING)
    if case.coupling is CouplingEvidence.PROSE:
        return reject_test_file(FindingCategory.PROSE_COUPLING)
    if case.literal_origin is LiteralOrigin.UNSOURCED_NUMERIC:
        return reject_test_file(FindingCategory.UNSOURCED_LITERAL)
    if case.literal_origin is LiteralOrigin.UNSOURCED_STRING:
        return reject_test_file(FindingCategory.UNSOURCED_LITERAL)
    if case.literal_origin is LiteralOrigin.STATIC_FIXTURE:
        return reject_test_file(FindingCategory.FIXTURE_LAUNDERING)
    if case.literal_origin is LiteralOrigin.LAUNDERED_INDIRECT:
        return reject_test_file(FindingCategory.LAUNDERED_INDIRECT)
    if not case.mutation_named:
        return reject_test_file(FindingCategory.UNFALSIFIABLE)
    if not case.aligned:
        return reject_test_file(FindingCategory.MISALIGNED)
    if case.coverage_path == "":
        return reject_test_file(FindingCategory.NO_COVERAGE)
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
