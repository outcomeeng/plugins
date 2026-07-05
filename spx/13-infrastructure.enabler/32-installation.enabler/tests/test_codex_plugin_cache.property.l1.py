"""Level 1 property evidence for Codex cache refresh convergence."""

from __future__ import annotations

from outcomeeng_testing.harnesses.codex_cache import (
    codex_cache_property_failure_notes_include_seed_and_replay,
    successful_refresh_preserves_absent_stale_codex_reported_version,
    successful_refresh_reconciles_to_generated_codex_manifest_version,
)


def test_successful_refresh_reconciles_to_generated_codex_manifest_version() -> None:
    successful_refresh_reconciles_to_generated_codex_manifest_version()


def test_successful_refresh_preserves_absent_stale_codex_reported_version() -> None:
    successful_refresh_preserves_absent_stale_codex_reported_version()


def test_codex_cache_property_failure_notes_include_seed_and_replay() -> None:
    assert codex_cache_property_failure_notes_include_seed_and_replay()
