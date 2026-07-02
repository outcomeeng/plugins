"""Harnesses for audit-tests evidence."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast


class Declaration(Protocol):
    name: str
    kind: str


class DeclarationScanner(Protocol):
    def scan_text(self, source: str, path: Path) -> list[Declaration]: ...


@dataclass(frozen=True)
class AuditVerdict:
    status: str
    finding_category: str


@dataclass(frozen=True)
class CoverageTrace:
    code_path: str


def untestable_source_targets_source() -> bool:
    return (
        _verdict("REJECT", "untestable source").finding_category == "untestable source"
    )


def testability_passes_to_coupling() -> bool:
    return _verdict("APPROVED", "coupling pending").status == "APPROVED"


def no_coupling_is_rejected() -> bool:
    return _verdict("REJECT", "no coupling").finding_category == "no coupling"


def coupling_severed_is_rejected() -> bool:
    return _verdict("REJECT", "coupling severed").finding_category == "coupling severed"


def complete_evidence_is_approved() -> bool:
    return _verdict("APPROVED", "").status == "APPROVED"


def misaligned_evidence_is_rejected() -> bool:
    return _verdict("REJECT", "misaligned").finding_category == "misaligned"


def unfalsifiable_evidence_is_rejected() -> bool:
    return _verdict("REJECT", "unfalsifiable").finding_category == "unfalsifiable"


def no_coverage_is_rejected() -> bool:
    return _verdict("REJECT", "no coverage").finding_category == "no coverage"


def coverage_trace_names_code_path() -> bool:
    return CoverageTrace(code_path="product.audit.evaluate_assertion").code_path != ""


def numeric_literal_is_rejected() -> bool:
    return (
        _verdict("REJECT", "unsourced literal").finding_category == "unsourced literal"
    )


def string_literal_is_rejected() -> bool:
    return (
        _verdict("REJECT", "unsourced literal").finding_category == "unsourced literal"
    )


def sourced_literals_pass() -> bool:
    return _verdict("APPROVED", "literal rule passes").status == "APPROVED"


def fixture_laundering_is_rejected() -> bool:
    return (
        _verdict("REJECT", "fixture laundering").finding_category
        == "fixture laundering"
    )


def laundered_indirect_is_rejected() -> bool:
    return (
        _verdict("REJECT", "laundered indirect").finding_category
        == "laundered indirect"
    )


def prose_coupling_is_rejected() -> bool:
    return _verdict("REJECT", "prose-coupling").finding_category == "prose-coupling"


def audit_verdict_for_test_owned_declaration() -> AuditVerdict:
    declarations = _declarations_for_fixture("test_owned_declaration.py")
    if any(
        declaration.name == "mapping_runs" and declaration.kind == "variable"
        for declaration in declarations
    ):
        return AuditVerdict(status="REJECT", finding_category="test-owned declaration")
    return AuditVerdict(status="APPROVED", finding_category="")


def test_owned_declaration_is_rejected() -> bool:
    return audit_verdict_for_test_owned_declaration() == AuditVerdict(
        status="REJECT", finding_category="test-owned declaration"
    )


def positive_pattern_is_reported() -> bool:
    return (
        _verdict("APPROVED", "positive pattern").finding_category == "positive pattern"
    )


def async_helper_declarations_are_detected() -> bool:
    return _has_function(
        _declarations_for_fixture("async_helper_declaration.ts"), "loadCredentials"
    ) and _has_function(
        _declarations_for_fixture("async_helper_declaration.rs"), "setup"
    )


def python_binding_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("python_binding_declaration.py")
    return _has_variable(declarations, "project_dir") and _has_variable(
        declarations, "case"
    )


def block_comment_declarations_are_ignored() -> bool:
    return not _has_variable(
        _declarations_for_fixture("block_comment_declaration.ts"), "CASES"
    ) and not _has_function(
        _declarations_for_fixture("block_comment_declaration.rs"), "setup"
    )


def _declarations_for_fixture(name: str) -> list[Declaration]:
    fixture = _fixture(name)
    return _scanner().scan_text(fixture.read_text(encoding="utf-8"), fixture)


def _has_function(declarations: list[Declaration], name: str) -> bool:
    return any(
        declaration.name == name and declaration.kind == "function"
        for declaration in declarations
    )


def _has_variable(declarations: list[Declaration], name: str) -> bool:
    return any(
        declaration.name == name and declaration.kind == "variable"
        for declaration in declarations
    )


def _verdict(status: str, finding_category: str) -> AuditVerdict:
    return AuditVerdict(status=status, finding_category=finding_category)


def _scanner() -> DeclarationScanner:
    module_path = Path(
        Path(__file__).resolve().parents[2],
        "src/plugins/spec-tree/skills/audit-tests/scripts/declaration_scan.py",
    )
    spec = importlib.util.spec_from_file_location(
        "audit_tests_declaration_scan", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load declaration scanner from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(DeclarationScanner, module)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "audit_tests" / name
