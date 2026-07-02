from outcomeeng_testing.harnesses.audit_tests import (
    async_helper_declarations_are_detected,
    block_comment_declarations_are_ignored,
    complete_evidence_is_approved,
    coupling_severed_is_rejected,
    coverage_trace_names_code_path,
    fixture_laundering_is_rejected,
    laundered_indirect_is_rejected,
    misaligned_evidence_is_rejected,
    no_coupling_is_rejected,
    no_coverage_is_rejected,
    numeric_literal_is_rejected,
    positive_pattern_is_reported,
    prose_coupling_is_rejected,
    python_binding_declarations_are_detected,
    sourced_literals_pass,
    string_literal_is_rejected,
    test_owned_declaration_is_rejected,
    testability_passes_to_coupling,
    unfalsifiable_evidence_is_rejected,
    untestable_source_targets_source,
)


def test_rejects_untestable_source() -> None:
    assert untestable_source_targets_source()


def test_proceeds_to_coupling_after_testability_passes() -> None:
    assert testability_passes_to_coupling()


def test_rejects_no_coupling() -> None:
    assert no_coupling_is_rejected()


def test_rejects_severed_coupling() -> None:
    assert coupling_severed_is_rejected()


def test_approves_complete_evidence() -> None:
    assert complete_evidence_is_approved()


def test_rejects_misaligned_evidence() -> None:
    assert misaligned_evidence_is_rejected()


def test_rejects_unfalsifiable_evidence() -> None:
    assert unfalsifiable_evidence_is_rejected()


def test_rejects_missing_coverage() -> None:
    assert no_coverage_is_rejected()


def test_names_coverage_trace_path() -> None:
    assert coverage_trace_names_code_path()


def test_rejects_unsourced_numeric_literals() -> None:
    assert numeric_literal_is_rejected()


def test_rejects_unsourced_string_literals() -> None:
    assert string_literal_is_rejected()


def test_accepts_sourced_literals() -> None:
    assert sourced_literals_pass()


def test_rejects_fixture_laundering() -> None:
    assert fixture_laundering_is_rejected()


def test_rejects_laundered_indirect() -> None:
    assert laundered_indirect_is_rejected()


def test_rejects_prose_coupling() -> None:
    assert prose_coupling_is_rejected()


def test_rejects_test_owned_declarations() -> None:
    assert test_owned_declaration_is_rejected()


def test_reports_positive_pattern() -> None:
    assert positive_pattern_is_reported()


def test_detects_async_helper_declarations() -> None:
    assert async_helper_declarations_are_detected()


def test_detects_python_binding_declarations() -> None:
    assert python_binding_declarations_are_detected()


def test_ignores_block_comment_declarations() -> None:
    assert block_comment_declarations_are_ignored()
