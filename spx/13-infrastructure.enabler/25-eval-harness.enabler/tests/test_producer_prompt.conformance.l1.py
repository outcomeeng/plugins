"""Conformance evidence for producer-derived eval prompt materialization."""

from __future__ import annotations

from outcomeeng_testing.evals.producer_prompt import (
    assert_cli_materializes_nested_eval_roots,
    assert_complete_file_templates_reject_invalid_placeholders,
    assert_materialization_preserves_placeholder_text_inside_producer_section,
    assert_materialization_rejects_noncanonical_prompt_path,
    assert_materializes_prompt_from_complete_producer_file,
    assert_materialization_rejects_absolute_producer_path,
    assert_materialization_rejects_producer_path_outside_repo,
    assert_materialization_rejects_prompt_path_outside_eval_dir,
    assert_materialization_rejects_prompt_template_alias,
    assert_materializes_prompt_from_named_producer_section,
    assert_materializes_prompt_from_ordered_complete_producer_files,
    assert_producer_files_check_detects_each_source_change,
)


def test_materializes_prompt_from_named_producer_section() -> None:
    assert_materializes_prompt_from_named_producer_section()


def test_materializes_prompt_from_complete_producer_file() -> None:
    assert_materializes_prompt_from_complete_producer_file()


def test_materializes_prompt_from_ordered_complete_producer_files() -> None:
    assert_materializes_prompt_from_ordered_complete_producer_files()


def test_producer_files_check_detects_each_source_change() -> None:
    assert_producer_files_check_detects_each_source_change()


def test_complete_file_templates_reject_invalid_placeholders() -> None:
    assert_complete_file_templates_reject_invalid_placeholders()


def test_materialization_rejects_prompt_path_outside_eval_dir() -> None:
    assert_materialization_rejects_prompt_path_outside_eval_dir()


def test_materialization_rejects_noncanonical_prompt_path() -> None:
    assert_materialization_rejects_noncanonical_prompt_path()


def test_materialization_rejects_prompt_template_alias() -> None:
    assert_materialization_rejects_prompt_template_alias()


def test_materialization_rejects_absolute_producer_path() -> None:
    assert_materialization_rejects_absolute_producer_path()


def test_materialization_rejects_producer_path_outside_repo() -> None:
    assert_materialization_rejects_producer_path_outside_repo()


def test_materialization_preserves_placeholder_text_inside_producer_section() -> None:
    assert_materialization_preserves_placeholder_text_inside_producer_section()


def test_cli_materializes_nested_eval_roots() -> None:
    assert_cli_materializes_nested_eval_roots()
