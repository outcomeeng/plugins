"""Level 1 conformance tests for local marketplace source discovery."""

from outcomeeng_testing.harnesses.marketplace_sources import (
    parse_codex_marketplace_sources_accepts_local_source,
    parse_codex_marketplace_sources_accepts_nested_local_source,
    parse_claude_marketplace_sources_normalizes_directory_source,
    parse_claude_installed_plugins_keeps_scope_state_and_project_path,
    parse_codex_marketplace_sources_accepts_nested_git_source,
    parse_codex_marketplace_sources_accepts_empty_marketplace_array,
    parse_claude_marketplace_sources_prefers_user_directory_source,
    parse_codex_marketplace_sources_prefers_local_source,
    require_matching_local_sources_rejects_git_backed_codex,
    require_matching_local_sources_rejects_path_mismatch,
    source_reconciliation_accepts_matching_runtime_sources,
    source_reconciliation_replaces_git_backed_codex_source,
    source_reconciliation_replaces_mismatched_codex_path,
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


def test_source_reconciliation_replaces_git_backed_codex_source() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_replaces_git_backed_codex_source
    )


def test_source_reconciliation_replaces_mismatched_codex_path() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_replaces_mismatched_codex_path
    )
