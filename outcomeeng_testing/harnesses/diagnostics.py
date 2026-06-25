"""Harness for the diagnostics node tests.

The diagnostics node's conformance test reads the authored and shipped diagnose
manifest to verify the build rendered the spx version floor into the contract
passed to ``spx diagnose``. The repository-root constant and the dist reader
live here because shared test scaffolding is production code outside ``tests/``
and outside ``spx/``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from outcomeeng.distribution.contracts import Target
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader

# ``parents[2]`` reaches the repository root from
# ``outcomeeng_testing/harnesses/diagnostics.py`` (harnesses ->
# outcomeeng_testing -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]

# The plugin and skill the diagnostics node ships.
SPEC_TREE_PLUGIN = "spec-tree"
DIAGNOSE_SKILL = "diagnose"
DIAGNOSE_MANIFEST = "manifest.json"

# The diagnose manifest's fixed contract fields. The expected plugin set is
# derived from the marketplace manifest so the test tracks the offered plugins.
EXPECTED_DIAGNOSE_CHECKS = (
    "session-environment",
    "spx-reachability",
    "worktree-pool",
    "session-store",
    "marketplace-install",
)
EXPECTED_MARKETPLACE = {"name": "outcomeeng", "source": "outcomeeng/plugins"}

# The authored ``diagnose`` files the build renders into ``dist/``.
AUTHORED_DIAGNOSE_SKILL = (
    REPO_ROOT
    / "src"
    / "plugins"
    / SPEC_TREE_PLUGIN
    / "skills"
    / DIAGNOSE_SKILL
    / "SKILL.md"
)
AUTHORED_DIAGNOSE_MANIFEST = AUTHORED_DIAGNOSE_SKILL.with_name(DIAGNOSE_MANIFEST)
MARKETPLACE_MANIFEST = REPO_ROOT / ".claude-plugin" / "marketplace.json"

# The build template token the authored manifest uses to source the spx version
# floor; the build's render pass replaces it with the source-of-truth value.
SPX_FLOOR_TOKEN = "{{! spx_floor !}}"


def authored_diagnose_manifest() -> dict[str, object]:
    """Return the authored diagnose manifest."""
    return _read_json_object(AUTHORED_DIAGNOSE_MANIFEST)


def authored_diagnose_text() -> str:
    """Return the authored ``diagnose`` skill body."""
    return AUTHORED_DIAGNOSE_SKILL.read_text(encoding="utf-8")


def expected_plugin_names() -> tuple[str, ...]:
    """Return the marketplace's offered plugin names in stable order."""
    manifest = _read_json_object(MARKETPLACE_MANIFEST)
    plugins = manifest["plugins"]
    if not isinstance(plugins, list):
        msg = "marketplace manifest field 'plugins' must be a list"
        raise TypeError(msg)

    names: list[str] = []
    for plugin in plugins:
        if not isinstance(plugin, dict):
            msg = "marketplace manifest plugins must be objects"
            raise TypeError(msg)
        name = plugin.get("name")
        if not isinstance(name, str) or not name:
            msg = "marketplace manifest plugin name must be a non-empty string"
            raise TypeError(msg)
        names.append(name)
    return tuple(sorted(names))


def read_shipped_diagnose_manifest(target: Target) -> dict[str, object]:
    """Return the shipped diagnose manifest for one distribution target."""
    manifest_path = (
        shipped_dist_reader().target_root(target)
        / SPEC_TREE_PLUGIN
        / "skills"
        / DIAGNOSE_SKILL
        / DIAGNOSE_MANIFEST
    )
    return _read_json_object(manifest_path)


def shipped_dist_reader() -> DistTreeReader:
    """Return a reader over the committed ``dist/`` tree at the repository root."""
    return DistTreeReader(REPO_ROOT)


def _read_json_object(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = f"{path} must contain a JSON object"
        raise TypeError(msg)
    return cast(dict[str, object], data)
