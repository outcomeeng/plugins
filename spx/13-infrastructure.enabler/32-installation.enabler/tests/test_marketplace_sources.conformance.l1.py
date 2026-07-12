"""Level 1 conformance tests for local marketplace source discovery."""

from outcomeeng_testing.harnesses.marketplace_sources import (
    claude_directory_root_does_not_require_codex_configuration,
    claude_directory_root_ignores_project_scope_duplicate,
    claude_directory_root_rejects_duplicate_local_roots,
    parse_codex_marketplace_sources_accepts_local_source,
    parse_codex_marketplace_sources_accepts_nested_local_source,
    parse_claude_marketplace_sources_normalizes_directory_source,
    parse_claude_installed_plugins_keeps_scope_state_and_project_path,
    parse_codex_marketplace_sources_accepts_nested_git_source,
    parse_codex_marketplace_sources_accepts_empty_marketplace_array,
    parse_marketplace_sources_reject_local_sources_without_paths,
    parse_claude_marketplace_sources_prefers_user_directory_source,
    parse_codex_marketplace_sources_prefers_local_source,
    require_matching_local_sources_rejects_git_backed_codex,
    require_matching_local_sources_rejects_path_mismatch,
    source_reconciliation_accepts_duplicate_lower_priority_matching_sources,
    source_reconciliation_accepts_matching_runtime_sources,
    source_reconciliation_rejects_ambiguous_claude_roots,
    source_reconciliation_rejects_ambiguous_shared_roots,
    source_reconciliation_replaces_git_backed_codex_source,
    source_reconciliation_replaces_mismatched_codex_path,
    source_validation_accepts_shared_root_with_stale_user_duplicate,
    source_validation_prefers_user_source_over_stale_project_or_local_duplicate,
    with_temporary_marketplace_path,
)


def test_parse_codex_marketplace_sources_accepts_local_source() -> None:
    assert with_temporary_marketplace_path(
        parse_codex_marketplace_sources_accepts_local_source
    )


def test_parse_codex_marketplace_sources_accepts_nested_local_source() -> None:
    assert with_temporary_marketplace_path(
        parse_codex_marketplace_sources_accepts_nested_local_source
    )


def test_parse_claude_marketplace_sources_normalizes_directory_source() -> None:
    assert with_temporary_marketplace_path(
        parse_claude_marketplace_sources_normalizes_directory_source
    )


def test_parse_claude_marketplace_sources_prefers_user_directory_source() -> None:
    assert with_temporary_marketplace_path(
        parse_claude_marketplace_sources_prefers_user_directory_source
    )


def test_parse_codex_marketplace_sources_prefers_local_source() -> None:
    assert with_temporary_marketplace_path(
        parse_codex_marketplace_sources_prefers_local_source
    )


def test_parse_claude_installed_plugins_keeps_scope_state_and_project_path() -> None:
    assert with_temporary_marketplace_path(
        parse_claude_installed_plugins_keeps_scope_state_and_project_path
    )


def test_parse_codex_marketplace_sources_accepts_nested_git_source() -> None:
    assert parse_codex_marketplace_sources_accepts_nested_git_source()


def test_parse_codex_marketplace_sources_accepts_empty_marketplace_array() -> None:
    assert parse_codex_marketplace_sources_accepts_empty_marketplace_array()


def test_parse_marketplace_sources_reject_local_sources_without_paths() -> None:
    assert parse_marketplace_sources_reject_local_sources_without_paths()


def test_require_matching_local_sources_rejects_git_backed_codex() -> None:
    assert with_temporary_marketplace_path(
        require_matching_local_sources_rejects_git_backed_codex
    )


def test_require_matching_local_sources_rejects_path_mismatch() -> None:
    assert with_temporary_marketplace_path(
        require_matching_local_sources_rejects_path_mismatch
    )


def test_source_reconciliation_accepts_matching_runtime_sources() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_accepts_matching_runtime_sources
    )


def test_source_reconciliation_accepts_duplicate_lower_priority_matching_sources() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_accepts_duplicate_lower_priority_matching_sources
    )


def test_source_validation_prefers_user_source_over_stale_project_or_local_duplicate() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_validation_prefers_user_source_over_stale_project_or_local_duplicate
    )


def test_source_validation_accepts_shared_root_with_stale_user_duplicate() -> None:
    assert with_temporary_marketplace_path(
        source_validation_accepts_shared_root_with_stale_user_duplicate
    )


def test_claude_directory_root_does_not_require_codex_configuration() -> None:
    assert with_temporary_marketplace_path(
        claude_directory_root_does_not_require_codex_configuration
    )


def test_claude_directory_root_rejects_duplicate_local_roots() -> None:
    assert with_temporary_marketplace_path(
        claude_directory_root_rejects_duplicate_local_roots
    )


def test_claude_directory_root_ignores_project_scope_duplicate() -> None:
    assert with_temporary_marketplace_path(
        claude_directory_root_ignores_project_scope_duplicate
    )


def test_source_reconciliation_rejects_ambiguous_shared_roots() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_rejects_ambiguous_shared_roots
    )


def test_source_reconciliation_rejects_ambiguous_claude_roots() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_rejects_ambiguous_claude_roots
    )


def test_source_reconciliation_replaces_git_backed_codex_source() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_replaces_git_backed_codex_source
    )


def test_source_reconciliation_replaces_mismatched_codex_path() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_replaces_mismatched_codex_path
    )
