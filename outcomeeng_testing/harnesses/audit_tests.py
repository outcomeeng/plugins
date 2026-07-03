"""Harnesses for audit-tests evidence."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Protocol, cast

from outcomeeng.test_evidence import (
    AuditCase,
    AuditStatus,
    CouplingEvidence,
    FindingCategory,
    LiteralOrigin,
    MIN_COUPLING_TAXONOMY_CATEGORIES,
    audit_case_after_testability,
    audit_case_verdict,
    coupling_taxonomy_category_count,
)


class Declaration(Protocol):
    name: str
    kind: str


class DeclarationScanner(Protocol):
    def scan_text(self, source: str, path: Path) -> list[Declaration]: ...


def untestable_source_targets_source() -> bool:
    return (
        audit_case_verdict(_audit_case(source_exposes_assertion=False)).finding_category
        is FindingCategory.UNTESTABLE_SOURCE
    )


def testability_passes_to_coupling() -> bool:
    verdict = audit_case_after_testability(_audit_case())
    return (
        verdict.status is AuditStatus.APPROVED
        and verdict.finding_category is FindingCategory.COUPLING_PENDING
    )


def no_coupling_is_rejected() -> bool:
    return (
        audit_case_verdict(_audit_case(coupling=CouplingEvidence.NONE)).finding_category
        is FindingCategory.NO_COUPLING
    )


def coupling_severed_is_rejected() -> bool:
    return (
        audit_case_verdict(
            _audit_case(coupling=CouplingEvidence.SEVERED)
        ).finding_category
        is FindingCategory.COUPLING_SEVERED
    )


def complete_evidence_is_approved() -> bool:
    return audit_case_verdict(_audit_case()).status is AuditStatus.APPROVED


def misaligned_evidence_is_rejected() -> bool:
    return (
        audit_case_verdict(_audit_case(aligned=False)).finding_category
        is FindingCategory.MISALIGNED
    )


def unfalsifiable_evidence_is_rejected() -> bool:
    return (
        audit_case_verdict(_audit_case(mutation_named=False)).finding_category
        is FindingCategory.UNFALSIFIABLE
    )


def no_coverage_is_rejected() -> bool:
    return (
        audit_case_verdict(_audit_case(coverage_path="")).finding_category
        is FindingCategory.NO_COVERAGE
    )


def coverage_trace_names_code_path() -> bool:
    verdict = audit_case_verdict(_audit_case())
    return (
        verdict.coverage_trace is not None
        and verdict.coverage_trace.code_path == audit_case_verdict.__qualname__
    )


def numeric_literal_is_rejected() -> bool:
    return (
        audit_case_verdict(
            _audit_case(literal_origin=LiteralOrigin.UNSOURCED_NUMERIC)
        ).finding_category
        is FindingCategory.UNSOURCED_LITERAL
    )


def string_literal_is_rejected() -> bool:
    return (
        audit_case_verdict(
            _audit_case(literal_origin=LiteralOrigin.UNSOURCED_STRING)
        ).finding_category
        is FindingCategory.UNSOURCED_LITERAL
    )


def sourced_literals_pass() -> bool:
    return (
        audit_case_verdict(
            _audit_case(literal_origin=LiteralOrigin.ALLOWLIST_OR_SOURCED)
        ).status
        is AuditStatus.APPROVED
    )


def fixture_laundering_is_rejected() -> bool:
    return (
        audit_case_verdict(
            _audit_case(literal_origin=LiteralOrigin.STATIC_FIXTURE)
        ).finding_category
        is FindingCategory.FIXTURE_LAUNDERING
    )


def laundered_indirect_is_rejected() -> bool:
    return (
        audit_case_verdict(
            _audit_case(literal_origin=LiteralOrigin.LAUNDERED_INDIRECT)
        ).finding_category
        is FindingCategory.LAUNDERED_INDIRECT
    )


def prose_coupling_is_rejected() -> bool:
    return (
        audit_case_verdict(
            _audit_case(coupling=CouplingEvidence.PROSE)
        ).finding_category
        is FindingCategory.PROSE_COUPLING
    )


def test_owned_declaration_is_rejected() -> bool:
    declarations = _declarations_for_fixture("test_owned_declaration.py")
    if any(
        declaration.name == "mapping_runs" and declaration.kind == "variable"
        for declaration in declarations
    ):
        return (
            audit_case_verdict(_audit_case(declarations=True)).finding_category
            is FindingCategory.TEST_OWNED_DECLARATION
        )
    return False


def positive_pattern_is_reported() -> bool:
    return (
        audit_case_verdict(_audit_case(positive_pattern=True)).finding_category
        is FindingCategory.POSITIVE_PATTERN
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


def python_pattern_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("python_pattern_declaration.py")
    return (
        _has_variable(declarations, "computed")
        and _has_variable(declarations, "root")
        and _has_variable(declarations, "first")
        and _has_variable(declarations, "rest")
        and _has_variable(declarations, "extra")
        and _has_variable(declarations, "missing")
    )


def block_comment_declarations_are_ignored() -> bool:
    typescript_declarations = _declarations_for_fixture("block_comment_declaration.ts")
    rust_declarations = _declarations_for_fixture("block_comment_declaration.rs")
    return (
        not _has_constant(typescript_declarations, "CASES")
        and _has_variable(typescript_declarations, "pattern")
        and _has_variable(typescript_declarations, "afterPattern")
        and _has_variable(typescript_declarations, "beforeTrailing")
        and _has_variable(typescript_declarations, "afterTrailing")
        and not _has_function(rust_declarations, "setup")
        and _has_variable(rust_declarations, "pattern")
        and _has_variable(rust_declarations, "before_trailing")
        and _has_variable(rust_declarations, "after_trailing")
    )


def multiple_typescript_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("multiple_declaration.ts")
    return (
        _has_variable(declarations, "input")
        and _has_variable(declarations, "expected")
        and not _has_variable(declarations, "other")
        and not _has_variable(declarations, "number")
    )


def typescript_loop_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("typescript_loop_declaration.ts")
    return (
        _has_variable(declarations, "row")
        and _has_variable(declarations, "input")
        and _has_variable(declarations, "expected")
        and _has_variable(declarations, "index")
    )


def typescript_multiline_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("typescript_multiline_declaration.ts")
    return (
        _has_variable(declarations, "source")
        and _has_variable(declarations, "target")
        and _has_variable(declarations, "rest")
        and _has_variable(declarations, "input")
        and _has_variable(declarations, "output")
        and _has_variable(declarations, "configured")
        and not _has_variable(declarations, "expected")
    )


def typescript_semicolonless_declarations_are_split() -> bool:
    declarations = _scanner().scan_text(
        """const semicolonlessObject = {
  enabled: true,
}
const afterSemicolonless = buildConfig()
""",
        Path("semicolonless.ts"),
    )
    return _has_variable(declarations, "semicolonlessObject") and _has_variable(
        declarations, "afterSemicolonless"
    )


def rust_destructuring_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("rust_destructuring_declaration.rs")
    return (
        _has_variable(declarations, "project_dir")
        and _has_variable(declarations, "expected")
        and _has_variable(declarations, "root")
        and _has_variable(declarations, "alias")
        and _has_variable(declarations, "value")
        and _has_variable(declarations, "nested_alias")
        and _has_variable(declarations, "nested_value")
        and _has_constant(declarations, "LOGGER")
        and not _has_variable(declarations, "Harness")
        and not _has_variable(declarations, "Foo")
    )


def rust_conditional_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("rust_conditional_declaration.rs")
    return (
        _has_variable(declarations, "value")
        and _has_variable(declarations, "input")
        and _has_variable(declarations, "expected")
        and _has_variable(declarations, "branch")
        and _has_variable(declarations, "nested_branch")
        and _has_variable(declarations, "block_branch")
        and _has_variable(declarations, "nested_block_branch")
        and _has_variable(declarations, "project_dir")
        and _has_variable(declarations, "target")
        and _has_variable(declarations, "root")
        and _has_variable(declarations, "nested_target")
    )


def coupling_taxonomy_has_distinct_failure_modes() -> bool:
    return coupling_taxonomy_category_count() >= MIN_COUPLING_TAXONOMY_CATEGORIES


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


def _has_constant(declarations: list[Declaration], name: str) -> bool:
    return any(
        declaration.name == name and declaration.kind == "constant"
        for declaration in declarations
    )


def _audit_case(
    *,
    source_exposes_assertion: bool = True,
    declarations: bool = False,
    coupling: CouplingEvidence = CouplingEvidence.DIRECT,
    literal_origin: LiteralOrigin = LiteralOrigin.ALLOWLIST_OR_SOURCED,
    mutation_named: bool = True,
    aligned: bool = True,
    coverage_path: str = audit_case_verdict.__qualname__,
    positive_pattern: bool = False,
) -> AuditCase:
    return AuditCase(
        source_exposes_assertion=source_exposes_assertion,
        declarations=declarations,
        coupling=coupling,
        literal_origin=literal_origin,
        mutation_named=mutation_named,
        aligned=aligned,
        coverage_path=coverage_path,
        positive_pattern=positive_pattern,
    )


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
