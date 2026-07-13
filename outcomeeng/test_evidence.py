"""Deterministic contracts for spec-tree test-evidence scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
import re
from typing import Final


class AuditStatus(StrEnum):
    APPROVED = "APPROVED"
    REJECT = "REJECT"


class FindingCategory(StrEnum):
    COUPLING_PENDING = "coupling pending"
    COUPLING_SEVERED = "coupling severed"
    FALSE_COUPLING = "false coupling"
    FIXTURE_LAUNDERING = "fixture laundering"
    FIXTURE_APPROVAL_MISSING = "fixture-approval-missing"
    FIXTURE_NOT_WHOLE_PAYLOAD = "fixture-not-whole-payload"
    INSUFFICIENT_DOMAIN_VARIATION = "insufficient-domain-variation"
    INVALID_REFERENCE = "invalid-reference"
    LAUNDERED_INDIRECT = "laundered indirect"
    MISALIGNED = "misaligned"
    MISSING_GOVERNING_REFERENCE = "missing-governing-reference"
    MISSING_INDEPENDENT_ORACLE = "missing-independent-oracle"
    MISSING_REPLAY_HARNESS = "missing-replay-harness"
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


class ReferenceRole(StrEnum):
    GOVERNANCE = "governance"
    IMPLEMENTATION = "implementation"
    TEST = "test"
    EVAL = "eval"


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
class LocalReference:
    role: ReferenceRole
    markdown_link: str


@dataclass(frozen=True)
class EvidenceDesignCase:
    independent_oracle: bool
    open_or_composable_domain: bool
    generator_varies: bool
    property_evidence: bool
    replay_harness: bool
    fixture_requested: bool
    fixture_whole_payload: bool
    fixture_approved: bool
    governance_reference: LocalReference | None
    implementation_reference: LocalReference | None


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


@dataclass(frozen=True)
class EvidenceDesignVerdict:
    status: AuditStatus
    findings: frozenset[FindingCategory] = frozenset()


MARKDOWN_LINK_PATTERN: Final = re.compile(r"\[[^\]\n]+\]\(([^()\s]+)\)")
NODE_DIRECTORY_PATTERN: Final = re.compile(
    r"\d{2}-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.(?:enabler|outcome)"
)
PYTHON_TEST_FILE_PATTERN: Final = re.compile(
    r"test_.+\.(?:scenario|mapping|conformance|property|compliance)"
    r"\.l[123](?:\.[a-z0-9-]+)?\.py"
)


def reject_test_file(category: FindingCategory) -> AuditVerdict:
    return AuditVerdict(
        status=AuditStatus.REJECT,
        finding_category=category,
        finding_target=FindingTarget.TEST_FILE,
    )


def coupling_taxonomy_category_count() -> int:
    return len(COUPLING_TAXONOMY_CATEGORIES)


def local_reference_target(
    reference: LocalReference,
    product_root: Path,
) -> Path | None:
    match = MARKDOWN_LINK_PATTERN.fullmatch(reference.markdown_link)
    if match is None:
        return None
    raw_target = match.group(1)
    target = PurePosixPath(raw_target)
    if (
        target.is_absolute()
        or raw_target.startswith("./")
        or "\\" in raw_target
        or any(part in {"", ".", ".."} for part in target.parts)
        or "://" in raw_target
    ):
        return None
    resolved = product_root.joinpath(*target.parts)
    if not resolved.is_file():
        return None
    if not _target_matches_role(reference.role, target):
        return None
    return resolved


def audit_evidence_design(
    case: EvidenceDesignCase,
    product_root: Path,
) -> EvidenceDesignVerdict:
    findings: set[FindingCategory] = set()
    if not case.independent_oracle:
        findings.add(FindingCategory.MISSING_INDEPENDENT_ORACLE)
    if case.open_or_composable_domain and not case.generator_varies:
        findings.add(FindingCategory.INSUFFICIENT_DOMAIN_VARIATION)
    if case.property_evidence and not case.replay_harness:
        findings.add(FindingCategory.MISSING_REPLAY_HARNESS)
    if case.fixture_requested and not case.fixture_whole_payload:
        findings.add(FindingCategory.FIXTURE_NOT_WHOLE_PAYLOAD)
    if case.fixture_requested and not case.fixture_approved:
        findings.add(FindingCategory.FIXTURE_APPROVAL_MISSING)
    if (
        case.governance_reference is None
        or local_reference_target(
            case.governance_reference,
            product_root,
        )
        is None
    ):
        findings.add(FindingCategory.MISSING_GOVERNING_REFERENCE)
    if (
        case.implementation_reference is not None
        and local_reference_target(
            case.implementation_reference,
            product_root,
        )
        is None
    ):
        findings.add(FindingCategory.INVALID_REFERENCE)
    return EvidenceDesignVerdict(
        status=AuditStatus.REJECT if findings else AuditStatus.APPROVED,
        findings=frozenset(findings),
    )


def _target_matches_role(role: ReferenceRole, target: PurePosixPath) -> bool:
    if role is ReferenceRole.GOVERNANCE:
        return _is_governance_target(target)
    if role is ReferenceRole.IMPLEMENTATION:
        return target.parts[0] != "spx"
    if role is ReferenceRole.TEST:
        return (
            target.parts[0] == "spx"
            and "tests" in target.parts
            and PYTHON_TEST_FILE_PATTERN.fullmatch(target.name) is not None
        )
    if role is ReferenceRole.EVAL:
        return target.name == "eval.toml" and "evals" in target.parts
    return False


def _is_governance_target(target: PurePosixPath) -> bool:
    if target.parts[0] != "spx" or target.suffix != ".md":
        return False
    if target.name.endswith((".adr.md", ".pdr.md", ".product.md")):
        return True
    parent = target.parent.name
    match = NODE_DIRECTORY_PATTERN.fullmatch(parent)
    return match is not None and target.name == f"{match.group('slug')}.md"


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
