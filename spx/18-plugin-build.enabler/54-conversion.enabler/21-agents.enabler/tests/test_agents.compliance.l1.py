"""Compliance evidence for converted Codex agent boundaries."""

from __future__ import annotations

import json
import tomllib

from outcomeeng.distribution.build import agent_capability
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    CODEX_PLUGIN_SUBDIR_NAME,
    DIST_DIR_NAME,
    SKILLS_SUBDIR_NAME,
    Target,
)
from outcomeeng_testing.harnesses.distribution import REPOSITORY_ROOT


from outcomeeng_testing.harnesses.agent_conversion import (
    assert_default_source_root_uses_rendered_codex_agents,
    assert_duplicate_generated_agent_filename_fails_before_install_writes,
    assert_environment_marker_is_namespaced_by_source_plugin,
    assert_environment_marker_without_source_plugin_is_rejected,
    assert_generated_toml_stays_outside_codex_plugin_manifest_content,
    assert_install_overwrites_generated_owned_agent_from_manifest,
    assert_install_refuses_to_claim_untracked_identical_agent,
    assert_invalid_generated_manifest_uses_converter_error,
    assert_manual_guidance_preserves_source_only_fields,
)


def test_manual_guidance_preserves_source_only_fields() -> None:
    assert_manual_guidance_preserves_source_only_fields()


def test_default_source_root_uses_rendered_codex_agents() -> None:
    assert_default_source_root_uses_rendered_codex_agents()


def test_generated_toml_stays_outside_codex_plugin_manifest_content() -> None:
    assert_generated_toml_stays_outside_codex_plugin_manifest_content()


def test_environment_marker_is_namespaced_by_source_plugin() -> None:
    assert_environment_marker_is_namespaced_by_source_plugin()


def test_environment_marker_without_source_plugin_is_rejected() -> None:
    assert_environment_marker_without_source_plugin_is_rejected()


def test_invalid_generated_manifest_uses_converter_error() -> None:
    assert_invalid_generated_manifest_uses_converter_error()


def test_install_refuses_to_claim_untracked_identical_agent() -> None:
    assert_install_refuses_to_claim_untracked_identical_agent()


def test_install_overwrites_generated_owned_agent_from_manifest() -> None:
    assert_install_overwrites_generated_owned_agent_from_manifest()


def test_duplicate_generated_agent_filename_fails_before_install_writes() -> None:
    assert_duplicate_generated_agent_filename_fails_before_install_writes()


def test_flat_namespace_agents_carry_the_plugin_slug_prefix() -> None:
    dist_root = REPOSITORY_ROOT / DIST_DIR_NAME
    for target in Target:
        capability = agent_capability(target)
        if capability.namespaced:
            continue
        tree = dist_root / target.value
        artifacts = sorted(
            path
            for path in tree.glob(
                f"*/{SKILLS_SUBDIR_NAME}/*/{AGENTS_SUBDIR_NAME}/*{capability.suffix}"
            )
        )
        assert artifacts, f"{target.value} carries no converted agent artifacts"
        for path in artifacts:
            plugin = path.relative_to(tree).parts[0]
            prefix = f"{plugin}_"
            assert path.name.startswith(prefix), (
                f"{path} filename lacks the {prefix!r} namespace prefix"
            )
            declared = tomllib.loads(path.read_text(encoding="utf-8"))["name"]
            assert declared == path.stem, (
                f"{path} declares name {declared!r}, which is not its filename stem"
            )
            assert declared.startswith(prefix), (
                f"{path} declares name {declared!r} without the {prefix!r} prefix, so "
                "a policy matching on name cannot attribute it to its plugin"
            )


def test_converted_agents_ship_inside_a_manifest_declared_surface() -> None:
    dist_root = REPOSITORY_ROOT / DIST_DIR_NAME
    for target in Target:
        capability = agent_capability(target)
        if capability.manifest_declares_agents:
            continue
        tree = dist_root / target.value
        assert not sorted(tree.glob(f"*/{AGENTS_SUBDIR_NAME}/*")), (
            f"{target.value} carries agents outside a manifest-declared surface"
        )
        for path in tree.glob(
            f"*/{SKILLS_SUBDIR_NAME}/*/{AGENTS_SUBDIR_NAME}/*{capability.suffix}"
        ):
            assert path.relative_to(tree).parts[1] == SKILLS_SUBDIR_NAME, (
                f"{path} is not inside the plugin's declared skill surface"
            )
        for manifest_path in tree.glob(f"*/{CODEX_PLUGIN_SUBDIR_NAME}/plugin.json"):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            assert "agents" not in manifest, (
                f"{manifest_path} declares an agents field this target's manifest "
                "schema does not carry"
            )
