"""Conformance evidence for producer-derived eval prompt materialization."""

from __future__ import annotations

from outcomeeng_testing.evals.producer_prompt import (
    assert_check_accepts_current_materialized_prompt,
    assert_check_rejects_stale_materialized_prompt,
    assert_cli_materializes_and_checks_prompt_drift,
    assert_cli_materializes_nested_eval_roots,
    assert_duplicate_producer_section_is_rejected,
    assert_materialization_preserves_placeholder_text_inside_producer_section,
    assert_materialization_rejects_absolute_producer_path,
    assert_materialization_rejects_producer_path_outside_repo,
    assert_materialization_rejects_prompt_path_outside_eval_dir,
    assert_materialization_rejects_prompt_template_alias,
    assert_materialized_prompt_changes_only_with_selected_section,
    assert_materializes_prompt_from_named_producer_section,
    assert_missing_producer_section_is_rejected,
    assert_non_step_tags_do_not_match_section_name,
    assert_required_prompt_source_fields_are_rejected_when_missing,
    assert_selected_section_preserves_nested_step_section,
    assert_selected_section_rejects_literal_step_closing_delimiter,
    assert_similar_attribute_names_do_not_match_section_name,
    assert_unsupported_prompt_source_kind_is_rejected,
)


def test_materializes_prompt_from_named_producer_section() -> None:
    assert_materializes_prompt_from_named_producer_section()


def test_check_accepts_current_materialized_prompt() -> None:
    assert_check_accepts_current_materialized_prompt()


def test_materialized_prompt_changes_only_with_selected_section() -> None:
    assert_materialized_prompt_changes_only_with_selected_section()


def test_check_rejects_stale_materialized_prompt() -> None:
    assert_check_rejects_stale_materialized_prompt()


def test_materialization_rejects_prompt_path_outside_eval_dir() -> None:
    assert_materialization_rejects_prompt_path_outside_eval_dir()


def test_materialization_rejects_prompt_template_alias() -> None:
    assert_materialization_rejects_prompt_template_alias()


def test_materialization_rejects_absolute_producer_path() -> None:
    assert_materialization_rejects_absolute_producer_path()


def test_materialization_rejects_producer_path_outside_repo() -> None:
    assert_materialization_rejects_producer_path_outside_repo()


def test_materialization_preserves_placeholder_text_inside_producer_section() -> None:
    assert_materialization_preserves_placeholder_text_inside_producer_section()


def test_missing_producer_section_is_rejected() -> None:
    assert_missing_producer_section_is_rejected()


def test_similar_attribute_names_do_not_match_section_name() -> None:
    assert_similar_attribute_names_do_not_match_section_name()


def test_non_step_tags_do_not_match_section_name() -> None:
    assert_non_step_tags_do_not_match_section_name()


def test_selected_section_rejects_literal_step_closing_delimiter() -> None:
    assert_selected_section_rejects_literal_step_closing_delimiter()


def test_selected_section_preserves_nested_step_section() -> None:
    assert_selected_section_preserves_nested_step_section()


def test_duplicate_producer_section_is_rejected() -> None:
    assert_duplicate_producer_section_is_rejected()


def test_unsupported_prompt_source_kind_is_rejected() -> None:
    assert_unsupported_prompt_source_kind_is_rejected()


def test_missing_prompt_source_fields_are_rejected() -> None:
    assert_required_prompt_source_fields_are_rejected_when_missing()


def test_cli_materializes_and_checks_prompt_drift() -> None:
    assert_cli_materializes_and_checks_prompt_drift()


def test_cli_materializes_nested_eval_roots() -> None:
    assert_cli_materializes_nested_eval_roots()
