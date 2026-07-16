"""Mapping evidence for producer-derived eval prompt definitions."""

from __future__ import annotations

from outcomeeng_testing.evals.producer_prompt import (
    assert_duplicate_producer_section_is_rejected,
    assert_invalid_producer_files_definitions_are_rejected,
    assert_missing_producer_section_is_rejected,
    assert_non_step_tags_do_not_match_section_name,
    assert_producer_file_rejects_section_selector,
    assert_required_prompt_source_fields_are_rejected_when_missing,
    assert_selected_section_preserves_nested_step_section,
    assert_selected_section_rejects_literal_step_closing_delimiter,
    assert_similar_attribute_names_do_not_match_section_name,
    assert_unsupported_prompt_source_kind_is_rejected,
)


def test_invalid_producer_files_definitions_are_rejected() -> None:
    assert_invalid_producer_files_definitions_are_rejected()


def test_producer_file_rejects_section_selector() -> None:
    assert_producer_file_rejects_section_selector()


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
