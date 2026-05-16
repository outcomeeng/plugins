"""Level 1 scenarios for the Codex plugin cache preservation step.

Each scenario corresponds to one assertion in
``spx/13-infrastructure.enabler/32-installation.enabler/installation.md``.

The tests drive the production ``GitPluginHistory`` against a real ephemeral
git repository created by ``outcomeeng_testing.harnesses.marketplace_repo``.
The only test double introduced is a quiet ``runner`` substituted for the
``codex plugin marketplace upgrade`` subprocess: real Codex mutates shared
admin state under ``~/.codex/``, which is a Stage 5 exception 4 (Safety) per
``plugins/spec-tree/skills/testing/references/methodology.md``. Every other
production code path — ``GitPluginHistory`` itself, the git-log walker,
``_parse_manifest_version``, the working-tree-version fallback, the real
filesystem under ``cache_root`` — runs unmodified.

This file replaces an earlier version that injected a ``StaticHistory`` stub
and bypassed the history walker entirely. The earlier shape let regressions
in ``GitPluginHistory``, ``_parse_manifest_version``, the ``--follow`` flag,
and ``Path.cwd()``-based repo-root resolution ship to production while these
tests stayed green.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from outcomeeng.distribution.codex_cache import (
    DEFAULT_MARKETPLACE,
    GitPluginHistory,
    preserve_during_upgrade,
)
from outcomeeng_testing.harnesses.marketplace_repo import (
    ManifestCommit,
    with_marketplace_repo,
)

PLUGIN_NAME = "spec-tree"
ORPHAN_PLUGIN_NAME = "removed-plugin"
OLDER_VERSION = "0.26.5"
CURRENT_VERSION = "0.26.6"


def _quiet_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Stage 5 exception 4 (Safety): swallow `codex plugin marketplace upgrade`.

    Real Codex mutates ``~/.codex/.tmp/marketplaces/<marketplace>/`` and the
    user's plugin cache. Tests must not touch shared admin state. The stub
    records nothing because the assertions look at the cache filesystem
    that ``preserve_during_upgrade`` writes after this call returns.
    """
    return subprocess.CompletedProcess(command, 0)


def _make_cache(cache_root: Path, plugin: str, version: str) -> Path:
    """Create the post-upgrade cache state: one real version directory."""
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / plugin / version
    (plugin_dir / "skills" / "x").mkdir(parents=True)
    return plugin_dir


def test_chain_recovery_restores_in_window_published_version_as_symlink(
    tmp_path: Path,
) -> None:
    """Two manifest versions committed within the window; only the current
    version is on disk. After preservation, the older version path is a
    symlink to the current version directory.
    """
    cache_root = tmp_path / "cache"
    current_dir = _make_cache(cache_root, PLUGIN_NAME, CURRENT_VERSION)
    older_path = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME / OLDER_VERSION

    with with_marketplace_repo(
        tmp_path,
        [
            ManifestCommit(plugin=PLUGIN_NAME, version=OLDER_VERSION, days_ago=5),
            ManifestCommit(plugin=PLUGIN_NAME, version=CURRENT_VERSION, days_ago=0),
        ],
    ) as repo:
        history = GitPluginHistory(repo_root=repo.root, window_days=10)
        result = preserve_during_upgrade(
            DEFAULT_MARKETPLACE,
            cache_root=cache_root,
            history=history,
            runner=_quiet_runner,
        )

    assert older_path.is_symlink(), f"expected {older_path} to be a symlink"
    assert older_path.resolve() == current_dir.resolve()
    assert older_path in result.linked_versions


def test_out_of_window_compatibility_symlink_is_removed(tmp_path: Path) -> None:
    """A compatibility symlink for a version whose manifest commit falls
    outside the window is removed during preservation.
    """
    cache_root = tmp_path / "cache"
    _make_cache(cache_root, PLUGIN_NAME, CURRENT_VERSION)
    stale_link = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME / OLDER_VERSION
    stale_link.symlink_to(CURRENT_VERSION, target_is_directory=True)

    with with_marketplace_repo(
        tmp_path,
        [
            ManifestCommit(plugin=PLUGIN_NAME, version=OLDER_VERSION, days_ago=42),
            ManifestCommit(plugin=PLUGIN_NAME, version=CURRENT_VERSION, days_ago=0),
        ],
    ) as repo:
        history = GitPluginHistory(repo_root=repo.root, window_days=10)
        result = preserve_during_upgrade(
            DEFAULT_MARKETPLACE,
            cache_root=cache_root,
            history=history,
            runner=_quiet_runner,
        )

    assert not os.path.lexists(stale_link), f"expected {stale_link} to be removed"
    assert stale_link in result.pruned_links


def test_orphan_plugin_cache_directory_is_pruned(tmp_path: Path) -> None:
    """A plugin directory present in the cache but absent from the working
    tree has its entire cache directory removed during preservation.
    """
    cache_root = tmp_path / "cache"
    orphan_dir = _make_cache(cache_root, ORPHAN_PLUGIN_NAME, OLDER_VERSION)
    _make_cache(cache_root, PLUGIN_NAME, CURRENT_VERSION)

    with with_marketplace_repo(
        tmp_path,
        [
            ManifestCommit(plugin=PLUGIN_NAME, version=CURRENT_VERSION, days_ago=0),
        ],
    ) as repo:
        history = GitPluginHistory(repo_root=repo.root, window_days=10)
        result = preserve_during_upgrade(
            DEFAULT_MARKETPLACE,
            cache_root=cache_root,
            history=history,
            runner=_quiet_runner,
        )

    assert not orphan_dir.exists(), f"expected {orphan_dir} cache to be pruned"
    assert ORPHAN_PLUGIN_NAME in result.pruned_plugins


def test_git_history_walker_returns_versions_committed_within_window(
    tmp_path: Path,
) -> None:
    """The production GitPluginHistory walker reads versions from git log of
    each plugin's manifest path. Versions whose commits fall outside the
    window are not returned; the current working-tree version is always
    included regardless of its commit's date.
    """
    in_window_version = "0.26.5"
    current_version = "0.26.6"
    out_of_window_version = "0.10.0"

    with with_marketplace_repo(
        tmp_path,
        [
            ManifestCommit(
                plugin=PLUGIN_NAME, version=out_of_window_version, days_ago=42
            ),
            ManifestCommit(plugin=PLUGIN_NAME, version=in_window_version, days_ago=5),
            ManifestCommit(plugin=PLUGIN_NAME, version=current_version, days_ago=0),
        ],
    ) as repo:
        history = GitPluginHistory(repo_root=repo.root, window_days=10)
        versions = history.published_versions(PLUGIN_NAME)

    assert current_version in versions
    assert in_window_version in versions
    assert out_of_window_version not in versions


def test_real_prior_version_directory_outside_window_is_left_in_place(
    tmp_path: Path,
) -> None:
    """Preservation manages symlinks only. A real (non-symlink) directory at
    a prior version path is left alone — removing it would risk data loss.
    """
    cache_root = tmp_path / "cache"
    current_dir = _make_cache(cache_root, PLUGIN_NAME, CURRENT_VERSION)
    real_prior = _make_cache(cache_root, PLUGIN_NAME, OLDER_VERSION)

    with with_marketplace_repo(
        tmp_path,
        [
            ManifestCommit(plugin=PLUGIN_NAME, version=OLDER_VERSION, days_ago=42),
            ManifestCommit(plugin=PLUGIN_NAME, version=CURRENT_VERSION, days_ago=0),
        ],
    ) as repo:
        history = GitPluginHistory(repo_root=repo.root, window_days=10)
        result = preserve_during_upgrade(
            DEFAULT_MARKETPLACE,
            cache_root=cache_root,
            history=history,
            runner=_quiet_runner,
        )

    assert real_prior.is_dir() and not real_prior.is_symlink(), (
        f"expected real prior directory {real_prior} to remain in place"
    )
    assert real_prior not in result.pruned_links
    assert current_dir.is_dir() and not current_dir.is_symlink()
