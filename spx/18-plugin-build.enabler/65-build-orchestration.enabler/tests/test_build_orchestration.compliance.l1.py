"""Compliance evidence for build orchestration wiring."""

from __future__ import annotations

from outcomeeng_testing.harnesses.build_orchestration import (
    claude_marketplace_matches_runtime_contract,
    codex_marketplace_matches_runtime_contract,
    dist_diff_surface_violations_are_rejected,
    dist_diff_surfaces_match_contract,
    justfile_matches_build_contract,
    justfile_recipe_violation_is_rejected,
    json_config_path_escape_is_rejected,
    lefthook_config_path_escape_is_rejected,
    lefthook_matches_build_contract,
    quality_gate_matches_build_orchestration_contract,
    repository_build_orchestration_matches_contract,
)


def test_repository_passes_the_build_orchestration_contract() -> None:
    assert repository_build_orchestration_matches_contract()


def test_quality_gate_runs_the_build_orchestration_contract() -> None:
    assert quality_gate_matches_build_orchestration_contract()


def test_dist_diff_surfaces_invoke_the_actionable_reporter() -> None:
    assert dist_diff_surfaces_match_contract()


def test_dist_diff_surface_violations_are_rejected() -> None:
    assert dist_diff_surface_violations_are_rejected()


def test_justfile_declares_build_skills_recipe() -> None:
    assert justfile_matches_build_contract()


def test_justfile_recipe_violation_is_rejected() -> None:
    assert justfile_recipe_violation_is_rejected()


def test_lefthook_runs_build_and_checks_dist_drift() -> None:
    assert lefthook_matches_build_contract()


def test_lefthook_config_path_escape_is_rejected() -> None:
    assert lefthook_config_path_escape_is_rejected()


def test_json_config_path_escape_is_rejected() -> None:
    assert json_config_path_escape_is_rejected()


def test_claude_marketplace_points_at_dist_claude() -> None:
    assert claude_marketplace_matches_runtime_contract()


def test_codex_marketplace_points_at_dist_codex() -> None:
    assert codex_marketplace_matches_runtime_contract()
