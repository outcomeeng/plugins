"""Level 1 scenario tests for marketplace source reconciliation."""

from outcomeeng_testing.harnesses.marketplace_sources import (
    source_reconciliation_accepts_unscoped_matching_claude_runtime_source,
    source_reconciliation_adds_absent_runtime_sources,
    source_reconciliation_adds_user_registration_for_managed_claude_source,
    source_reconciliation_explicit_root_replaces_stale_runtime_paths,
    source_reconciliation_failed_codex_add_surfaces_error,
    source_reconciliation_ignores_managed_scope_claude_plugins_without_project_path,
    source_reconciliation_ignores_managed_source_at_non_canonical_path,
    source_reconciliation_ignores_project_duplicate_when_user_source_canonical,
    source_reconciliation_ignores_project_source_and_adds_user_registration,
    source_reconciliation_prefers_shared_root_over_stale_user_duplicate,
    source_reconciliation_preserves_user_scope_claude_plugin_installs,
    source_reconciliation_rejects_project_source_without_project_path,
    source_reconciliation_repairs_scoped_matching_codex_source,
    source_reconciliation_repairs_scoped_stale_codex_duplicate,
    source_reconciliation_repairs_stale_codex_duplicate,
    source_reconciliation_repairs_stale_user_source_despite_unscoped_canonical_match,
    source_reconciliation_repairs_unscoped_stale_claude_runtime_source,
    source_reconciliation_restores_enabled_user_scope_claude_plugins,
    source_reconciliation_unscoped_default_adds_user_registration_and_restores_user_plugins,
    source_reconciliation_user_restore_already_enabled_response_is_accepted,
    source_reconciliation_user_restore_idempotent_errors_are_accepted,
    source_reconciliation_user_restore_non_idempotent_errors_surface,
    with_temporary_marketplace_path,
)


def test_source_reconciliation_repairs_user_registration_paths() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_adds_absent_runtime_sources
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_unscoped_default_adds_user_registration_and_restores_user_plugins
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_explicit_root_replaces_stale_runtime_paths
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_preserves_user_scope_claude_plugin_installs
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_unscoped_stale_claude_runtime_source
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_accepts_unscoped_matching_claude_runtime_source
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_adds_user_registration_for_managed_claude_source
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_prefers_shared_root_over_stale_user_duplicate
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_ignores_project_duplicate_when_user_source_canonical
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_stale_user_source_despite_unscoped_canonical_match
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_rejects_project_source_without_project_path
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_ignores_project_source_and_adds_user_registration
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_scoped_matching_codex_source
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_stale_codex_duplicate
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_scoped_stale_codex_duplicate
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_failed_codex_add_surfaces_error
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_user_restore_idempotent_errors_are_accepted
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_user_restore_already_enabled_response_is_accepted
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_ignores_managed_scope_claude_plugins_without_project_path
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_ignores_managed_source_at_non_canonical_path
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_restores_enabled_user_scope_claude_plugins
    )
    assert with_temporary_marketplace_path(
        source_reconciliation_user_restore_non_idempotent_errors_surface
    )
