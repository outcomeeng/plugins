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
    source_reconciliation_adds_absent_runtime_source_at_matching_project_scope,
    source_reconciliation_unscoped_default_restores_only_user_plugins,
    source_reconciliation_accepts_matching_runtime_sources,
    source_reconciliation_accepts_relative_project_settings_source,
    source_reconciliation_replaces_git_backed_codex_source,
    source_reconciliation_replaces_mismatched_codex_path,
    source_reconciliation_explicit_root_replaces_stale_runtime_paths,
    source_reconciliation_repairs_stale_project_declaration_when_runtime_matches,
    source_reconciliation_repairs_stale_project_declaration_for_scoped_runtime,
    source_reconciliation_preserves_claude_plugin_installs_when_source_changes,
    source_reconciliation_preserves_user_scope_claude_plugin_installs,
    source_reconciliation_restores_user_plugin_from_scoped_repair_context,
    source_reconciliation_repairs_local_scope_claude_source,
    source_reconciliation_repairs_runtime_source_with_stale_scoped_settings,
    source_reconciliation_preserves_second_matching_scoped_plugin,
    source_reconciliation_filter_checks_later_repair_targets,
    source_reconciliation_filter_skips_unscoped_before_later_scoped_target,
    source_reconciliation_repairs_matching_source_with_stale_project_path,
    source_reconciliation_repairs_scoped_runtime_source_without_project_path,
    source_reconciliation_rejects_malformed_claude_settings,
    source_reconciliation_rejects_non_object_claude_settings,
    source_reconciliation_rejects_scoped_claude_plugin_without_project_path,
    source_reconciliation_repairs_unscoped_stale_claude_runtime_source,
    source_reconciliation_repairs_unscoped_runtime_with_stale_scoped_settings,
    source_reconciliation_readds_matching_scoped_settings_after_unscoped_repair,
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


def test_source_reconciliation_adds_absent_runtime_source_at_matching_project_scope() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_adds_absent_runtime_source_at_matching_project_scope
    )


def test_source_reconciliation_unscoped_default_restores_only_user_plugins() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_unscoped_default_restores_only_user_plugins
    )


def test_source_reconciliation_accepts_matching_runtime_sources() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_accepts_matching_runtime_sources
    )


def test_source_reconciliation_accepts_relative_project_settings_source() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_accepts_relative_project_settings_source
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


def test_source_reconciliation_repairs_stale_project_declaration_when_runtime_matches() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_stale_project_declaration_when_runtime_matches
    )


def test_source_reconciliation_repairs_stale_project_declaration_for_scoped_runtime() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_stale_project_declaration_for_scoped_runtime
    )


def test_source_reconciliation_preserves_claude_plugin_installs_when_source_changes() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_preserves_claude_plugin_installs_when_source_changes
    )


def test_source_reconciliation_preserves_user_scope_claude_plugin_installs() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_preserves_user_scope_claude_plugin_installs
    )


def test_source_reconciliation_restores_user_plugin_from_scoped_repair_context() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_restores_user_plugin_from_scoped_repair_context
    )


def test_source_reconciliation_repairs_local_scope_claude_source() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_local_scope_claude_source
    )


def test_source_reconciliation_repairs_runtime_source_with_stale_scoped_settings() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_runtime_source_with_stale_scoped_settings
    )


def test_source_reconciliation_preserves_second_matching_scoped_plugin() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_preserves_second_matching_scoped_plugin
    )


def test_source_reconciliation_filter_checks_later_repair_targets() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_filter_checks_later_repair_targets
    )


def test_source_reconciliation_filter_skips_unscoped_before_later_scoped_target() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_filter_skips_unscoped_before_later_scoped_target
    )


def test_source_reconciliation_repairs_matching_source_with_stale_project_path() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_matching_source_with_stale_project_path
    )


def test_source_reconciliation_repairs_scoped_runtime_source_without_project_path() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_scoped_runtime_source_without_project_path
    )


def test_source_reconciliation_rejects_malformed_claude_settings() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_rejects_malformed_claude_settings
    )


def test_source_reconciliation_rejects_non_object_claude_settings() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_rejects_non_object_claude_settings
    )


def test_source_reconciliation_rejects_scoped_claude_plugin_without_project_path() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_rejects_scoped_claude_plugin_without_project_path
    )


def test_source_reconciliation_repairs_unscoped_stale_claude_runtime_source() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_unscoped_stale_claude_runtime_source
    )


def test_source_reconciliation_repairs_unscoped_runtime_with_stale_scoped_settings() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_unscoped_runtime_with_stale_scoped_settings
    )


def test_source_reconciliation_readds_matching_scoped_settings_after_unscoped_repair() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_readds_matching_scoped_settings_after_unscoped_repair
    )


def test_source_reconciliation_failed_codex_add_surfaces_error() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_failed_codex_add_surfaces_error
    )
