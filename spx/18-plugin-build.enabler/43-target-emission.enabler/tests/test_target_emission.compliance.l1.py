"""Compliance evidence for per-target emission."""

from __future__ import annotations

from outcomeeng_testing.harnesses.target_emission import (
    claude_output_preserves_skill_dir_token,
    codex_command_frontmatter_strips_claude_fields,
    codex_output_rewrites_skill_dir_token,
    codex_skill_frontmatter_strips_claude_fields,
    every_source_file_emits_to_each_target,
    frontmatter_strip_is_idempotent,
    outputs_exclude_execution_time_injection,
    path_rewrite_is_idempotent,
    skill_dir_escape_preserves_authoring_guidance,
    target_trees_mirror_source_structure,
)


def test_every_source_file_emits_to_both_target_trees() -> None:
    assert every_source_file_emits_to_each_target()


def test_target_trees_mirror_source_structure() -> None:
    assert target_trees_mirror_source_structure()


def test_claude_output_preserves_skill_dir_token() -> None:
    assert claude_output_preserves_skill_dir_token()


def test_codex_output_rewrites_skill_dir_token_to_codex_token() -> None:
    assert codex_output_rewrites_skill_dir_token()


def test_skill_dir_rewrite_escape_preserves_authoring_guidance() -> None:
    assert skill_dir_escape_preserves_authoring_guidance()


def test_codex_skill_frontmatter_strips_claude_only_fields() -> None:
    assert codex_skill_frontmatter_strips_claude_fields()


def test_codex_command_frontmatter_strips_claude_only_fields() -> None:
    assert codex_command_frontmatter_strips_claude_fields()


def test_path_rewrite_is_idempotent() -> None:
    assert path_rewrite_is_idempotent()


def test_frontmatter_strip_is_idempotent() -> None:
    assert frontmatter_strip_is_idempotent()


def test_outputs_do_not_contain_execution_time_cat_injection() -> None:
    assert outputs_exclude_execution_time_injection()
