"""Compliance evidence for converted Codex agent boundaries."""

from __future__ import annotations

import json
import shutil
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest

from outcomeeng.distribution.agents import (
    AGENT_NAME_FIELD,
    CODEX_AGENT_ENV_SEPARATOR,
    CODEX_AGENT_ENV_VAR,
    SHELL_ENVIRONMENT_POLICY_FIELD,
    SHELL_ENVIRONMENT_SET_FIELD,
    AgentConversionError,
    agent_environment_marker,
    convert_agents,
)
from outcomeeng.distribution.build import (
    FLAT_AGENT_PLUGIN_SEPARATOR,
    SourceFormatError,
    agent_capability,
    build,
    converted_agent_relative_path,
    source_plugin_name,
)
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    CODEX_PLUGIN_MANIFEST,
    DIST_DIR_NAME,
    RECURSIVE_GLOB,
    SKILLS_SUBDIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
)
from outcomeeng_testing.harnesses.agent_conversion import (
    LIFECYCLE_COLLISION_SOURCE,
    build_repository_agents,
    repository_wrapper_agents,
    toml_string,
    toml_table,
    write_filename_collision_sources,
)
from outcomeeng_testing.harnesses.snapshots import snapshot_files


def test_environment_marker_is_namespaced_by_source_plugin(tmp_path: Path) -> None:
    repository_agents = build_repository_agents(tmp_path)
    capability = agent_capability(Target.CODEX)

    assert repository_agents.sources_for(Target.CODEX)
    for source_path in repository_agents.sources_for(Target.CODEX):
        plugin = source_plugin_name(source_path, src_root=repository_agents.source_root)
        artifact = (
            repository_agents.dist_root
            / Target.CODEX.value
            / converted_agent_relative_path(
                plugin, source_path.stem, capability=capability
            )
        )
        parsed = tomllib.loads(artifact.read_text(encoding="utf-8"))
        marker = toml_string(
            toml_table(
                toml_table(parsed, SHELL_ENVIRONMENT_POLICY_FIELD),
                SHELL_ENVIRONMENT_SET_FIELD,
            ),
            CODEX_AGENT_ENV_VAR,
        )

        assert marker == f"{plugin}{CODEX_AGENT_ENV_SEPARATOR}{source_path.stem}"


def test_environment_marker_without_source_plugin_is_rejected() -> None:
    wrappers = repository_wrapper_agents()

    assert wrappers
    for wrapper in wrappers:
        source = replace(wrapper, source_path=Path(wrapper.source_path.name))

        with pytest.raises(AgentConversionError):
            agent_environment_marker(source)


def test_two_sources_converting_to_one_filename_fail(tmp_path: Path) -> None:
    # The build-level path-collision check below guards the generated tree.
    # This guards conversion itself, which the harnesses call directly, so a
    # colliding pair cannot silently reduce to one written definition.
    with pytest.raises(AgentConversionError):
        convert_agents(write_filename_collision_sources(tmp_path))


def test_two_sources_claiming_one_output_fail_before_the_build_writes(
    tmp_path: Path,
) -> None:
    src_root = shutil.copytree(LIFECYCLE_COLLISION_SOURCE, tmp_path / SOURCE_ROOT_NAME)
    dist_root = tmp_path / DIST_DIR_NAME
    with pytest.raises(SourceFormatError):
        build(src_root, dist_root)
    # The plan fails before any target tree is written.
    assert not snapshot_files(dist_root)


def test_flat_namespace_agents_carry_the_plugin_slug_prefix(tmp_path: Path) -> None:
    repository_agents = build_repository_agents(tmp_path)
    flat_targets = tuple(
        target for target in Target if not agent_capability(target).namespaced
    )

    assert flat_targets
    assert repository_agents.sources
    for target in flat_targets:
        capability = agent_capability(target)
        tree = repository_agents.dist_root / target.value
        artifacts = sorted(
            tree.glob(
                f"*/{SKILLS_SUBDIR_NAME}/*/{AGENTS_SUBDIR_NAME}/*{capability.suffix}"
            )
        )
        assert artifacts, f"{target.value} carries no converted agent artifacts"
        target_sources = repository_agents.sources_for(target)
        plugins = {
            source_plugin_name(source_path, src_root=repository_agents.source_root)
            for source_path in target_sources
        }
        for plugin in sorted(plugins):
            expected_stems = {
                FLAT_AGENT_PLUGIN_SEPARATOR.join((plugin, source_path.stem))
                for source_path in target_sources
                if source_plugin_name(
                    source_path, src_root=repository_agents.source_root
                )
                == plugin
            }
            actual = {
                path.stem
                for path in artifacts
                if path.relative_to(tree).parts[0] == plugin
            }

            assert actual == expected_stems
        for path in artifacts:
            declared = tomllib.loads(path.read_text(encoding="utf-8"))[AGENT_NAME_FIELD]
            assert declared == path.stem, (
                f"{path} declares name {declared!r}, which is not its filename stem"
            )


def test_converted_agents_ship_inside_a_manifest_declared_surface(
    tmp_path: Path,
) -> None:
    repository_agents = build_repository_agents(tmp_path)
    converting_targets = tuple(
        target
        for target in Target
        if not agent_capability(target).manifest_declares_agents
    )

    assert converting_targets
    for target in converting_targets:
        capability = agent_capability(target)
        tree = repository_agents.dist_root / target.value
        assert not sorted(tree.glob(f"*/{AGENTS_SUBDIR_NAME}/*")), (
            f"{target.value} carries agents outside a manifest-declared surface"
        )
        manifests = sorted(tree.glob(str(Path("*") / CODEX_PLUGIN_MANIFEST)))
        assert manifests, f"{target.value} carries no plugin manifest"
        declared_skill_roots: set[Path] = set()
        for manifest_path in manifests:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            declared_skills = manifest[SKILLS_SUBDIR_NAME]
            assert isinstance(declared_skills, str)
            plugin_root = tree / manifest_path.relative_to(tree).parts[0]
            declared_root = (plugin_root / declared_skills).resolve()
            assert declared_root == (plugin_root / SKILLS_SUBDIR_NAME).resolve()
            assert AGENTS_SUBDIR_NAME not in manifest, (
                f"{manifest_path} declares an agents field this target's manifest "
                "schema does not carry"
            )
            declared_skill_roots.add(declared_root)
        converted = sorted(
            tree.glob(
                str(Path(RECURSIVE_GLOB) / AGENTS_SUBDIR_NAME / f"*{capability.suffix}")
            )
        )
        assert converted, f"{target.value} carries no converted agent artifacts"
        for path in converted:
            assert any(
                path.resolve().is_relative_to(root) for root in declared_skill_roots
            ), f"{path} is not inside a plugin's manifest-declared skill surface"
