from outcomeeng_testing.harnesses.audit_tests import (
    async_local_function_declarations_are_detected,
    block_comment_declarations_are_ignored,
    complete_evidence_is_approved,
    coupling_severed_is_rejected,
    coverage_trace_names_code_path,
    false_coupling_is_rejected,
    fixture_laundering_is_rejected,
    local_function_declaration_is_rejected,
    laundered_indirect_coupling_is_rejected,
    laundered_indirect_is_rejected,
    misaligned_evidence_is_rejected,
    multiple_typescript_declarations_are_detected,
    no_coupling_is_rejected,
    no_coverage_is_rejected,
    numeric_literal_is_rejected,
    owned_declaration_categories_are_rejected,
    positive_pattern_is_reported,
    partial_coupling_is_rejected,
    prose_coupling_is_rejected,
    property_failure_notes_include_seed_and_replay,
    python_binding_declarations_are_detected,
    python_comprehension_declarations_are_detected,
    python_exception_declarations_are_detected,
    python_parameter_declarations_are_detected,
    python_pattern_declarations_are_detected,
    python_starred_assignment_declarations_are_detected,
    python_test_function_wrappers_are_not_owned_declarations,
    rust_conditional_declarations_are_detected,
    rust_destructuring_declarations_are_detected,
    rust_inline_match_arm_declarations_are_detected,
    rust_lifetime_before_block_comment_declarations_are_ignored,
    rust_lifetime_declarations_are_split,
    rust_loop_declarations_are_detected,
    rust_match_declarations_are_detected,
    rust_closure_parameter_declarations_are_detected,
    rust_or_pattern_declarations_are_detected,
    rust_raw_string_declarations_are_ignored,
    rust_test_function_wrappers_are_not_owned_declarations,
    sourced_literals_pass,
    string_literal_is_rejected,
    owned_declaration_is_rejected,
    testability_passes_to_coupling,
    typescript_class_declarations_are_detected,
    typescript_function_parameter_declarations_are_detected,
    typescript_generator_declarations_are_detected,
    typescript_loop_declarations_are_detected,
    typescript_multiline_declarations_are_detected,
    typescript_nested_using_and_class_declarations_are_detected,
    typescript_regex_literal_declarations_are_preserved,
    typescript_semicolonless_declarations_are_split,
    typescript_semicolonless_type_alias_parameters_are_ignored,
    typescript_typed_destructuring_declarations_are_detected,
    typescript_catch_declarations_are_detected,
    typescript_comparison_initializer_declarators_are_split,
    typescript_same_line_statement_declarations_are_detected,
    typescript_jsx_closing_declarations_are_split,
    typescript_template_literal_declarations_are_ignored,
    typescript_using_declarations_are_detected,
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


def test_rejects_false_coupling() -> None:
    assert false_coupling_is_rejected()


def test_rejects_partial_coupling() -> None:
    assert partial_coupling_is_rejected()


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


def test_rejects_laundered_indirect_coupling() -> None:
    assert laundered_indirect_coupling_is_rejected()


def test_rejects_prose_coupling() -> None:
    assert prose_coupling_is_rejected()


def test_rejects_test_owned_declarations() -> None:
    assert owned_declaration_is_rejected()


def test_rejects_local_function_declarations() -> None:
    assert local_function_declaration_is_rejected()


def test_rejects_owned_declaration_categories() -> None:
    assert owned_declaration_categories_are_rejected()


def test_reports_positive_pattern() -> None:
    assert positive_pattern_is_reported()


def test_reports_property_seed_and_replay_on_failure() -> None:
    assert property_failure_notes_include_seed_and_replay()


def test_detects_async_local_function_declarations() -> None:
    assert async_local_function_declarations_are_detected()


def test_detects_python_binding_declarations() -> None:
    assert python_binding_declarations_are_detected()


def test_detects_python_pattern_declarations() -> None:
    assert python_pattern_declarations_are_detected()


def test_detects_python_starred_assignment_declarations() -> None:
    assert python_starred_assignment_declarations_are_detected()


def test_detects_python_exception_declarations() -> None:
    assert python_exception_declarations_are_detected()


def test_detects_python_parameter_declarations() -> None:
    assert python_parameter_declarations_are_detected()


def test_detects_python_comprehension_declarations() -> None:
    assert python_comprehension_declarations_are_detected()


def test_ignores_python_test_function_wrappers() -> None:
    assert python_test_function_wrappers_are_not_owned_declarations()


def test_ignores_block_comment_declarations() -> None:
    assert block_comment_declarations_are_ignored()


def test_detects_multiple_typescript_declarations() -> None:
    assert multiple_typescript_declarations_are_detected()


def test_detects_typescript_loop_declarations() -> None:
    assert typescript_loop_declarations_are_detected()


def test_detects_typescript_multiline_declarations() -> None:
    assert typescript_multiline_declarations_are_detected()


def test_detects_typescript_typed_destructuring_declarations() -> None:
    assert typescript_typed_destructuring_declarations_are_detected()


def test_detects_typescript_function_parameter_declarations() -> None:
    assert typescript_function_parameter_declarations_are_detected()


def test_detects_typescript_using_declarations() -> None:
    assert typescript_using_declarations_are_detected()


def test_detects_typescript_class_declarations() -> None:
    assert typescript_class_declarations_are_detected()


def test_detects_nested_typescript_using_and_class_declarations() -> None:
    assert typescript_nested_using_and_class_declarations_are_detected()


def test_splits_typescript_semicolonless_declarations() -> None:
    assert typescript_semicolonless_declarations_are_split()


def test_ignores_typescript_semicolonless_type_alias_parameters() -> None:
    assert typescript_semicolonless_type_alias_parameters_are_ignored()


def test_detects_typescript_same_line_statement_declarations() -> None:
    assert typescript_same_line_statement_declarations_are_detected()


def test_splits_typescript_comparison_initializer_declarators() -> None:
    assert typescript_comparison_initializer_declarators_are_split()


def test_splits_typescript_jsx_closing_declarations() -> None:
    assert typescript_jsx_closing_declarations_are_split()


def test_ignores_declarations_inside_typescript_template_literals() -> None:
    assert typescript_template_literal_declarations_are_ignored()


def test_preserves_typescript_regex_literal_declarations() -> None:
    assert typescript_regex_literal_declarations_are_preserved()


def test_detects_typescript_catch_declarations() -> None:
    assert typescript_catch_declarations_are_detected()


def test_detects_typescript_generator_declarations() -> None:
    assert typescript_generator_declarations_are_detected()


def test_detects_rust_destructuring_declarations() -> None:
    assert rust_destructuring_declarations_are_detected()


def test_detects_rust_conditional_declarations() -> None:
    assert rust_conditional_declarations_are_detected()


def test_detects_rust_loop_declarations() -> None:
    assert rust_loop_declarations_are_detected()


def test_detects_rust_match_declarations() -> None:
    assert rust_match_declarations_are_detected()


def test_detects_rust_inline_match_arm_declarations() -> None:
    assert rust_inline_match_arm_declarations_are_detected()


def test_detects_rust_closure_parameter_declarations() -> None:
    assert rust_closure_parameter_declarations_are_detected()


def test_ignores_rust_test_function_wrappers() -> None:
    assert rust_test_function_wrappers_are_not_owned_declarations()


def test_ignores_declarations_inside_rust_raw_strings() -> None:
    assert rust_raw_string_declarations_are_ignored()


def test_splits_rust_lifetime_declarations() -> None:
    assert rust_lifetime_declarations_are_split()


def test_ignores_block_comment_declarations_after_rust_lifetime() -> None:
    assert rust_lifetime_before_block_comment_declarations_are_ignored()


def test_detects_rust_or_pattern_declarations() -> None:
    assert rust_or_pattern_declarations_are_detected()
