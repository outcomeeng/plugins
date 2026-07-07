"""Level 1 compliance evidence for Codex cache refresh commands."""

from __future__ import annotations

from outcomeeng_testing.harnesses.codex_cache import (
    local_refresh_reads_addable_codex_plugins_from_dist_codex,
    local_refresh_never_invokes_marketplace_upgrade,
)


def test_local_refresh_reads_addable_codex_plugins_from_dist_codex() -> None:
    local_refresh_reads_addable_codex_plugins_from_dist_codex()


def test_local_refresh_never_invokes_marketplace_upgrade() -> None:
    assert local_refresh_never_invokes_marketplace_upgrade()
