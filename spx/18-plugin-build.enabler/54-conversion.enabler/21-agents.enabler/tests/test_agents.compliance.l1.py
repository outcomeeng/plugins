"""Compliance evidence for converted Codex agent boundaries."""

from __future__ import annotations

import json
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest

from outcomeeng.distribution.agents import (
    CODEX_AGENT_ENV_SEPARATOR,
    CODEX_AGENT_ENV_VAR,
    AgentConversionError,
    agent_environment_marker,
    convert_agents,
    iter_agent_files,
    parse_agent_markdown,
)
from outcomeeng.distribution.build import (
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
    PLUGIN_NAME,
    agent_conversion_fixture,
    toml_string,
    toml_table,
)
from outcomeeng_testing.harnesses.distribution import REPOSITORY_ROOT
from outcomeeng_testing.harnesses.src_tree import write_agent_source


def test_environment_marker_is_namespaced_by_source_plugin(tmp_path: Path) -> None:
    source_root = REPOSITORY_ROOT / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME
    sources = iter_agent_files(source_root)
    dist_root = tmp_path / DIST_DIR_NAME
    build(REPOSITORY_ROOT / SOURCE_ROOT_NAME, dist_root)
    capability = agent_capability(Target.CODEX)

    assert sources
    for source_path in sources:
        plugin = source_path.parents[1].name
        generated_type = agent_slug(
            plugin,
            source_path.stem,
            capability=capability,
        )
        artifact = (
            dist_root
            / Target.CODEX.value
            / plugin
            / SKILLS_SUBDIR_NAME
            / f"{plugin}-plugin"
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

    with pytest.raises(AgentConversionError) as raised:
        agent_environment_marker(source)

    assert "agent source path must be under <plugin>/agents" in str(raised.value)


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

    with pytest.raises(AgentConversionError) as raised:
        convert_agents(tmp_path / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME)

    assert "multiple source agents convert to" in str(raised.value)


def test_two_sources_claiming_one_output_fail_before_the_build_writes(
    tmp_path: Path,
) -> None:
    src_root = tmp_path / "src"
    plugin = src_root / "plugins" / "sample"
    # An authored skill directory that collides with the per-plugin lifecycle
    # skill the template renders into this same plugin.
    for skill in ("s1", "sample-plugin"):
        (plugin / "skills" / skill).mkdir(parents=True)
        (plugin / "skills" / skill / "SKILL.md").write_text(
            "---\nname: x\ndescription: d\n---\nbody\n", encoding="utf-8"
        )
    template = src_root / "templates" / "plugin"
    template.mkdir(parents=True)
    (template / "SKILL.md").write_text(
        "---\nname: t\ndescription: d\n---\nbody\n", encoding="utf-8"
    )

    dist_root = tmp_path / "dist"
    with pytest.raises(SourceFormatError) as raised:
        build(src_root, dist_root)
    assert "same output" in str(raised.value)
    # The plan fails before any target tree is written.
    assert not dist_root.exists() or not sorted(dist_root.rglob("SKILL.md"))


def test_flat_namespace_agents_carry_the_plugin_slug_prefix(tmp_path: Path) -> None:
    dist_root = tmp_path / DIST_DIR_NAME
    build(REPOSITORY_ROOT / SOURCE_ROOT_NAME, dist_root)
    source_plugins = REPOSITORY_ROOT / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME
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
        for plugin_dir in sorted(source_plugins.iterdir()):
            source_agents = plugin_dir / AGENTS_SUBDIR_NAME
            if not source_agents.is_dir():
                continue
            plugin = plugin_dir.name
            # Hand-authored separators keep this oracle independent of the
            # production constants agent_slug reads.
            expected_stems = {
                source.stem
                if source.stem.startswith(f"{plugin}-")
                else f"{plugin}_{source.stem}"
                for source in source_agents.glob("*.md")
            }
            actual = {
                path.stem
                for path in artifacts
                if path.relative_to(tree).parts[0] == plugin
            }

            assert actual == expected_stems
        for path in artifacts:
            declared = tomllib.loads(path.read_text(encoding="utf-8"))["name"]
            assert declared == path.stem, (
                f"{path} declares name {declared!r}, which is not its filename stem"
            )


def test_converted_agents_ship_inside_a_manifest_declared_surface(
    tmp_path: Path,
) -> None:
    dist_root = tmp_path / DIST_DIR_NAME
    build(REPOSITORY_ROOT / SOURCE_ROOT_NAME, dist_root)
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
