"""Compliance evidence for converted Codex agent boundaries."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from outcomeeng.distribution.build import (
    SourceFormatError,
    agent_capability,
    build,
)
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    CODEX_PLUGIN_SUBDIR_NAME,
    DIST_DIR_NAME,
    SKILLS_SUBDIR_NAME,
    Target,
)
from outcomeeng_testing.harnesses.distribution import REPOSITORY_ROOT


from outcomeeng_testing.harnesses.agent_conversion import (
    assert_environment_marker_is_namespaced_by_source_plugin,
    assert_environment_marker_without_source_plugin_is_rejected,
    assert_generated_toml_stays_outside_codex_plugin_manifest_content,
    assert_manual_guidance_preserves_source_only_fields,
    converting_sources_that_slugify_alike,
)


def test_manual_guidance_preserves_source_only_fields() -> None:
    assert_manual_guidance_preserves_source_only_fields()


def test_generated_toml_stays_outside_codex_plugin_manifest_content() -> None:
    assert_generated_toml_stays_outside_codex_plugin_manifest_content()


def test_environment_marker_is_namespaced_by_source_plugin() -> None:
    assert_environment_marker_is_namespaced_by_source_plugin()


def test_environment_marker_without_source_plugin_is_rejected() -> None:
    assert_environment_marker_without_source_plugin_is_rejected()


def test_two_sources_converting_to_one_filename_fail(tmp_path: Path) -> None:
    # The build-level path-collision check below guards the generated tree.
    # This guards conversion itself, which the harnesses call directly, so a
    # colliding pair cannot silently reduce to one written definition.
    collision = converting_sources_that_slugify_alike(tmp_path)

    assert collision.error is not None, (
        "conversion returned instead of failing, so the pair reduced to the "
        f"filenames {collision.filenames}, dropping a definition"
    )
    assert "multiple source agents convert to" in collision.error, (
        f"conversion failed for an unrelated reason: {collision.error}"
    )
    assert not collision.filenames, (
        f"a failed conversion still reported converted filenames: {collision.filenames}"
    )


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


def _run_placement(checkout: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    """Run the shipped placement script exactly as a consumer invokes it."""
    script = (
        REPOSITORY_ROOT
        / DIST_DIR_NAME
        / "codex"
        / "spec-tree"
        / SKILLS_SUBDIR_NAME
        / "spec-tree-plugin"
        / "scripts"
        / "place_agents.py"
    )
    return subprocess.run(
        [sys.executable, str(script), "--checkout", str(checkout), *extra],
        capture_output=True,
        text=True,
        check=False,
    )


def test_placement_leaves_every_file_outside_its_namespace_untouched(
    tmp_path: Path,
) -> None:
    agents_dir = tmp_path / ".codex" / "agents"
    agents_dir.mkdir(parents=True)
    developer_owned = agents_dir / "my-own-agent.toml"
    other_plugin = agents_dir / "otherplugin_helper.toml"
    developer_owned.write_text('name = "my-own-agent"\n', encoding="utf-8")
    # Content identical to what this plugin generates must still be left alone:
    # matching content is not ownership.
    shipped = sorted(
        (
            REPOSITORY_ROOT
            / DIST_DIR_NAME
            / "codex"
            / "spec-tree"
            / SKILLS_SUBDIR_NAME
            / "spec-tree-plugin"
            / AGENTS_SUBDIR_NAME
        ).glob("spec-tree_*.toml")
    )
    assert shipped
    other_plugin.write_text(shipped[0].read_text(encoding="utf-8"), encoding="utf-8")

    result = _run_placement(tmp_path)
    assert result.returncode == 0, result.stderr

    assert developer_owned.read_text(encoding="utf-8") == 'name = "my-own-agent"\n'
    assert other_plugin.exists(), "another plugin's definition was pruned"
    placed = sorted(agents_dir.glob("spec-tree_*.toml"))
    assert len(placed) == len(shipped)


def test_placement_prunes_only_retired_definitions_in_its_namespace(
    tmp_path: Path,
) -> None:
    agents_dir = tmp_path / ".codex" / "agents"
    agents_dir.mkdir(parents=True)
    retired = agents_dir / "spec-tree_retired-auditor.toml"
    retired.write_text('name = "spec-tree_retired-auditor"\n', encoding="utf-8")
    foreign_retired = agents_dir / "otherplugin_retired.toml"
    foreign_retired.write_text('name = "otherplugin_retired"\n', encoding="utf-8")

    assert _run_placement(tmp_path).returncode == 0
    assert not retired.exists(), "a retired definition in this namespace survived"
    assert foreign_retired.exists(), "pruning reached outside this plugin's namespace"


def test_placement_check_reports_drift_and_writes_nothing(tmp_path: Path) -> None:
    agents_dir = tmp_path / ".codex" / "agents"
    agents_dir.mkdir(parents=True)

    drifted = _run_placement(tmp_path, "--check")
    assert drifted.returncode == 1, "check passed against an empty agent directory"
    assert "drift" in drifted.stdout
    assert not sorted(agents_dir.glob("*.toml")), "check wrote files"

    assert _run_placement(tmp_path).returncode == 0
    assert _run_placement(tmp_path, "--check").returncode == 0
