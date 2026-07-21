"""Compliance evidence for per-target emission."""

from __future__ import annotations

from outcomeeng.distribution.build import agent_capability
from outcomeeng.distribution.contracts import SKILLS_SUBDIR_NAME, Target
from outcomeeng_testing.harnesses.target_emission import (
    claude_output_preserves_skill_dir_token,
    codex_output_rewrites_skill_dir_token,
    codex_skill_frontmatter_strips_claude_fields,
    frontmatter_strip_is_idempotent,
    outputs_exclude_execution_time_injection,
    path_rewrite_is_idempotent,
    planned_matches_emitted,
    planned_sources,
    repeated_include_emits_shared_source_once,
    skill_dir_escape_preserves_authoring_guidance,
    source_emission_counts,
    structure_deviations,
    synthetic_inventory_is_complete,
    target_scoped_includes_emit_only_to_matching_tree,
)


def test_every_source_file_emits_to_both_target_trees() -> None:
    counts = source_emission_counts()
    sources = planned_sources()
    assert sources
    for target, per_source in counts.items():
        missing = [source for source in sources if per_source[source] < 1]
        assert not missing, f"{target.value} emits nothing for {missing}"
    assert planned_matches_emitted() == dict.fromkeys(counts, True)
    assert synthetic_inventory_is_complete()


def test_target_trees_mirror_source_structure() -> None:
    capabilities = {target: agent_capability(target) for target in Target}
    for target, deviations in structure_deviations().items():
        if capabilities[target].manifest_declares_agents:
            assert not deviations, (
                f"{target.value} declares agents in its manifest, so no output "
                f"may leave its mirrored path: {deviations}"
            )
            continue
        for path in deviations:
            assert path.parts[1] == SKILLS_SUBDIR_NAME, (
                f"{target.value} deviation outside the lifecycle skill: {path}"
            )
            assert path.suffix == capabilities[target].suffix, (
                f"{target.value} deviation is not a native agent artifact: {path}"
            )


def test_repeated_include_emits_shared_source_once_per_target() -> None:
    assert repeated_include_emits_shared_source_once()


def test_claude_output_preserves_skill_dir_token() -> None:
    assert claude_output_preserves_skill_dir_token()


def test_codex_output_rewrites_skill_dir_token_to_codex_token() -> None:
    assert codex_output_rewrites_skill_dir_token()


def test_skill_dir_rewrite_escape_preserves_authoring_guidance() -> None:
    assert skill_dir_escape_preserves_authoring_guidance()


def test_codex_skill_frontmatter_strips_claude_only_fields() -> None:
    assert codex_skill_frontmatter_strips_claude_fields()


def test_target_scoped_includes_emit_only_to_matching_tree() -> None:
    assert target_scoped_includes_emit_only_to_matching_tree()


def test_path_rewrite_is_idempotent() -> None:
    assert path_rewrite_is_idempotent()


def test_frontmatter_strip_is_idempotent() -> None:
    assert frontmatter_strip_is_idempotent()


def test_outputs_do_not_contain_execution_time_skill_content_injection() -> None:
    assert outputs_exclude_execution_time_injection()
