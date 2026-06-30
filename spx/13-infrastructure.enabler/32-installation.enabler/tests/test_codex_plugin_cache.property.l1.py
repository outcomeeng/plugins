"""Level 1 property evidence for Codex cache refresh convergence."""

from __future__ import annotations

from dataclasses import dataclass, field

from hypothesis import given, settings

from outcomeeng.distribution import codex_cache as preserve_codex_plugin_cache
from outcomeeng.distribution.marketplace_sources import DEFAULT_MARKETPLACE
from outcomeeng_testing.generators.codex_cache import (
    StaleAfterSuccessfulRefresh,
    stale_after_successful_refreshes,
)
from outcomeeng_testing.harnesses.codex_cache import (
    MaterializingAddRunner,
    codex_cache_workspace,
    write_dist_codex_manifest,
    write_plugin_root,
)


@dataclass(frozen=True)
class StaticHistory:
    plugins: frozenset[str]
    versions_by_plugin: dict[str, frozenset[str]]
    current_by_plugin: dict[str, str]

    def working_tree_plugins(self) -> frozenset[str]:
        return self.plugins

    def published_versions(self, plugin: str) -> frozenset[str]:
        return self.versions_by_plugin.get(plugin, frozenset())

    def current_version(self, plugin: str) -> str | None:
        return self.current_by_plugin.get(plugin)


@dataclass
class StaleAfterAddInstalled:
    plugin: str
    version: str
    calls: list[str] = field(default_factory=list)

    def installed_plugin_versions(self, marketplace: str) -> dict[str, str]:
        self.calls.append(marketplace)
        return {self.plugin: self.version}


@settings(max_examples=40)
@given(refresh=stale_after_successful_refreshes())
def test_successful_refresh_reconciles_to_generated_codex_manifest_version(
    refresh: StaleAfterSuccessfulRefresh,
) -> None:
    with codex_cache_workspace() as workspace:
        write_dist_codex_manifest(
            workspace.repo_root,
            refresh.plugin,
            refresh.desired_version,
        )
        write_plugin_root(
            workspace.cache_root,
            refresh.plugin,
            refresh.stale_version,
            "stale content",
        )
        plugin_dir = workspace.cache_root / DEFAULT_MARKETPLACE / refresh.plugin
        stale_dir = plugin_dir / refresh.stale_version
        desired_dir = plugin_dir / refresh.desired_version
        history = StaticHistory(
            plugins=frozenset([refresh.plugin]),
            versions_by_plugin={
                refresh.plugin: frozenset(
                    [refresh.stale_version, refresh.desired_version]
                ),
            },
            current_by_plugin={refresh.plugin: refresh.stale_version},
        )
        installed = StaleAfterAddInstalled(
            plugin=refresh.plugin,
            version=refresh.stale_version,
        )
        runner = MaterializingAddRunner.from_dist_manifests(
            cache_root=workspace.cache_root,
            repo_root=workspace.repo_root,
        )

        result = preserve_codex_plugin_cache.refresh_installed_plugins(
            DEFAULT_MARKETPLACE,
            repo_root=workspace.repo_root,
            cache_root=workspace.cache_root,
            history=history,
            installed=installed,
            runner=runner,
        )

        assert runner.calls == [
            (
                *preserve_codex_plugin_cache.CODEX_PLUGIN_ADD_COMMAND,
                f"{refresh.plugin}@{DEFAULT_MARKETPLACE}",
            )
        ]
        assert installed.calls == [DEFAULT_MARKETPLACE, DEFAULT_MARKETPLACE]
        assert result.refresh_returncode == 0
        assert desired_dir.is_dir() and not desired_dir.is_symlink(), (
            f"expected {desired_dir} to remain the real current directory"
        )
        assert stale_dir.is_symlink(), (
            f"expected {stale_dir} to become a compatibility symlink"
        )
        assert stale_dir.resolve() == desired_dir.resolve(), (
            f"expected {stale_dir} to point at {desired_dir}"
        )
        real_versions = sorted(
            path.name
            for path in plugin_dir.iterdir()
            if path.is_dir() and not path.is_symlink()
        )
        assert real_versions == [refresh.desired_version]


@settings(max_examples=40)
@given(refresh=stale_after_successful_refreshes())
def test_successful_refresh_preserves_absent_stale_codex_reported_version(
    refresh: StaleAfterSuccessfulRefresh,
) -> None:
    with codex_cache_workspace() as workspace:
        write_dist_codex_manifest(
            workspace.repo_root,
            refresh.plugin,
            refresh.desired_version,
        )
        history = StaticHistory(
            plugins=frozenset([refresh.plugin]),
            versions_by_plugin={refresh.plugin: frozenset([refresh.desired_version])},
            current_by_plugin={refresh.plugin: refresh.desired_version},
        )
        installed = StaleAfterAddInstalled(
            plugin=refresh.plugin,
            version=refresh.stale_version,
        )
        runner = MaterializingAddRunner.from_dist_manifests(
            cache_root=workspace.cache_root,
            repo_root=workspace.repo_root,
        )

        result = preserve_codex_plugin_cache.refresh_installed_plugins(
            DEFAULT_MARKETPLACE,
            repo_root=workspace.repo_root,
            cache_root=workspace.cache_root,
            history=history,
            installed=installed,
            runner=runner,
        )

        plugin_dir = workspace.cache_root / DEFAULT_MARKETPLACE / refresh.plugin
        stale_dir = plugin_dir / refresh.stale_version
        desired_dir = plugin_dir / refresh.desired_version
        assert result.refresh_returncode == 0
        assert desired_dir.is_dir() and not desired_dir.is_symlink(), (
            f"expected {desired_dir} to remain the real current directory"
        )
        assert stale_dir.is_symlink(), (
            f"expected absent stale report {stale_dir} to be recreated"
        )
        assert stale_dir.resolve() == desired_dir.resolve(), (
            f"expected {stale_dir} to point at {desired_dir}"
        )
