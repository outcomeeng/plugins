"""Mapping evidence for canonical Codex marketplace agent identities."""

from __future__ import annotations

import tomllib
from pathlib import Path

from outcomeeng.distribution.build import (
    agent_capability,
    agent_slug,
    build,
)
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    DIST_DIR_NAME,
    PLUGINS_DIR_NAME,
    SKILLS_SUBDIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
)
from outcomeeng_testing.harnesses.distribution import REPOSITORY_ROOT


def test_flat_namespace_agent_identity_contains_plugin_exactly_once(
    tmp_path: Path,
) -> None:
    source_plugins = REPOSITORY_ROOT / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME
    sources = tuple(sorted(source_plugins.glob(f"*/{AGENTS_SUBDIR_NAME}/*.md")))
    assert sources
    dist_root = tmp_path / DIST_DIR_NAME
    build(REPOSITORY_ROOT / SOURCE_ROOT_NAME, dist_root)

    for target in Target:
        capability = agent_capability(target)
        if capability.namespaced:
            continue
        target_tree = dist_root / target.value
        for source in sources:
            plugin = source.parents[1].name
            stem = source.stem
            # Hand-authored separators keep this oracle independent of the
            # production constants agent_slug reads.
            expected = stem if stem.startswith(f"{plugin}-") else f"{plugin}_{stem}"

            slug = agent_slug(plugin, stem, capability=capability)
            assert slug == expected
            assert slug.count(plugin) == 1
            assert slug.endswith(stem)
            artifact = (
                target_tree
                / plugin
                / SKILLS_SUBDIR_NAME
                / f"{plugin}-plugin"
                / AGENTS_SUBDIR_NAME
                / f"{expected}{capability.suffix}"
            )
            assert artifact.exists(), f"missing canonical agent artifact {artifact}"
            parsed = tomllib.loads(artifact.read_text(encoding="utf-8"))
            assert parsed["name"] == expected
