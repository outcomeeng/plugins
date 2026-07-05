"""Level 1 conformance tests for local marketplace source discovery."""

from outcomeeng_testing.harnesses.marketplace_sources import (
    parse_codex_marketplace_sources_accepts_local_source,
    parse_codex_marketplace_sources_accepts_nested_local_source,
    parse_claude_marketplace_sources_normalizes_directory_source,
    parse_claude_installed_plugins_keeps_scope_state_and_project_path,
    parse_codex_marketplace_sources_accepts_nested_git_source,
    parse_codex_marketplace_sources_accepts_empty_marketplace_array,
    require_matching_local_sources_rejects_git_backed_codex,
    require_matching_local_sources_rejects_path_mismatch,
    available_codex_plugins_are_read_from_dist_codex,
    source_reconciliation_adds_absent_runtime_sources,
    source_reconciliation_accepts_matching_runtime_sources,
    source_reconciliation_replaces_git_backed_codex_source,
    source_reconciliation_replaces_mismatched_codex_path,
    source_reconciliation_explicit_root_replaces_stale_runtime_paths,
    source_reconciliation_preserves_claude_plugin_installs_when_source_changes,
    source_reconciliation_accepts_already_enabled_claude_plugin_restore,
    source_reconciliation_rejects_scoped_claude_plugin_without_project_path,
    source_reconciliation_failed_codex_add_surfaces_error,
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


def test_available_codex_plugins_are_read_from_dist_codex() -> None:
    assert with_temporary_marketplace_path(
        available_codex_plugins_are_read_from_dist_codex
    )


def test_source_reconciliation_adds_absent_runtime_sources() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_adds_absent_runtime_sources
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


def test_source_reconciliation_explicit_root_replaces_stale_runtime_paths() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_explicit_root_replaces_stale_runtime_paths
    )


def test_source_reconciliation_preserves_claude_plugin_installs_when_source_changes() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_preserves_claude_plugin_installs_when_source_changes
    )


def test_source_reconciliation_accepts_already_enabled_claude_plugin_restore() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_accepts_already_enabled_claude_plugin_restore
    )


def test_source_reconciliation_rejects_scoped_claude_plugin_without_project_path() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_rejects_scoped_claude_plugin_without_project_path
    )


def test_source_reconciliation_failed_codex_add_surfaces_error() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_failed_codex_add_surfaces_error
    )
