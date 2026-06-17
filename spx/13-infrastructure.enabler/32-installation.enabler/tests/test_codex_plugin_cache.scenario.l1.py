"""Level 1 installation scenarios for chain-recovery cache preservation.

Each scenario corresponds to one assertion in
``spx/13-infrastructure.enabler/32-installation.enabler/installation.md``.

The direct preservation scenarios take a ``PluginHistory`` provider that names the
working-tree plugin set and per-plugin published versions in the window. They
inject a ``StaticHistory`` implementation (Stage 5 exception 2 -- interaction
protocol DI) in place of the production git-history walker mandated by
``21-codex-cache-preservation.adr.md``. CLI-surface scenarios that verify
``main()`` output call ``main()`` directly with the production ``GitPluginHistory``
against a synthetic non-git repository.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from outcomeeng.distribution import codex_cache as preserve_codex_plugin_cache
from outcomeeng.distribution.marketplace_sources import (
    CODEX_PLUGIN_MANIFEST,
    DEFAULT_MARKETPLACE,
    DIST_CODEX_PLUGINS_DIR,
)

PLUGIN_NAME = "spec-tree"
ORPHAN_PLUGIN_NAME = "removed-plugin"
UNINSTALLED_PLUGIN_NAME = "uninstalled-plugin"
OLDER_VERSION = "0.26.5"
CURRENT_VERSION = "0.26.6"
NEW_CURRENT_VERSION = "0.26.7"

# Faithful to the captured broken state: a working-tree plugin whose only cache
# entry is a stale real version directory while its current version was never
# materialized and Codex does not report it as installed.
NOT_INSTALLED_PLUGIN = "python"
NOT_INSTALLED_STALE_VERSION = "0.18.6"
NOT_INSTALLED_CURRENT_VERSION = "0.18.8"


@dataclass(frozen=True)
class StaticHistory:
    """Explicit interaction-protocol stub for the plugin-history provider.

    Maps to Stage 5 exception 2 in ``/testing``: tests cannot drive a real git
    walker against a synthetic working tree at l1, so the dependency is injected
    as a typed Protocol with deterministic return values for the working-tree
    plugin set, each plugin's published-in-window versions, and each plugin's
    current working-tree manifest version.
    """

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
    """Interaction-protocol stub for the Codex installed-version provider.

    Stage 5 exception 2 (interaction-protocol DI): the real provider queries the
    `codex` binary, which is absent at l1, so the installed set is injected as a
    typed Protocol returning deterministic plugin-name to version data.
    """

    versions: dict[str, str]

    def installed_plugin_versions(self, marketplace: str) -> dict[str, str]:
        return self.versions


@dataclass
class SequencedInstalled:
    """Installed-version provider whose response changes after refresh.

    Stage 5 exception 2 (interaction-protocol DI): the real Codex provider is
    queried before and after `codex plugin add`. This spy returns deterministic
    versions for each query so the test can prove reconciliation uses the
    post-refresh installed set.
    """

    versions_by_call: tuple[dict[str, str], ...]
    calls: list[str] = field(default_factory=list)

    def installed_plugin_versions(self, marketplace: str) -> dict[str, str]:
        self.calls.append(marketplace)
        index = min(len(self.calls) - 1, len(self.versions_by_call) - 1)
        return self.versions_by_call[index]


@dataclass(frozen=True)
class RaisingInstalled:
    """Stub that fails the installed-set query (Stage 5 exception 1 -- failure
    simulation), proving preservation aborts before mutating the cache."""

    def installed_plugin_versions(self, marketplace: str) -> dict[str, str]:
        raise preserve_codex_plugin_cache.InstalledSetError(
            "installed-set query failed"
        )


@dataclass
class MaterializingAddRunner:
    """Runner stub that materializes cache roots for local Codex plugin adds.

    Stage 5 exception 2 (interaction-protocol DI): the production path invokes
    `codex plugin add <plugin>@<marketplace>` and observes Codex's filesystem
    side effect. The l1 test records the command sequence and materializes the
    same side effect deterministically.
    """

    cache_root: Path
    versions: dict[str, str]
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        command_tuple = tuple(command)
        self.calls.append(command_tuple)
        add_prefix = preserve_codex_plugin_cache.CODEX_PLUGIN_ADD_COMMAND
        if command_tuple[: len(add_prefix)] == add_prefix:
            plugin_ref = command_tuple[len(add_prefix)]
            plugin, separator, marketplace = plugin_ref.partition("@")
            if separator != "@" or marketplace != DEFAULT_MARKETPLACE:
                return subprocess.CompletedProcess(command, 64)
            _write_skill(
                self.cache_root,
                plugin,
                self.versions[plugin],
                f"{plugin} materialized content",
            )
        return subprocess.CompletedProcess(command, 0)


def _skill_file(cache_root: Path, plugin: str, version: str) -> Path:
    return (
        cache_root
        / DEFAULT_MARKETPLACE
        / plugin
        / version
        / "skills"
        / "contextualizing"
        / "SKILL.md"
    )


def _write_skill(cache_root: Path, plugin: str, version: str, text: str) -> None:
    skill_file = _skill_file(cache_root, plugin, version)
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text(text)
    manifest = (
        cache_root / DEFAULT_MARKETPLACE / plugin / version / CODEX_PLUGIN_MANIFEST
    )
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": plugin, "version": version}))


def _write_partial_hook_root(cache_root: Path, plugin: str, version: str) -> None:
    hook_script = (
        cache_root / DEFAULT_MARKETPLACE / plugin / version / "scripts" / "load-gate.py"
    )
    hook_script.parent.mkdir(parents=True)
    hook_script.write_text("print('partial hook root')\n")


def _write_manifest(repo_root: Path, plugin: str, version: str) -> None:
    manifest = repo_root / "src" / "plugins" / plugin / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": plugin, "version": version}))


def _write_dist_codex_manifest(repo_root: Path, plugin: str, version: str) -> None:
    manifest = repo_root / DIST_CODEX_PLUGINS_DIR / plugin / CODEX_PLUGIN_MANIFEST
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": plugin, "version": version}))


def _repo_with_dist_codex_plugin(tmp_path: Path, plugin: str, version: str) -> Path:
    repo_root = tmp_path / "repo"
    _write_dist_codex_manifest(repo_root, plugin, version)
    return repo_root


def _quiet_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 0)


def test_local_refresh_reinstalls_installed_dist_plugins_without_upgrade(
    tmp_path: Path,
) -> None:
    """Local refresh discovers addable plugins from `dist/codex`, intersects that
    with the Codex installed set, refreshes those plugins in deterministic manifest
    order, and never invokes the marketplace upgrade path that removes older cache
    directories.
    """
    repo_root = tmp_path / "repo"
    cache_root = tmp_path / "cache"
    _write_dist_codex_manifest(repo_root, "zeta", "0.2.0")
    _write_dist_codex_manifest(repo_root, "alpha", "0.1.0")
    history = StaticHistory(
        plugins=frozenset(["alpha", "zeta"]),
        versions_by_plugin={
            "alpha": frozenset(["0.1.0"]),
            "zeta": frozenset(["0.2.0"]),
        },
        current_by_plugin={"alpha": "0.1.0", "zeta": "0.2.0"},
    )
    runner = MaterializingAddRunner(
        cache_root=cache_root,
        versions={"alpha": "0.1.0", "zeta": "0.2.0"},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({"zeta": "0.2.0", "alpha": "0.1.0"}),
        runner=runner,
    )

    assert runner.calls == [
        (*preserve_codex_plugin_cache.CODEX_PLUGIN_ADD_COMMAND, "alpha@outcomeeng"),
        (*preserve_codex_plugin_cache.CODEX_PLUGIN_ADD_COMMAND, "zeta@outcomeeng"),
    ]
    assert all("upgrade" not in call for call in runner.calls)
    assert result.refresh_returncode == 0
    assert _skill_file(cache_root, "alpha", "0.1.0").is_file()
    assert _skill_file(cache_root, "zeta", "0.2.0").is_file()


def test_local_refresh_requeries_installed_versions_before_reconciliation(
    tmp_path: Path,
) -> None:
    """A successful local plugin add can move the installed version forward; cache
    reconciliation uses the post-refresh installed set so the new version remains
    the sole real directory.
    """
    repo_root = tmp_path / "repo"
    cache_root = tmp_path / "cache"
    _write_dist_codex_manifest(repo_root, PLUGIN_NAME, NEW_CURRENT_VERSION)
    _write_skill(cache_root, PLUGIN_NAME, CURRENT_VERSION, "prior content")
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME
    prior_dir = plugin_dir / CURRENT_VERSION
    current_dir = plugin_dir / NEW_CURRENT_VERSION
    history = StaticHistory(
        plugins=frozenset([PLUGIN_NAME]),
        versions_by_plugin={
            PLUGIN_NAME: frozenset([CURRENT_VERSION, NEW_CURRENT_VERSION]),
        },
        current_by_plugin={PLUGIN_NAME: NEW_CURRENT_VERSION},
    )
    installed = SequencedInstalled(
        (
            {PLUGIN_NAME: CURRENT_VERSION},
            {PLUGIN_NAME: NEW_CURRENT_VERSION},
        )
    )
    runner = MaterializingAddRunner(
        cache_root=cache_root,
        versions={PLUGIN_NAME: NEW_CURRENT_VERSION},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=installed,
        runner=runner,
    )

    assert installed.calls == [DEFAULT_MARKETPLACE, DEFAULT_MARKETPLACE], (
        "expected installed versions to be queried before and after refresh; "
        f"got {installed.calls}"
    )
    assert result.refresh_returncode == 0
    assert current_dir.is_dir() and not current_dir.is_symlink(), (
        f"expected {current_dir} to remain the real current directory"
    )
    assert prior_dir.is_symlink(), (
        f"expected {prior_dir} to become a compatibility symlink"
    )
    assert prior_dir.resolve() == current_dir.resolve(), (
        f"expected {prior_dir} to point at {current_dir}"
    )


def test_chain_recovery_restores_in_window_published_version_as_symlink(
    tmp_path: Path,
) -> None:
    """Two published versions in the window, cache contains only the latest version
    directory. After preservation, the older published version path is a symlink
    pointing at the current version directory.
    """
    repo_root = _repo_with_dist_codex_plugin(tmp_path, PLUGIN_NAME, CURRENT_VERSION)
    cache_root = tmp_path / "cache"
    _write_skill(cache_root, PLUGIN_NAME, CURRENT_VERSION, "current content")
    older_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME / OLDER_VERSION
    current_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME / CURRENT_VERSION
    history = StaticHistory(
        plugins=frozenset([PLUGIN_NAME]),
        versions_by_plugin={
            PLUGIN_NAME: frozenset([OLDER_VERSION, CURRENT_VERSION]),
        },
        current_by_plugin={PLUGIN_NAME: CURRENT_VERSION},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({PLUGIN_NAME: CURRENT_VERSION}),
        runner=_quiet_runner,
    )

    assert older_dir.is_symlink(), (
        f"expected {older_dir} to be a symlink after chain recovery"
    )
    assert older_dir.resolve() == current_dir, (
        f"expected {older_dir} to resolve to {current_dir}, got {older_dir.resolve()}"
    )
    assert older_dir in result.linked_versions, (
        f"expected {older_dir} in result.linked_versions={result.linked_versions}"
    )


def test_stale_worktree_target_and_partial_root_replaced_by_codex_target(
    tmp_path: Path,
) -> None:
    """Reproduces the active-session failure mode: the worktree manifest still says
    `CURRENT_VERSION`, Codex reports `NEW_CURRENT_VERSION`, and a manual recovery
    left `CURRENT_VERSION` as a partial real plugin root while an older
    compatibility path points at it. Preservation rewrites both in-window paths as
    direct symlinks to the complete Codex-reported version, leaving exactly one real
    directory for the plugin.
    """
    repo_root = _repo_with_dist_codex_plugin(tmp_path, PLUGIN_NAME, NEW_CURRENT_VERSION)
    cache_root = tmp_path / "cache"
    _write_skill(cache_root, PLUGIN_NAME, NEW_CURRENT_VERSION, "codex content")
    _write_partial_hook_root(cache_root, PLUGIN_NAME, CURRENT_VERSION)
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME
    installed_dir = plugin_dir / NEW_CURRENT_VERSION
    stale_worktree_path = plugin_dir / CURRENT_VERSION
    older_link = plugin_dir / OLDER_VERSION
    older_link.symlink_to(CURRENT_VERSION, target_is_directory=True)
    history = StaticHistory(
        plugins=frozenset([PLUGIN_NAME]),
        versions_by_plugin={
            PLUGIN_NAME: frozenset(
                [OLDER_VERSION, CURRENT_VERSION, NEW_CURRENT_VERSION]
            ),
        },
        current_by_plugin={PLUGIN_NAME: CURRENT_VERSION},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({PLUGIN_NAME: NEW_CURRENT_VERSION}),
        runner=_quiet_runner,
    )

    assert stale_worktree_path.is_symlink(), (
        f"expected partial root {stale_worktree_path} replaced by a symlink"
    )
    assert stale_worktree_path.resolve() == installed_dir, (
        f"expected {stale_worktree_path} to resolve directly to {installed_dir}"
    )
    assert older_link.is_symlink(), f"expected {older_link} to remain a symlink"
    assert older_link.resolve() == installed_dir, (
        f"expected {older_link} to resolve directly to {installed_dir}"
    )
    real_versions = [
        path.name
        for path in plugin_dir.iterdir()
        if path.is_dir() and not path.is_symlink()
    ]
    assert real_versions == [NEW_CURRENT_VERSION], (
        f"expected exactly one real version directory, got {real_versions}"
    )
    assert stale_worktree_path in result.linked_versions


def test_extra_real_version_directory_replaced_by_direct_symlink(
    tmp_path: Path,
) -> None:
    """When a prior installed version remains as a complete real directory, the
    preservation step converts that in-window path into a direct symlink to the
    Codex-reported installed version so the plugin cache has one real root.
    """
    repo_root = _repo_with_dist_codex_plugin(tmp_path, PLUGIN_NAME, NEW_CURRENT_VERSION)
    cache_root = tmp_path / "cache"
    _write_skill(cache_root, PLUGIN_NAME, CURRENT_VERSION, "stale real content")
    _write_skill(cache_root, PLUGIN_NAME, NEW_CURRENT_VERSION, "codex content")
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME
    stale_real_path = plugin_dir / CURRENT_VERSION
    installed_dir = plugin_dir / NEW_CURRENT_VERSION
    history = StaticHistory(
        plugins=frozenset([PLUGIN_NAME]),
        versions_by_plugin={
            PLUGIN_NAME: frozenset([CURRENT_VERSION, NEW_CURRENT_VERSION]),
        },
        current_by_plugin={PLUGIN_NAME: CURRENT_VERSION},
    )

    preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({PLUGIN_NAME: NEW_CURRENT_VERSION}),
        runner=_quiet_runner,
    )

    assert stale_real_path.is_symlink(), (
        f"expected non-target real directory {stale_real_path} replaced"
    )
    assert stale_real_path.resolve() == installed_dir, (
        f"expected {stale_real_path} to resolve directly to {installed_dir}"
    )
    real_versions = [
        path.name
        for path in plugin_dir.iterdir()
        if path.is_dir() and not path.is_symlink()
    ]
    assert real_versions == [NEW_CURRENT_VERSION], (
        f"expected exactly one real version directory, got {real_versions}"
    )


def test_out_of_window_compatibility_symlink_is_removed(tmp_path: Path) -> None:
    """A compatibility symlink for a version absent from the published window is
    removed during preservation; the current version directory remains real.
    """
    cache_root = tmp_path / "cache"
    _write_skill(cache_root, PLUGIN_NAME, CURRENT_VERSION, "current content")
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME
    older_link = plugin_dir / OLDER_VERSION
    current_dir = plugin_dir / CURRENT_VERSION
    older_link.symlink_to(CURRENT_VERSION, target_is_directory=True)
    history = StaticHistory(
        plugins=frozenset([PLUGIN_NAME]),
        versions_by_plugin={
            PLUGIN_NAME: frozenset([CURRENT_VERSION]),
        },
        current_by_plugin={PLUGIN_NAME: CURRENT_VERSION},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        cache_root=cache_root,
        history=history,
        runner=_quiet_runner,
    )

    assert not os.path.lexists(older_link), (
        f"expected {older_link} to be removed (version outside window)"
    )
    assert current_dir.is_dir() and not current_dir.is_symlink(), (
        f"expected {current_dir} to remain a real directory"
    )
    assert older_link in result.pruned_links, (
        f"expected {older_link} in result.pruned_links={result.pruned_links}"
    )


def test_orphan_plugin_cache_directory_is_pruned(tmp_path: Path) -> None:
    """A plugin directory present in the cache but absent from the working tree has
    its entire cache directory removed during preservation.
    """
    cache_root = tmp_path / "cache"
    _write_skill(cache_root, ORPHAN_PLUGIN_NAME, OLDER_VERSION, "orphan content")
    orphan_dir = cache_root / DEFAULT_MARKETPLACE / ORPHAN_PLUGIN_NAME
    history = StaticHistory(
        plugins=frozenset(),
        versions_by_plugin={},
        current_by_plugin={},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        cache_root=cache_root,
        history=history,
        runner=_quiet_runner,
    )

    assert not orphan_dir.exists(), (
        f"expected {orphan_dir} to be removed (plugin absent from working tree)"
    )
    assert ORPHAN_PLUGIN_NAME in result.pruned_plugins, (
        f"expected {ORPHAN_PLUGIN_NAME} in result.pruned_plugins={result.pruned_plugins}"
    )


def test_uncached_working_tree_plugin_does_not_emit_warning(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A working-tree plugin that is not installed in the local Codex cache is skipped
    silently; cache preservation only has work to do for plugins with cache state."""
    repo_root = tmp_path / "repo"
    cache_root = tmp_path / "cache"
    _write_manifest(repo_root, PLUGIN_NAME, CURRENT_VERSION)
    _write_manifest(repo_root, UNINSTALLED_PLUGIN_NAME, CURRENT_VERSION)
    _write_skill(cache_root, PLUGIN_NAME, CURRENT_VERSION, "current content")

    exit_code = preserve_codex_plugin_cache.main(
        [
            DEFAULT_MARKETPLACE,
            "--cache-root",
            str(cache_root),
            "--repo-root",
            str(repo_root),
            "--dry-run",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    output = f"{captured.out}{captured.err}"
    assert "warning:" not in output


def test_cli_repo_root_still_runs_local_source_preflight(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A non-dry-run CLI invocation with `--repo-root` still verifies the live
    Codex marketplace source before any installed-set query or cache mutation.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    cache_root = tmp_path / "cache"

    def _rejecting_local_root(marketplace: str) -> Path:
        raise preserve_codex_plugin_cache.MarketplaceSourceError(
            f"Codex marketplace `{marketplace}` must be registered as a local source"
        )

    exit_code = preserve_codex_plugin_cache.main(
        [
            DEFAULT_MARKETPLACE,
            "--cache-root",
            str(cache_root),
            "--repo-root",
            str(repo_root),
        ],
        marketplace_root_resolver=_rejecting_local_root,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "must be registered as a local source" in captured.err


def test_upgrade_without_current_real_dir_creates_no_current_symlink(
    tmp_path: Path,
) -> None:
    """A successful upgrade leaves only the older version as a real directory while
    the current working-tree version is in the published window but not materialized
    as a real directory. Preservation creates no compatibility symlink for the
    current version and removes the non-target real directory, so no cache path
    resolves to stale content.
    """
    repo_root = _repo_with_dist_codex_plugin(tmp_path, PLUGIN_NAME, CURRENT_VERSION)
    cache_root = tmp_path / "cache"
    _write_skill(cache_root, PLUGIN_NAME, OLDER_VERSION, "stale content")
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME
    older_dir = plugin_dir / OLDER_VERSION
    current_path = plugin_dir / CURRENT_VERSION
    history = StaticHistory(
        plugins=frozenset([PLUGIN_NAME]),
        versions_by_plugin={
            PLUGIN_NAME: frozenset([OLDER_VERSION, CURRENT_VERSION]),
        },
        current_by_plugin={PLUGIN_NAME: CURRENT_VERSION},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({PLUGIN_NAME: CURRENT_VERSION}),
        runner=_quiet_runner,
    )

    assert not os.path.lexists(current_path), (
        f"expected no cache entry at {current_path}; preservation must not fabricate "
        f"a symlink for the current version pointing at the stale {older_dir}"
    )
    assert result.linked_versions == (), (
        f"expected no compatibility symlinks created, got {result.linked_versions}"
    )
    assert not older_dir.exists(), (
        f"expected non-target real directory {older_dir} removed"
    )
    assert older_dir in result.pruned_links, (
        f"expected removed real directory {older_dir} in "
        f"result.pruned_links={result.pruned_links}"
    )


def test_stale_current_version_symlink_is_removed_when_no_real_dir(
    tmp_path: Path,
) -> None:
    """A prior run left a compatibility symlink at the current version pointing at an
    older real directory, and the current version still has no real directory. The
    next preservation run removes the stale symlink and the non-target real directory
    so the current version resolves to nothing rather than to the older directory's
    content.
    """
    repo_root = _repo_with_dist_codex_plugin(tmp_path, PLUGIN_NAME, CURRENT_VERSION)
    cache_root = tmp_path / "cache"
    _write_skill(cache_root, PLUGIN_NAME, OLDER_VERSION, "stale content")
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME
    older_dir = plugin_dir / OLDER_VERSION
    current_link = plugin_dir / CURRENT_VERSION
    current_link.symlink_to(OLDER_VERSION, target_is_directory=True)
    history = StaticHistory(
        plugins=frozenset([PLUGIN_NAME]),
        versions_by_plugin={
            PLUGIN_NAME: frozenset([OLDER_VERSION, CURRENT_VERSION]),
        },
        current_by_plugin={PLUGIN_NAME: CURRENT_VERSION},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({PLUGIN_NAME: CURRENT_VERSION}),
        runner=_quiet_runner,
    )

    assert not os.path.lexists(current_link), (
        f"expected the stale symlink {current_link} to be removed so the current "
        f"version no longer resolves to {older_dir}"
    )
    assert current_link in result.pruned_links, (
        f"expected {current_link} in result.pruned_links={result.pruned_links}"
    )
    assert not older_dir.exists(), (
        f"expected non-target real directory {older_dir} removed"
    )
    assert older_dir in result.pruned_links, (
        f"expected removed real directory {older_dir} in "
        f"result.pruned_links={result.pruned_links}"
    )


def test_all_compatibility_symlinks_removed_when_current_real_dir_absent(
    tmp_path: Path,
) -> None:
    """A prior run left an older in-window version symlinked to a now-non-current
    real directory, and the new current version has no real directory. The next
    preservation run removes every compatibility symlink and the non-target real
    directory for the plugin so no version resolves to the non-current directory.
    """
    repo_root = _repo_with_dist_codex_plugin(tmp_path, PLUGIN_NAME, NEW_CURRENT_VERSION)
    cache_root = tmp_path / "cache"
    # CURRENT_VERSION is the prior current with a real directory; OLDER_VERSION is an
    # in-window compatibility symlink pointing at it; NEW_CURRENT_VERSION is the new
    # current with no real directory after the upgrade.
    _write_skill(cache_root, PLUGIN_NAME, CURRENT_VERSION, "prior content")
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME
    prior_real_dir = plugin_dir / CURRENT_VERSION
    older_link = plugin_dir / OLDER_VERSION
    older_link.symlink_to(CURRENT_VERSION, target_is_directory=True)
    history = StaticHistory(
        plugins=frozenset([PLUGIN_NAME]),
        versions_by_plugin={
            PLUGIN_NAME: frozenset(
                [OLDER_VERSION, CURRENT_VERSION, NEW_CURRENT_VERSION]
            ),
        },
        current_by_plugin={PLUGIN_NAME: NEW_CURRENT_VERSION},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({PLUGIN_NAME: NEW_CURRENT_VERSION}),
        runner=_quiet_runner,
    )

    assert not os.path.lexists(older_link), (
        f"expected the in-window symlink {older_link} to be removed so it no longer "
        f"resolves to the non-current {prior_real_dir}"
    )
    assert older_link in result.pruned_links, (
        f"expected {older_link} in result.pruned_links={result.pruned_links}"
    )
    assert not prior_real_dir.exists(), (
        f"expected non-target real directory {prior_real_dir} removed"
    )
    assert prior_real_dir in result.pruned_links, (
        f"expected removed real directory {prior_real_dir} in "
        f"result.pruned_links={result.pruned_links}"
    )


def test_multiple_compatibility_symlinks_all_removed_when_current_real_dir_absent(
    tmp_path: Path,
) -> None:
    """Two compatibility symlinks — an older in-window entry and a current-version
    entry, both pointing at the same prior real directory — are all removed in one
    pass when the declared current version has no real directory of its own, and the
    non-target real directory is removed in the same pass.
    """
    repo_root = _repo_with_dist_codex_plugin(tmp_path, PLUGIN_NAME, NEW_CURRENT_VERSION)
    cache_root = tmp_path / "cache"
    _write_skill(cache_root, PLUGIN_NAME, CURRENT_VERSION, "prior content")
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME
    prior_real_dir = plugin_dir / CURRENT_VERSION
    older_link = plugin_dir / OLDER_VERSION
    current_link = plugin_dir / NEW_CURRENT_VERSION
    older_link.symlink_to(CURRENT_VERSION, target_is_directory=True)
    current_link.symlink_to(CURRENT_VERSION, target_is_directory=True)
    history = StaticHistory(
        plugins=frozenset([PLUGIN_NAME]),
        versions_by_plugin={
            PLUGIN_NAME: frozenset(
                [OLDER_VERSION, CURRENT_VERSION, NEW_CURRENT_VERSION]
            ),
        },
        current_by_plugin={PLUGIN_NAME: NEW_CURRENT_VERSION},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({PLUGIN_NAME: NEW_CURRENT_VERSION}),
        runner=_quiet_runner,
    )

    assert not os.path.lexists(older_link) and not os.path.lexists(current_link), (
        f"expected both {older_link} and {current_link} removed, got "
        f"lexists={os.path.lexists(older_link)}/{os.path.lexists(current_link)}"
    )
    assert older_link in result.pruned_links and current_link in result.pruned_links, (
        f"expected both symlinks in result.pruned_links={result.pruned_links}"
    )
    assert not prior_real_dir.exists(), (
        f"expected non-target real directory {prior_real_dir} removed"
    )
    assert prior_real_dir in result.pruned_links, (
        f"expected removed real directory {prior_real_dir} in "
        f"result.pruned_links={result.pruned_links}"
    )


def test_plugin_with_undeterminable_current_version_prunes_symlinks_and_exits(
    tmp_path: Path,
) -> None:
    """A working-tree plugin whose current version cannot be determined (absent from
    the history's current-version map, as when its manifest version is unreadable)
    takes the no-current-real-directory branch: its compatibility symlinks are pruned
    and the loop exits cleanly without creating any link or leaving a non-target real
    directory.
    """
    cache_root = tmp_path / "cache"
    _write_skill(cache_root, PLUGIN_NAME, OLDER_VERSION, "older content")
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME
    older_dir = plugin_dir / OLDER_VERSION
    stale_link = plugin_dir / CURRENT_VERSION
    stale_link.symlink_to(OLDER_VERSION, target_is_directory=True)
    history = StaticHistory(
        plugins=frozenset([PLUGIN_NAME]),
        versions_by_plugin={
            PLUGIN_NAME: frozenset([OLDER_VERSION, CURRENT_VERSION]),
        },
        current_by_plugin={},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        cache_root=cache_root,
        history=history,
        runner=_quiet_runner,
    )

    assert not os.path.lexists(stale_link), (
        f"expected {stale_link} pruned when the current version is undeterminable"
    )
    assert stale_link in result.pruned_links, (
        f"expected {stale_link} in result.pruned_links={result.pruned_links}"
    )
    assert result.linked_versions == (), (
        f"expected no links when the current version is undeterminable, got {result.linked_versions}"
    )
    assert not older_dir.exists(), (
        f"expected non-target real directory {older_dir} removed"
    )


def test_not_installed_plugin_with_stale_real_dir_is_pruned(tmp_path: Path) -> None:
    """A working-tree plugin whose only cache entry is a stale real version directory,
    and which Codex does not report as installed, has its entire cache directory pruned
    -- not-installed is treated identically to a working-tree-absent orphan. Reproduces
    the captured state where `python/0.18.6` lingered while `0.18.8` was never
    materialized and `validate_install` reported MISSING for the current version.
    """
    repo_root = tmp_path / "repo"
    cache_root = tmp_path / "cache"
    _write_skill(
        cache_root, NOT_INSTALLED_PLUGIN, NOT_INSTALLED_STALE_VERSION, "stale content"
    )
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / NOT_INSTALLED_PLUGIN
    history = StaticHistory(
        plugins=frozenset([NOT_INSTALLED_PLUGIN]),
        versions_by_plugin={
            NOT_INSTALLED_PLUGIN: frozenset(
                [NOT_INSTALLED_STALE_VERSION, NOT_INSTALLED_CURRENT_VERSION]
            ),
        },
        current_by_plugin={NOT_INSTALLED_PLUGIN: NOT_INSTALLED_CURRENT_VERSION},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({}),
        runner=_quiet_runner,
    )

    assert not plugin_dir.exists(), (
        f"expected the whole cache directory {plugin_dir} pruned for a not-installed "
        f"plugin, leaving nothing for validate_install to flag"
    )
    assert NOT_INSTALLED_PLUGIN in result.pruned_plugins, (
        f"expected {NOT_INSTALLED_PLUGIN} in result.pruned_plugins={result.pruned_plugins}"
    )


def test_installed_set_query_failure_aborts_without_pruning(tmp_path: Path) -> None:
    """When the installed-set query fails, preservation raises and mutates nothing: a
    cache directory that would be pruned were the query to succeed empty remains intact,
    proving the abort happens before any prune so a degraded signal never drives
    deletion.
    """
    cache_root = tmp_path / "cache"
    _write_skill(
        cache_root, NOT_INSTALLED_PLUGIN, NOT_INSTALLED_STALE_VERSION, "stale content"
    )
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / NOT_INSTALLED_PLUGIN
    history = StaticHistory(
        plugins=frozenset([NOT_INSTALLED_PLUGIN]),
        versions_by_plugin={
            NOT_INSTALLED_PLUGIN: frozenset([NOT_INSTALLED_CURRENT_VERSION]),
        },
        current_by_plugin={NOT_INSTALLED_PLUGIN: NOT_INSTALLED_CURRENT_VERSION},
    )

    with pytest.raises(preserve_codex_plugin_cache.InstalledSetError):
        preserve_codex_plugin_cache.refresh_installed_plugins(
            DEFAULT_MARKETPLACE,
            cache_root=cache_root,
            history=history,
            installed=RaisingInstalled(),
            runner=_quiet_runner,
        )

    assert plugin_dir.is_dir(), (
        f"expected {plugin_dir} untouched when the installed-set query fails; "
        f"preservation must abort before any prune"
    )


def test_dry_run_skips_installed_set_query_and_retains_cache(tmp_path: Path) -> None:
    """A dry run reports planned changes without querying the installed set: the
    provided installed provider is never invoked (a raising one does not raise), and
    a not-installed plugin whose cache a real run would prune is retained. The preview
    therefore needs no Codex CLI present and mutates nothing.
    """
    cache_root = tmp_path / "cache"
    _write_skill(
        cache_root, NOT_INSTALLED_PLUGIN, NOT_INSTALLED_STALE_VERSION, "stale content"
    )
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / NOT_INSTALLED_PLUGIN
    history = StaticHistory(
        plugins=frozenset([NOT_INSTALLED_PLUGIN]),
        versions_by_plugin={
            NOT_INSTALLED_PLUGIN: frozenset(
                [NOT_INSTALLED_STALE_VERSION, NOT_INSTALLED_CURRENT_VERSION]
            ),
        },
        current_by_plugin={NOT_INSTALLED_PLUGIN: NOT_INSTALLED_CURRENT_VERSION},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        cache_root=cache_root,
        history=history,
        installed=RaisingInstalled(),
        dry_run=True,
        runner=_quiet_runner,
    )

    assert plugin_dir.is_dir(), (
        f"dry run must retain {plugin_dir}: it skips the installed-set query and "
        f"prunes nothing"
    )
    assert result.pruned_plugins == (), (
        f"dry run plans no prunes when the query is skipped, got {result.pruned_plugins}"
    )
    assert plugin_dir / NOT_INSTALLED_STALE_VERSION in result.pruned_links, (
        "dry run must report the stale real directory it would prune without "
        f"mutating it; got result.pruned_links={result.pruned_links}"
    )


def test_plugin_add_failure_returns_before_cache_prune(tmp_path: Path) -> None:
    """A non-zero local plugin add returns before cache pruning: the result carries
    the refresh return code, and no cache directory is pruned.
    """
    repo_root = tmp_path / "repo"
    cache_root = tmp_path / "cache"
    _write_dist_codex_manifest(
        repo_root,
        NOT_INSTALLED_PLUGIN,
        NOT_INSTALLED_CURRENT_VERSION,
    )
    _write_skill(
        cache_root, NOT_INSTALLED_PLUGIN, NOT_INSTALLED_STALE_VERSION, "stale content"
    )
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / NOT_INSTALLED_PLUGIN
    history = StaticHistory(
        plugins=frozenset([NOT_INSTALLED_PLUGIN]),
        versions_by_plugin={
            NOT_INSTALLED_PLUGIN: frozenset([NOT_INSTALLED_CURRENT_VERSION]),
        },
        current_by_plugin={NOT_INSTALLED_PLUGIN: NOT_INSTALLED_CURRENT_VERSION},
    )

    def _failing_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1)

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled(
            {NOT_INSTALLED_PLUGIN: NOT_INSTALLED_CURRENT_VERSION}
        ),
        runner=_failing_runner,
    )

    assert result.refresh_returncode == 1, (
        f"expected the refresh return code to propagate, got {result.refresh_returncode}"
    )
    assert plugin_dir.is_dir(), (
        f"expected {plugin_dir} untouched: a refresh failure returns before any prune"
    )


def test_partial_plugin_add_failure_reconciles_successful_refresh(
    tmp_path: Path,
) -> None:
    """When one plugin add succeeds before a later plugin add fails, the successful
    plugin is reconciled before the non-zero refresh result returns.
    """
    repo_root = tmp_path / "repo"
    cache_root = tmp_path / "cache"
    _write_dist_codex_manifest(repo_root, "alpha", "0.2.0")
    _write_dist_codex_manifest(repo_root, "zeta", "0.2.0")
    _write_skill(cache_root, "alpha", "0.1.0", "prior alpha content")
    _write_skill(cache_root, "zeta", "0.1.0", "prior zeta content")
    alpha_dir = cache_root / DEFAULT_MARKETPLACE / "alpha"
    alpha_prior_dir = alpha_dir / "0.1.0"
    alpha_current_dir = alpha_dir / "0.2.0"
    zeta_dir = cache_root / DEFAULT_MARKETPLACE / "zeta"
    zeta_prior_dir = zeta_dir / "0.1.0"
    history = StaticHistory(
        plugins=frozenset(["alpha", "zeta"]),
        versions_by_plugin={
            "alpha": frozenset(["0.1.0", "0.2.0"]),
            "zeta": frozenset(["0.1.0", "0.2.0"]),
        },
        current_by_plugin={"alpha": "0.2.0", "zeta": "0.2.0"},
    )

    def _failing_second_runner(
        command: list[str],
    ) -> subprocess.CompletedProcess[str]:
        plugin_ref = command[len(preserve_codex_plugin_cache.CODEX_PLUGIN_ADD_COMMAND)]
        plugin, _, _ = plugin_ref.partition("@")
        if plugin == "alpha":
            _write_skill(cache_root, "alpha", "0.2.0", "current alpha content")
            return subprocess.CompletedProcess(command, 0)
        return subprocess.CompletedProcess(command, 1)

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({"alpha": "0.2.0", "zeta": "0.2.0"}),
        runner=_failing_second_runner,
    )

    assert result.refresh_returncode == 1
    assert alpha_current_dir.is_dir() and not alpha_current_dir.is_symlink(), (
        f"expected successful refresh target {alpha_current_dir} to stay real"
    )
    assert alpha_prior_dir.is_symlink(), (
        f"expected {alpha_prior_dir} to be repaired before returning failure"
    )
    assert alpha_prior_dir.resolve() == alpha_current_dir.resolve(), (
        f"expected {alpha_prior_dir} to point at {alpha_current_dir}"
    )
    assert zeta_prior_dir.is_dir() and not zeta_prior_dir.is_symlink(), (
        f"expected failed plugin cache {zeta_prior_dir} to remain untouched"
    )


def test_absent_cache_with_empty_installed_set_runs_no_plugin_add(
    tmp_path: Path,
) -> None:
    """An empty Codex installed set against an absent cache is a valid empty refresh:
    no plugin add command runs, no registration repair is attempted, and no cache
    mutation is needed.
    """
    repo_root = tmp_path / "repo"
    cache_root = tmp_path / "cache"
    history = StaticHistory(
        plugins=frozenset([PLUGIN_NAME]),
        versions_by_plugin={PLUGIN_NAME: frozenset([OLDER_VERSION, CURRENT_VERSION])},
        current_by_plugin={PLUGIN_NAME: CURRENT_VERSION},
    )
    runner = MaterializingAddRunner(
        cache_root=cache_root,
        versions={PLUGIN_NAME: CURRENT_VERSION},
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({}),
        runner=runner,
    )

    assert runner.calls == []
    assert result.refresh_returncode == 0
    assert result.linked_versions == ()
    assert result.pruned_links == ()
    assert result.pruned_plugins == ()


def test_installed_plugin_preserved_while_not_installed_sibling_pruned(
    tmp_path: Path,
) -> None:
    """With two working-tree plugins — one in the Codex installed set, one absent —
    preservation keeps the installed plugin's cache and prunes the not-installed
    sibling's. This pins the preserved set to the intersection of the working-tree
    set and the installed set: pruning every plugin (ignoring the installed set) or
    preserving every plugin (ignoring it) both fail this test.
    """
    repo_root = _repo_with_dist_codex_plugin(tmp_path, PLUGIN_NAME, CURRENT_VERSION)
    cache_root = tmp_path / "cache"
    _write_skill(cache_root, PLUGIN_NAME, CURRENT_VERSION, "installed content")
    _write_skill(
        cache_root, NOT_INSTALLED_PLUGIN, NOT_INSTALLED_STALE_VERSION, "stale content"
    )
    installed_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME
    not_installed_dir = cache_root / DEFAULT_MARKETPLACE / NOT_INSTALLED_PLUGIN
    history = StaticHistory(
        plugins=frozenset([PLUGIN_NAME, NOT_INSTALLED_PLUGIN]),
        versions_by_plugin={
            PLUGIN_NAME: frozenset([CURRENT_VERSION]),
            NOT_INSTALLED_PLUGIN: frozenset(
                [NOT_INSTALLED_STALE_VERSION, NOT_INSTALLED_CURRENT_VERSION]
            ),
        },
        current_by_plugin={
            PLUGIN_NAME: CURRENT_VERSION,
            NOT_INSTALLED_PLUGIN: NOT_INSTALLED_CURRENT_VERSION,
        },
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({PLUGIN_NAME: CURRENT_VERSION}),
        runner=_quiet_runner,
    )

    assert installed_dir.is_dir(), (
        f"installed plugin {installed_dir} must be preserved (it is in the intersection)"
    )
    assert PLUGIN_NAME not in result.pruned_plugins, (
        f"expected {PLUGIN_NAME} not pruned, got {result.pruned_plugins}"
    )
    assert not not_installed_dir.exists(), (
        f"not-installed plugin {not_installed_dir} must be pruned (outside the intersection)"
    )
    assert NOT_INSTALLED_PLUGIN in result.pruned_plugins, (
        f"expected {NOT_INSTALLED_PLUGIN} in result.pruned_plugins={result.pruned_plugins}"
    )


def test_empty_installed_set_prunes_every_plugin_cache(tmp_path: Path) -> None:
    """A successful query reporting an empty installed set prunes every plugin's cache
    directory for the marketplace — an empty set is a valid prune-all instruction,
    distinct from a failed query (which aborts).
    """
    repo_root = tmp_path / "repo"
    cache_root = tmp_path / "cache"
    _write_skill(cache_root, PLUGIN_NAME, CURRENT_VERSION, "content a")
    _write_skill(
        cache_root, NOT_INSTALLED_PLUGIN, NOT_INSTALLED_STALE_VERSION, "content b"
    )
    dir_a = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME
    dir_b = cache_root / DEFAULT_MARKETPLACE / NOT_INSTALLED_PLUGIN
    history = StaticHistory(
        plugins=frozenset([PLUGIN_NAME, NOT_INSTALLED_PLUGIN]),
        versions_by_plugin={
            PLUGIN_NAME: frozenset([CURRENT_VERSION]),
            NOT_INSTALLED_PLUGIN: frozenset([NOT_INSTALLED_CURRENT_VERSION]),
        },
        current_by_plugin={
            PLUGIN_NAME: CURRENT_VERSION,
            NOT_INSTALLED_PLUGIN: NOT_INSTALLED_CURRENT_VERSION,
        },
    )

    result = preserve_codex_plugin_cache.refresh_installed_plugins(
        DEFAULT_MARKETPLACE,
        repo_root=repo_root,
        cache_root=cache_root,
        history=history,
        installed=StaticInstalled({}),
        runner=_quiet_runner,
    )

    assert not dir_a.exists() and not dir_b.exists(), (
        f"empty installed set must prune every cache dir; "
        f"a={dir_a.exists()} b={dir_b.exists()}"
    )
    assert PLUGIN_NAME in result.pruned_plugins and (
        NOT_INSTALLED_PLUGIN in result.pruned_plugins
    ), f"expected both plugins pruned, got {result.pruned_plugins}"
