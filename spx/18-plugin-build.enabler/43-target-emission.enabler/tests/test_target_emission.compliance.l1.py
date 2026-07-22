"""Compliance evidence for per-target emission."""

from __future__ import annotations

from outcomeeng_testing.harnesses.distribution import CANONICAL_SOURCE_ROOT
from outcomeeng.distribution.build import (
    AGENT_CAPABILITY_REGISTRY,
    EmissionAction,
    agent_capability,
    agent_slug,
    plugin_names,
    template_source_files,
)
from outcomeeng.distribution.contracts import SKILLS_SUBDIR_NAME, Target
from outcomeeng_testing.harnesses.target_emission import (
    claude_output_preserves_skill_dir_token,
    codex_output_rewrites_skill_dir_token,
    codex_skill_frontmatter_strips_claude_fields,
    frontmatter_strip_is_idempotent,
    outputs_exclude_execution_time_injection,
    path_rewrite_is_idempotent,
    planned_versus_emitted,
    planned_sources,
    repeated_include_emits_shared_source_once,
    skill_dir_escape_preserves_authoring_guidance,
    source_emission_counts,
    agent_artifact_paths,
    agent_artifacts_carrying_foreign_skill_dir_token,
    structure_deviations,
    synthetic_inventory,
    target_scoped_includes_emit_only_to_matching_tree,
)


def test_every_source_file_emits_to_both_target_trees() -> None:
    counts = source_emission_counts()
    sources = planned_sources()
    assert sources
    template_sources = set(template_source_files(CANONICAL_SOURCE_ROOT))
    plugin_count = len(plugin_names(CANONICAL_SOURCE_ROOT))
    for target, per_source in counts.items():
        missing = [source for source in sources if per_source[source] < 1]
        assert not missing, f"{target.value} emits nothing for {missing}"
        # An ordinary source emits exactly once per target; only a per-plugin
        # template fans out, and then exactly once per plugin. Requiring only
        # "at least one" would let a duplicate emission pass unnoticed.
        for source in sources:
            expected = plugin_count if source in template_sources else 1
            assert per_source[source] == expected, (
                f"{target.value} emits {per_source[source]} outputs for {source}, "
                f"expected {expected}"
            )

    for target, inventory in planned_versus_emitted().items():
        assert inventory.planned_paths == inventory.emitted_paths, (
            f"{target.value} planned/emitted path mismatch: "
            f"{inventory.planned_paths ^ inventory.emitted_paths}"
        )
        assert inventory.planned_directories == inventory.emitted_directories, (
            f"{target.value} planned/emitted directory mismatch: "
            f"{inventory.planned_directories ^ inventory.emitted_directories}"
        )

    fixture = synthetic_inventory()
    assert fixture.covered_subdirs == fixture.expected_subdirs, (
        "synthetic fixture misses plugin subdirectories: "
        f"{fixture.expected_subdirs - fixture.covered_subdirs}"
    )
    assert any(len(path.parts) == 2 for path in fixture.source_paths), (
        "synthetic fixture covers no plugin-root file"
    )
    required_actions = {
        EmissionAction.FAN_OUT,
        EmissionAction.CONVERT_AGENT,
        EmissionAction.PLACEMENT_MANIFEST,
    }
    assert required_actions <= fixture.covered_actions, (
        f"synthetic fixture misses emission actions: "
        f"{required_actions - fixture.covered_actions}"
    )
    for target, per_source in fixture.per_source_counts.items():
        uncovered = [path for path in fixture.source_paths if per_source[path] < 1]
        assert not uncovered, f"{target.value} emits nothing for {uncovered}"
    for target, inventory in fixture.planned_versus_emitted.items():
        assert inventory.planned_paths == inventory.emitted_paths, (
            f"synthetic {target.value} planned/emitted mismatch: "
            f"{inventory.planned_paths ^ inventory.emitted_paths}"
        )


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


def test_agent_capabilities_resolve_from_the_source_owned_registry() -> None:
    for target in Target:
        capability = agent_capability(target)
        assert capability.suffix.startswith("."), (
            f"{target.value} declares no native agent artifact suffix"
        )
        # Filename shape comes from the registry's namespace flag, not from
        # emission logic: a namespaced target keeps the bare stem, a flat one
        # takes the plugin slug as a prefix.
        slug = agent_slug("someplugin", "someagent", capability=capability)
        assert slug == (
            "someagent" if capability.namespaced else "someplugin_someagent"
        ), f"{target.value} derives an unexpected agent slug {slug!r}"
        if capability.manifest_declares_agents:
            assert capability.checkout_directory is None, (
                f"{target.value} declares agents in its manifest, so it needs no "
                "checkout placement directory"
            )
        else:
            assert capability.checkout_directory, (
                f"{target.value} cannot declare agents in its manifest, so it must "
                "name the checkout directory its agents are placed into"
            )


def test_no_target_tree_carries_an_agent_artifact_it_cannot_read() -> None:
    foreign_suffixes = {
        target: {
            other.suffix
            for name, other in AGENT_CAPABILITY_REGISTRY.items()
            if name != target.value
        }
        - {agent_capability(target).suffix}
        for target in Target
    }
    for target in Target:
        capability = agent_capability(target)
        artifacts = agent_artifact_paths(target)
        assert artifacts, (
            f"{target.value} carries no agent artifacts, so this check would "
            "pass vacuously"
        )
        for path in artifacts:
            assert path.suffix == capability.suffix, (
                f"{target.value} carries {path}, whose suffix is not this "
                f"target's native agent format {capability.suffix}"
            )
            assert path.suffix not in foreign_suffixes[target], (
                f"{target.value} carries a foreign agent artifact: {path}"
            )


def test_no_agent_artifact_carries_another_targets_skill_dir_token() -> None:
    # Conversion emits a derived artifact, so it bypasses the rendered-text
    # corpus the skill-dir rewrite assertions draw from. Reading the committed
    # agent artifacts directly keeps the rewrite contract reachable for the
    # converted class instead of holding only where the corpus already looks.
    for target in Target:
        assert agent_artifact_paths(target), (
            f"{target.value} carries no agent artifacts, so this check would "
            "pass vacuously"
        )
        leaked = agent_artifacts_carrying_foreign_skill_dir_token(target)
        assert not leaked, (
            f"{target.value} agent artifacts carry another target's skill-dir "
            f"token, so conversion skipped the rewrite: {leaked}"
        )
