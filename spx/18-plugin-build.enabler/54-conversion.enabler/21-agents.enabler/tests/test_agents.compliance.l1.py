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
    AgentConversionError,
    agent_environment_marker,
    convert_agents,
    iter_agent_files,
    parse_agent_markdown,
)
from outcomeeng.distribution.build import (
    FLAT_AGENT_PLUGIN_SEPARATOR,
    LIFECYCLE_TEMPLATE_NAME,
    SourceFormatError,
    agent_capability,
    agent_slug,
    build,
)
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    CODEX_PLUGIN_SUBDIR_NAME,
    DIST_DIR_NAME,
    PLUGINS_DIR_NAME,
    SKILLS_SUBDIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
)
from outcomeeng_testing.harnesses.agent_conversion import (
    DUPLICATE_REVIEWER_FIXTURE,
    DUPLICATE_REVIEWER_BANG_FIXTURE,
    LIFECYCLE_COLLISION_SOURCE,
    PLUGIN_NAME,
    agent_conversion_fixture,
    build_repository_agents,
    toml_string,
    toml_table,
)
from outcomeeng_testing.harnesses.distribution import REPOSITORY_ROOT, snapshot_files
from outcomeeng_testing.harnesses.src_tree import write_agent_source


def test_environment_marker_is_namespaced_by_source_plugin(tmp_path: Path) -> None:
    repository_agents = build_repository_agents(tmp_path)
    capability = agent_capability(Target.CODEX)

    assert repository_agents.sources
    for source_path in repository_agents.sources:
        plugin = source_path.parents[1].name
        generated_type = agent_slug(
            plugin,
            source_path.stem,
            capability=capability,
        )
        artifact = (
            repository_agents.dist_root
            / Target.CODEX.value
            / plugin
            / SKILLS_SUBDIR_NAME
            / f"{plugin}-{LIFECYCLE_TEMPLATE_NAME}"
            / AGENTS_SUBDIR_NAME
            / f"{generated_type}{capability.suffix}"
        )
        parsed = tomllib.loads(artifact.read_text(encoding="utf-8"))
        marker = toml_string(
            toml_table(toml_table(parsed, "shell_environment_policy"), "set"),
            CODEX_AGENT_ENV_VAR,
        )
        expected_type = source_path.stem

        assert marker == (f"{plugin}{CODEX_AGENT_ENV_SEPARATOR}{expected_type}")


def test_environment_marker_without_source_plugin_is_rejected() -> None:
    source_path = iter_agent_files(
        REPOSITORY_ROOT / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME
    )[0]
    source = replace(
        parse_agent_markdown(source_path),
        source_path=Path(source_path.name),
    )

    with pytest.raises(AgentConversionError):
        agent_environment_marker(source)


def test_two_sources_converting_to_one_filename_fail(tmp_path: Path) -> None:
    # The build-level path-collision check below guards the generated tree.
    # This guards conversion itself, which the harnesses call directly, so a
    # colliding pair cannot silently reduce to one written definition.
    for fixture in (DUPLICATE_REVIEWER_FIXTURE, DUPLICATE_REVIEWER_BANG_FIXTURE):
        write_agent_source(
            tmp_path,
            PLUGIN_NAME,
            Path(fixture).stem,
            agent_conversion_fixture(fixture),
        )

    with pytest.raises(AgentConversionError):
        convert_agents(tmp_path / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME)


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
    for target in Target:
        capability = agent_capability(target)
        if capability.namespaced:
            continue
        tree = repository_agents.dist_root / target.value
        artifacts = sorted(
            path
            for path in tree.glob(
                f"*/{SKILLS_SUBDIR_NAME}/*/{AGENTS_SUBDIR_NAME}/*{capability.suffix}"
            )
        )
        assert artifacts, f"{target.value} carries no converted agent artifacts"
        for plugin_dir in sorted(
            {source_path.parents[1] for source_path in repository_agents.sources}
        ):
            plugin = plugin_dir.name
            expected_stems = {
                FLAT_AGENT_PLUGIN_SEPARATOR.join((plugin, source_path.stem))
                for source_path in repository_agents.sources
                if source_path.parents[1] == plugin_dir
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
    for target in Target:
        capability = agent_capability(target)
        if capability.manifest_declares_agents:
            continue
        tree = repository_agents.dist_root / target.value
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
            declared_skills = manifest[SKILLS_SUBDIR_NAME]
            assert isinstance(declared_skills, str)
            plugin_root = manifest_path.parent.parent
            assert (plugin_root / declared_skills).resolve() == (
                plugin_root / SKILLS_SUBDIR_NAME
            ).resolve()
            assert "agents" not in manifest, (
                f"{manifest_path} declares an agents field this target's manifest "
                "schema does not carry"
            )
