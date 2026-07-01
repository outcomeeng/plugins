"""Level 1 compliance tests for Codex cache refresh commands."""

from __future__ import annotations

from pathlib import Path

from outcomeeng.distribution import codex_cache
from outcomeeng.distribution.marketplace_sources import DEFAULT_MARKETPLACE
from outcomeeng_testing.harnesses.codex_cache import (
    MaterializingAddRunner,
    StaticHistory,
    StaticInstalled,
    write_dist_codex_manifest,
)


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
