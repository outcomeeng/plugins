"""Compliance evidence for plugin catalog generation."""

from __future__ import annotations

from outcomeeng_testing.harnesses.plugin_catalog import (
    check_mode_fails_when_readme_catalog_drifts,
    generated_catalog_is_deterministic,
    generated_catalog_uses_declared_sentinels,
    purpose_shortening_preserves_untrimmed_em_dash,
    runtime_divergent_skill_descriptions_name_each_target,
)


def test_generated_catalog_is_deterministic() -> None:
    assert generated_catalog_is_deterministic()


def test_generated_catalog_uses_declared_sentinels() -> None:
    assert generated_catalog_uses_declared_sentinels()


def test_check_mode_fails_when_readme_catalog_drifts() -> None:
    assert check_mode_fails_when_readme_catalog_drifts()


def test_runtime_divergent_skill_descriptions_name_each_target() -> None:
    assert runtime_divergent_skill_descriptions_name_each_target()


def test_purpose_shortening_preserves_untrimmed_em_dash() -> None:
    assert purpose_shortening_preserves_untrimmed_em_dash()
