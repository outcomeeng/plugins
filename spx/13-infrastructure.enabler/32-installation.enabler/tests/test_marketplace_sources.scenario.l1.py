"""Level 1 scenario tests for marketplace source reconciliation."""

from outcomeeng_testing.harnesses.marketplace_sources import (
    source_reconciliation_adds_absent_runtime_sources,
    source_reconciliation_explicit_root_replaces_stale_runtime_paths,
    source_reconciliation_failed_codex_add_surfaces_error,
    source_reconciliation_preserves_user_scope_claude_plugin_installs,
    source_reconciliation_repairs_scoped_matching_codex_source,
    source_reconciliation_repairs_scoped_runtime_source_as_user_registration,
    source_reconciliation_repairs_unscoped_stale_claude_runtime_source,
    source_reconciliation_restores_enabled_user_scope_claude_plugins,
    source_reconciliation_unscoped_default_restores_only_user_plugins,
    source_reconciliation_user_restore_idempotent_errors_are_accepted,
    source_reconciliation_user_restore_non_idempotent_errors_surface,
    with_temporary_marketplace_path,
)


def test_source_reconciliation_adds_absent_runtime_sources() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_adds_absent_runtime_sources
    )


def test_source_reconciliation_unscoped_default_restores_only_user_plugins() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_unscoped_default_restores_only_user_plugins
    )


def test_source_reconciliation_explicit_root_replaces_stale_runtime_paths() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_explicit_root_replaces_stale_runtime_paths
    )


def test_source_reconciliation_preserves_user_scope_claude_plugin_installs() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_preserves_user_scope_claude_plugin_installs
    )


def test_source_reconciliation_repairs_unscoped_stale_claude_runtime_source() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_unscoped_stale_claude_runtime_source
    )


def test_source_reconciliation_repairs_scoped_runtime_source_as_user_registration() -> (
    None
):
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_scoped_runtime_source_as_user_registration
    )


def test_source_reconciliation_repairs_scoped_matching_codex_source() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_repairs_scoped_matching_codex_source
    )


def test_source_reconciliation_failed_codex_add_surfaces_error() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_failed_codex_add_surfaces_error
    )


def test_source_reconciliation_user_restore_idempotent_errors_are_accepted() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_user_restore_idempotent_errors_are_accepted
    )


def test_source_reconciliation_restores_enabled_user_scope_claude_plugins() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_restores_enabled_user_scope_claude_plugins
    )


def test_source_reconciliation_user_restore_non_idempotent_errors_surface() -> None:
    assert with_temporary_marketplace_path(
        source_reconciliation_user_restore_non_idempotent_errors_surface
    )
