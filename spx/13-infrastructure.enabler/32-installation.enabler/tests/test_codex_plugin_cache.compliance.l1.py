"""Level 1 compliance tests for Codex cache refresh commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from outcomeeng.distribution import codex_cache
from outcomeeng.distribution.marketplace_sources import DEFAULT_MARKETPLACE
from outcomeeng_testing.harnesses.codex_cache import (
    MaterializingAddRunner,
    write_dist_codex_manifest,
)


@dataclass(frozen=True)
class StaticHistory:
    """Interaction-protocol stub for plugin history in a synthetic repository."""

    plugins: frozenset[str]
    versions_by_plugin: dict[str, frozenset[str]]
    current_by_plugin: dict[str, str]

    def working_tree_plugins(self) -> frozenset[str]:
        return self.plugins

    def published_versions(self, plugin: str) -> frozenset[str]:
        return self.versions_by_plugin.get(plugin, frozenset())

    def current_version(self, plugin: str) -> str | None:
        return self.current_by_plugin.get(plugin)


@dataclass(frozen=True)
class StaticInstalled:
    """Interaction-protocol stub for the Codex installed-version provider."""

    versions: dict[str, str]

    def installed_plugin_versions(self, marketplace: str) -> dict[str, str]:
        return self.versions


def test_local_refresh_never_invokes_marketplace_upgrade(tmp_path: Path) -> None:
    """Maintainer refresh reinstalls generated plugins one at a time."""
    repo_root = tmp_path / "repo"
    cache_root = tmp_path / "cache"
    plugin_name = "spec-tree"
    version = "0.1.0"
    write_dist_codex_manifest(repo_root, plugin_name, version)
    history = StaticHistory(
        plugins=frozenset([plugin_name]),
        versions_by_plugin={plugin_name: frozenset([version])},
        current_by_plugin={plugin_name: version},
    )
    runner = MaterializingAddRunner(
        cache_root=cache_root,
        versions={plugin_name: version},
    )

    result = codex_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({plugin_name: version}),
        runner=runner,
    )

    assert runner.calls == [
        (*codex_cache.CODEX_PLUGIN_ADD_COMMAND, f"{plugin_name}@{DEFAULT_MARKETPLACE}")
    ]
    assert all(
        command[:3] != ("codex", "plugin", "marketplace") for command in runner.calls
    )
    assert result.refresh_returncode == 0
