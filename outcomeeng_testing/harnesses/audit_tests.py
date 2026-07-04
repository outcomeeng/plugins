"""Harnesses for audit-tests evidence."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast

from hypothesis import given, seed, settings

from outcomeeng.test_evidence import (
    AuditCase,
    AuditStatus,
    COUPLING_TAXONOMY_CATEGORIES,
    CouplingEvidence,
    FindingTarget,
    FindingCategory,
    LiteralOrigin,
    MIN_COUPLING_TAXONOMY_CATEGORIES,
    UNTESTABLE_SOURCE_SKIPPED_CHECKS,
    audit_case_after_testability,
    audit_case_verdict,
    coupling_taxonomy_category_count,
)
from outcomeeng_testing.generators.audit_tests import coupling_taxonomy_categories


AUDIT_TESTS_PROPERTY_SEED = 20260704
AUDIT_TESTS_PROPERTY_REPLAY_PATH = (
    "just test "
    "spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/tests/"
    "test_test_auditing.property.l1.py::"
    "test_coupling_taxonomy_classifies_distinct_failure_modes"
)
AUDIT_TESTS_PROPERTY_EXAMPLES = 25


class Declaration(Protocol):
    name: str
    kind: str


class DeclarationScanner(Protocol):
    def scan_text(self, source: str, path: Path) -> list[Declaration]: ...


def coupling_taxonomy_property(test_func: Callable[..., None]) -> Callable[[], None]:
    configured = seed(AUDIT_TESTS_PROPERTY_SEED)(
        settings(max_examples=AUDIT_TESTS_PROPERTY_EXAMPLES)(
            given(category=coupling_taxonomy_categories())(test_func)
        )
    )

    def wrapper() -> None:
        try:
            configured()
        except AssertionError as error:
            error.add_note(f"Hypothesis seed: {AUDIT_TESTS_PROPERTY_SEED}")
            error.add_note(f"Replay path: {AUDIT_TESTS_PROPERTY_REPLAY_PATH}")
            raise

    return wrapper


def untestable_source_targets_source() -> bool:
    verdict = audit_case_verdict(_audit_case(source_exposes_assertion=False))
    return (
        verdict.finding_category is FindingCategory.UNTESTABLE_SOURCE
        and verdict.finding_target is FindingTarget.SOURCE_FILE
        and verdict.skipped_checks == UNTESTABLE_SOURCE_SKIPPED_CHECKS
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


def false_coupling_is_rejected() -> bool:
    return (
        audit_case_verdict(
            _audit_case(coupling=CouplingEvidence.FALSE)
        ).finding_category
        is FindingCategory.FALSE_COUPLING
    )


def partial_coupling_is_rejected() -> bool:
    return (
        audit_case_verdict(
            _audit_case(coupling=CouplingEvidence.PARTIAL)
        ).finding_category
        is FindingCategory.PARTIAL_COUPLING
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


def laundered_indirect_coupling_is_rejected() -> bool:
    return (
        audit_case_verdict(
            _audit_case(coupling=CouplingEvidence.LAUNDERED_INDIRECT)
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


def helper_function_declaration_is_rejected() -> bool:
    declarations = _declarations_for_fixture("async_helper_declaration.ts")
    if not _has_function(declarations, "loadCredentials"):
        return False
    return (
        audit_case_verdict(_audit_case(declarations=True)).finding_category
        is FindingCategory.TEST_OWNED_DECLARATION
    )


def owned_declaration_categories_are_rejected() -> bool:
    declarations = _declarations_for_fixture("test_owned_declaration_categories.py")
    expected_declarations = {
        "test_data",
        "expected_output",
        "RUNNER_SETTINGS",
        "PROPERTY_CONFIGURATION",
        "setup_policy",
        "reusable_cases",
        "fixture_path",
        "generator_choice",
        "harness_behavior",
    }
    observed_declarations = {declaration.name for declaration in declarations}
    return (
        expected_declarations <= observed_declarations
        and audit_case_verdict(_audit_case(declarations=True)).finding_category
        is FindingCategory.TEST_OWNED_DECLARATION
    )


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
    return (
        _has_variable(declarations, "project_dir")
        and _has_variable(declarations, "cases")
        and _has_variable(declarations, "case")
    )


def python_pattern_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("python_pattern_declaration.py")
    return (
        _has_variable(declarations, "case")
        and _has_variable(declarations, "computed")
        and _has_variable(declarations, "root")
        and _has_variable(declarations, "first")
        and _has_variable(declarations, "rest")
        and _has_variable(declarations, "extra")
        and _has_variable(declarations, "missing")
    )


def python_starred_assignment_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("python_starred_assignment_declaration.py")
    return (
        _has_variable(declarations, "first")
        and _has_variable(declarations, "rest")
        and _has_variable(declarations, "head")
        and _has_variable(declarations, "middle")
        and _has_variable(declarations, "tail")
    )


def python_exception_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("python_exception_declaration.py")
    return _has_variable(declarations, "error")


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
const semicolonlessIdentifier =
  sourceValue
const afterIdentifier = buildConfig()
const semicolonlessNumber =
  1
const afterNumber = buildConfig()
const semicolonlessSum =
  first +
  second
const afterSum = buildConfig()
const semicolonlessTernary = sourceValue
  /* comment-only line before continuation */
  ? first
  : second,
  afterTernary = buildConfig()
const semicolonlessCurrentLineComment = sourceValue /* block starts
  block continues */
  ? first
  : second,
  afterCurrentLineComment = buildConfig()
const semicolonlessCall = sourceValue
  (first),
  afterCall = buildConfig()
const semicolonlessIndex = sourceValue
  [first],
  afterIndex = buildConfig()
const semicolonlessTemplate = tag
  `value`,
  afterTemplate = buildConfig()
const afterTernaryStatement = buildConfig()
""",
        Path("semicolonless.ts"),
    )
    return (
        _has_variable(declarations, "semicolonlessObject")
        and _has_variable(declarations, "afterSemicolonless")
        and _has_variable(declarations, "semicolonlessIdentifier")
        and _has_variable(declarations, "afterIdentifier")
        and _has_variable(declarations, "semicolonlessNumber")
        and _has_variable(declarations, "afterNumber")
        and _has_variable(declarations, "semicolonlessSum")
        and _has_variable(declarations, "afterSum")
        and _has_variable(declarations, "semicolonlessTernary")
        and _has_variable(declarations, "afterTernary")
        and _has_variable(declarations, "semicolonlessCurrentLineComment")
        and _has_variable(declarations, "afterCurrentLineComment")
        and _has_variable(declarations, "semicolonlessCall")
        and _has_variable(declarations, "afterCall")
        and _has_variable(declarations, "semicolonlessIndex")
        and _has_variable(declarations, "afterIndex")
        and _has_variable(declarations, "semicolonlessTemplate")
        and _has_variable(declarations, "afterTemplate")
        and _has_variable(declarations, "afterTernaryStatement")
    )


def typescript_same_line_statement_declarations_are_detected() -> bool:
    declarations = _scanner().scan_text(
        (
            "const first = buildConfig(); const second = buildConfig(); "
            "let third = buildConfig(); var fourth = buildConfig(); "
            "const semicolonPattern = /;/; const afterPattern = buildConfig();"
        ),
        Path("same-line.ts"),
    )
    return (
        _has_variable(declarations, "first")
        and _has_variable(declarations, "second")
        and _has_variable(declarations, "third")
        and _has_variable(declarations, "fourth")
        and _has_variable(declarations, "semicolonPattern")
        and _has_variable(declarations, "afterPattern")
    )


def typescript_comparison_initializer_declarators_are_split() -> bool:
    declarations = _scanner().scan_text(
        "const underLimit = count < max, expected = true",
        Path("comparison.ts"),
    )
    return _has_variable(declarations, "underLimit") and _has_variable(
        declarations, "expected"
    )


def typescript_jsx_closing_declarations_are_split() -> bool:
    declarations = _scanner().scan_text(
        """const element = <Widget />
const expected = buildExpectation()
const closed = <section></section>
const afterClosed = buildExpectation()
""",
        Path("component.tsx"),
    )
    return (
        _has_variable(declarations, "element")
        and _has_variable(declarations, "expected")
        and _has_variable(declarations, "closed")
        and _has_variable(declarations, "afterClosed")
    )


def typescript_template_literal_declarations_are_ignored() -> bool:
    declarations = _declarations_for_fixture(
        "typescript_template_literal_declaration.ts"
    )
    return (
        _has_variable(declarations, "source")
        and _has_variable(declarations, "afterSource")
        and not _has_constant(declarations, "CASES")
        and not _has_function(declarations, "setup")
    )


def typescript_regex_literal_declarations_are_preserved() -> bool:
    declarations = _declarations_for_fixture("typescript_regex_literal_declaration.ts")
    return (
        _has_variable(declarations, "urlPattern")
        and _has_variable(declarations, "afterPattern")
        and _has_variable(declarations, "arrowPattern")
        and _has_variable(declarations, "afterArrowPattern")
        and _has_function(declarations, "matchesReturnPattern")
        and _has_variable(declarations, "divisionValue")
        and _has_variable(declarations, "afterDivision")
        and _has_variable(declarations, "afterKeywordPattern")
    )


def typescript_catch_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("typescript_catch_declaration.ts")
    return _has_variable(declarations, "error")


def typescript_generator_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("typescript_generator_declaration.ts")
    return _has_function(declarations, "generateCases") and _has_function(
        declarations, "streamCases"
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


def rust_loop_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("rust_loop_declaration.rs")
    return (
        _has_variable(declarations, "case")
        and _has_variable(declarations, "input")
        and _has_variable(declarations, "expected")
        and _has_variable(declarations, "root")
        and _has_variable(declarations, "target")
        and not _has_variable(declarations, "Harness")
    )


def rust_match_declarations_are_detected() -> bool:
    declarations = _declarations_for_fixture("rust_match_declaration.rs")
    return (
        _has_variable(declarations, "value")
        and _has_variable(declarations, "input")
        and _has_variable(declarations, "expected")
        and _has_variable(declarations, "root")
        and _has_variable(declarations, "target")
        and _has_variable(declarations, "multiline_input")
        and _has_variable(declarations, "multiline_expected")
        and _has_variable(declarations, "multiline_root")
        and _has_variable(declarations, "multiline_target")
        and not _has_variable(declarations, "Harness")
        and not _has_variable(declarations, "None")
        and not _has_variable(declarations, "ImportedVariant")
    )


def rust_lifetime_declarations_are_split() -> bool:
    declarations = _scanner().scan_text(
        """let value: &'static str = source();
let expected = build_expected();
""",
        Path("lifetime.rs"),
    )
    return _has_variable(declarations, "value") and _has_variable(
        declarations, "expected"
    )


def rust_lifetime_before_block_comment_declarations_are_ignored() -> bool:
    declarations = _scanner().scan_text(
        """let value: &'static str = source();
/*
let commented = "not real";
*/
let expected = build_expected();
""",
        Path("lifetime-comment.rs"),
    )
    return (
        _has_variable(declarations, "value")
        and not _has_variable(declarations, "commented")
        and _has_variable(declarations, "expected")
    )


def rust_or_pattern_declarations_are_detected() -> bool:
    declarations = _scanner().scan_text(
        """match result {
    Ok(value) | Err(value) => assert_value(value),
}
""",
        Path("or-pattern.rs"),
    )
    return _has_variable(declarations, "value")


def coupling_taxonomy_has_distinct_failure_modes() -> bool:
    return coupling_taxonomy_category_count() >= MIN_COUPLING_TAXONOMY_CATEGORIES


def coupling_taxonomy_category_is_distinct_failure_mode(
    category: CouplingEvidence,
) -> bool:
    return (
        category in COUPLING_TAXONOMY_CATEGORIES
        and coupling_taxonomy_has_distinct_failure_modes()
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
