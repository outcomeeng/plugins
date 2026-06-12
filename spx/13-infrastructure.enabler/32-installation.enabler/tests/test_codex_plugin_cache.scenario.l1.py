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
from dataclasses import dataclass
from pathlib import Path

import pytest

from outcomeeng.distribution import codex_cache as preserve_codex_plugin_cache
from outcomeeng.distribution.codex_cache import DEFAULT_MARKETPLACE

PLUGIN_NAME = "spec-tree"
ORPHAN_PLUGIN_NAME = "removed-plugin"
UNINSTALLED_PLUGIN_NAME = "uninstalled-plugin"
OLDER_VERSION = "0.26.5"
CURRENT_VERSION = "0.26.6"
NEW_CURRENT_VERSION = "0.26.7"


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


def _write_manifest(repo_root: Path, plugin: str, version: str) -> None:
    manifest = repo_root / "src" / "plugins" / plugin / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": plugin, "version": version}))


def _quiet_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 0)


def test_chain_recovery_restores_in_window_published_version_as_symlink(
    tmp_path: Path,
) -> None:
    """Two published versions in the window, cache contains only the latest version
    directory. After preservation, the older published version path is a symlink
    pointing at the current version directory.
    """
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

    result = preserve_codex_plugin_cache.preserve_during_upgrade(
        DEFAULT_MARKETPLACE,
        cache_root=cache_root,
        history=history,
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

    result = preserve_codex_plugin_cache.preserve_during_upgrade(
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

    result = preserve_codex_plugin_cache.preserve_during_upgrade(
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


def test_upgrade_without_current_real_dir_creates_no_current_symlink(
    tmp_path: Path,
) -> None:
    """A successful upgrade leaves only the older version as a real directory while
    the current working-tree version is in the published window but not materialized
    as a real directory. Preservation creates no compatibility symlink for the current
    version, so the current version path never resolves to the stale older directory.
    """
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

    result = preserve_codex_plugin_cache.preserve_during_upgrade(
        DEFAULT_MARKETPLACE,
        cache_root=cache_root,
        history=history,
        runner=_quiet_runner,
    )

    assert not os.path.lexists(current_path), (
        f"expected no cache entry at {current_path}; preservation must not fabricate "
        f"a symlink for the current version pointing at the stale {older_dir}"
    )
    assert current_path not in result.linked_versions, (
        f"expected the current version not linked, got {result.linked_versions}"
    )
    assert older_dir.is_dir() and not older_dir.is_symlink(), (
        f"expected {older_dir} to remain an untouched real directory"
    )


def test_stale_current_version_symlink_is_removed_when_no_real_dir(
    tmp_path: Path,
) -> None:
    """A prior run left a compatibility symlink at the current version pointing at an
    older real directory, and the current version still has no real directory. The
    next preservation run removes the stale symlink so the current version resolves
    to nothing rather than to the older directory's content.
    """
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

    result = preserve_codex_plugin_cache.preserve_during_upgrade(
        DEFAULT_MARKETPLACE,
        cache_root=cache_root,
        history=history,
        runner=_quiet_runner,
    )

    assert not os.path.lexists(current_link), (
        f"expected the stale symlink {current_link} to be removed so the current "
        f"version no longer resolves to {older_dir}"
    )
    assert current_link in result.pruned_links, (
        f"expected {current_link} in result.pruned_links={result.pruned_links}"
    )
    assert older_dir.is_dir() and not older_dir.is_symlink(), (
        f"expected {older_dir} to remain an untouched real directory"
    )


def test_all_compatibility_symlinks_removed_when_current_real_dir_absent(
    tmp_path: Path,
) -> None:
    """A prior run left an older in-window version symlinked to a now-non-current
    real directory, and the new current version has no real directory. The next
    preservation run removes every compatibility symlink for the plugin so no
    version resolves to the non-current directory.
    """
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

    result = preserve_codex_plugin_cache.preserve_during_upgrade(
        DEFAULT_MARKETPLACE,
        cache_root=cache_root,
        history=history,
        runner=_quiet_runner,
    )

    assert not os.path.lexists(older_link), (
        f"expected the in-window symlink {older_link} to be removed so it no longer "
        f"resolves to the non-current {prior_real_dir}"
    )
    assert older_link in result.pruned_links, (
        f"expected {older_link} in result.pruned_links={result.pruned_links}"
    )
    assert prior_real_dir.is_dir() and not prior_real_dir.is_symlink(), (
        f"expected the real directory {prior_real_dir} to remain untouched"
    )


def test_plugin_with_undeterminable_current_version_prunes_symlinks_and_exits(
    tmp_path: Path,
) -> None:
    """A working-tree plugin whose current version cannot be determined (absent from
    the history's current-version map, as when its manifest version is unreadable)
    takes the no-current-real-directory branch: its compatibility symlinks are pruned
    and the loop exits cleanly without creating any link.
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

    result = preserve_codex_plugin_cache.preserve_during_upgrade(
        DEFAULT_MARKETPLACE,
        cache_root=cache_root,
        history=history,
        runner=_quiet_runner,
    )

    assert not os.path.lexists(stale_link), (
        f"expected {stale_link} pruned when the current version is undeterminable"
    )
    assert result.linked_versions == (), (
        f"expected no links when the current version is undeterminable, got {result.linked_versions}"
    )
    assert older_dir.is_dir() and not older_dir.is_symlink(), (
        f"expected {older_dir} to remain an untouched real directory"
    )
