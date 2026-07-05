"""Level-1 installation scenario evidence for Codex cache preservation."""

from __future__ import annotations

from outcomeeng_testing.harnesses.codex_cache_scenarios import (
    codex_cache_scenarios_pass,
)


def test_codex_cache_scenarios() -> None:
    assert codex_cache_scenarios_pass()
