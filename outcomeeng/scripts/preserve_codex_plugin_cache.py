"""Upgrade a Codex marketplace and reconcile the plugin cache against history.

After the upgrade, the cache for each plugin in the working tree is reconciled
against the set of versions published to the plugin's manifest within the
configured window (default ten days). Versions inside the window become
either the real current directory or a symlink pointing at it; versions outside
the window are removed; plugins absent from the working tree have their cache
directory pruned in full.

Per
``spx/13-infrastructure.enabler/32-installation.enabler/21-codex-cache-preservation.adr.md``:
the preservation set is derived from git history, not from the pre-upgrade
cache snapshot. A single bypassed recipe invocation has no permanent effect --
the next invocation reconstructs the symlink set from the same authoritative
source.

Usage::

    uv run python -m outcomeeng.scripts.preserve_codex_plugin_cache outcomeeng
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

DEFAULT_MARKETPLACE = "outcomeeng"
DEFAULT_WINDOW_DAYS = 10
CODEX_UPGRADE_COMMAND = ("codex", "plugin", "marketplace", "upgrade")

type CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


class PluginHistory(Protocol):
    """Source-of-truth for which versions to preserve.

    Production implementations walk git history of each plugin's manifest within
    the configured window, per
    ``spx/13-infrastructure.enabler/32-installation.enabler/21-codex-cache-preservation.adr.md``.
    """

    def working_tree_plugins(self) -> frozenset[str]: ...

    def published_versions(self, plugin: str) -> frozenset[str]: ...


@dataclass(frozen=True)
class GitPluginHistory:
    """Default PluginHistory: walks ``git log`` of each plugin's manifest."""

    repo_root: Path
    window_days: int = DEFAULT_WINDOW_DAYS

    def working_tree_plugins(self) -> frozenset[str]:
        plugins_dir = self.repo_root / "plugins"
        if not plugins_dir.is_dir():
            return frozenset()
        names: set[str] = set()
        for child in plugins_dir.iterdir():
            if not child.is_dir():
                continue
            manifest = child / ".claude-plugin" / "plugin.json"
            if manifest.is_file():
                names.add(child.name)
        return frozenset(names)

    def published_versions(self, plugin: str) -> frozenset[str]:
        manifest_rel = f"plugins/{plugin}/.claude-plugin/plugin.json"
        log_result = subprocess.run(
            [
                "git",
                "log",
                f"--since={self.window_days} days ago",
                "--format=%H",
                "--follow",
                "--",
                manifest_rel,
            ],
            capture_output=True,
            text=True,
            cwd=self.repo_root,
            check=False,
        )
        versions: set[str] = set()
        if log_result.returncode == 0:
            for sha in log_result.stdout.split():
                version = self._read_manifest_version_at(sha, manifest_rel)
                if version is not None:
                    versions.add(version)
        # Always include the current working-tree version, even if its commit
        # falls outside the window. The current version is the published target,
        # not a historical compatibility entry.
        current = self._read_working_tree_version(manifest_rel)
        if current is not None:
            versions.add(current)
        return frozenset(versions)

    def _read_manifest_version_at(self, sha: str, manifest_rel: str) -> str | None:
        result = subprocess.run(
            ["git", "show", f"{sha}:{manifest_rel}"],
            capture_output=True,
            text=True,
            cwd=self.repo_root,
            check=False,
        )
        if result.returncode != 0:
            return None
        return _parse_manifest_version(result.stdout)

    def _read_working_tree_version(self, manifest_rel: str) -> str | None:
        manifest_path = self.repo_root / manifest_rel
        try:
            text = manifest_path.read_text()
        except OSError:
            return None
        return _parse_manifest_version(text)


def _parse_manifest_version(text: str) -> str | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    version = data.get("version")
    return version if isinstance(version, str) else None


@dataclass(frozen=True)
class CachePreservationResult:
    """Observable results from one marketplace upgrade wrapper run."""

    linked_versions: tuple[Path, ...]
    pruned_links: tuple[Path, ...]
    pruned_plugins: tuple[str, ...]
    skipped_plugins: tuple[str, ...]
    upgrade_returncode: int


def default_cache_root() -> Path:
    return Path.home() / ".codex" / "plugins" / "cache"


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True)


def preserve_during_upgrade(
    marketplace: str = DEFAULT_MARKETPLACE,
    *,
    cache_root: Path | None = None,
    runner: CommandRunner = run_command,
    dry_run: bool = False,
    history: PluginHistory | None = None,
) -> CachePreservationResult:
    """Run the marketplace upgrade and reconcile the cache against history."""
    resolved_cache_root = cache_root if cache_root is not None else default_cache_root()
    resolved_history = (
        history if history is not None else GitPluginHistory(repo_root=Path.cwd())
    )
    command = [*CODEX_UPGRADE_COMMAND, marketplace]

    upgrade_result: subprocess.CompletedProcess[str]
    if dry_run:
        upgrade_result = subprocess.CompletedProcess(command, 0)
    else:
        upgrade_result = runner(command)

    if upgrade_result.returncode != 0:
        return CachePreservationResult(
            linked_versions=(),
            pruned_links=(),
            pruned_plugins=(),
            skipped_plugins=(),
            upgrade_returncode=upgrade_result.returncode,
        )

    marketplace_dir = resolved_cache_root / marketplace
    working_tree_plugins = resolved_history.working_tree_plugins()

    pruned_plugins = _prune_orphan_plugins(
        marketplace_dir, working_tree_plugins, dry_run=dry_run
    )

    linked_versions: list[Path] = []
    pruned_links: list[Path] = []
    skipped_plugins: list[str] = []

    for plugin in sorted(working_tree_plugins):
        plugin_dir = marketplace_dir / plugin
        in_window = resolved_history.published_versions(plugin)
        current_real = _newest_real_version_dir(plugin_dir)
        if current_real is None:
            skipped_plugins.append(plugin)
            continue

        keep_versions = in_window | {current_real.name}
        pruned_links.extend(
            _prune_out_of_window_paths(plugin_dir, keep_versions, dry_run=dry_run)
        )
        linked_versions.extend(
            _ensure_in_window_symlinks(
                plugin_dir, current_real, in_window, dry_run=dry_run
            )
        )

    return CachePreservationResult(
        linked_versions=tuple(linked_versions),
        pruned_links=tuple(pruned_links),
        pruned_plugins=tuple(pruned_plugins),
        skipped_plugins=tuple(skipped_plugins),
        upgrade_returncode=upgrade_result.returncode,
    )


def _prune_orphan_plugins(
    marketplace_dir: Path,
    working_tree_plugins: frozenset[str],
    *,
    dry_run: bool,
) -> list[str]:
    if not marketplace_dir.is_dir():
        return []
    pruned: list[str] = []
    for plugin_dir in sorted(marketplace_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        if plugin_dir.name in working_tree_plugins:
            continue
        if not dry_run:
            shutil.rmtree(plugin_dir)
        pruned.append(plugin_dir.name)
    return pruned


def _newest_real_version_dir(plugin_dir: Path) -> Path | None:
    if not plugin_dir.is_dir():
        return None
    real_versions = [
        entry
        for entry in plugin_dir.iterdir()
        if entry.is_dir() and not entry.is_symlink()
    ]
    if not real_versions:
        return None
    return max(real_versions, key=lambda p: p.stat().st_mtime)


def _prune_out_of_window_paths(
    plugin_dir: Path,
    keep_versions: frozenset[str],
    *,
    dry_run: bool,
) -> list[Path]:
    pruned: list[Path] = []
    for entry in sorted(plugin_dir.iterdir()):
        if entry.name in keep_versions:
            continue
        if not entry.is_symlink():
            # Real version directory outside the keep set is left alone -- only
            # Codex itself creates these, and removing them risks data loss.
            continue
        if not dry_run:
            entry.unlink()
        pruned.append(entry)
    return pruned


def _ensure_in_window_symlinks(
    plugin_dir: Path,
    current_real: Path,
    in_window: frozenset[str],
    *,
    dry_run: bool,
) -> list[Path]:
    linked: list[Path] = []
    for version in sorted(in_window):
        if version == current_real.name:
            continue
        target_path = plugin_dir / version
        if _is_symlink_to(target_path, current_real):
            continue
        if os.path.lexists(target_path):
            if not target_path.is_symlink():
                # A real directory at an in-window version is left alone --
                # the same data-loss concern as out-of-window real directories.
                continue
            if not dry_run:
                target_path.unlink()
        if not dry_run:
            plugin_dir.mkdir(parents=True, exist_ok=True)
            target_path.symlink_to(current_real.name, target_is_directory=True)
        linked.append(target_path)
    return linked


def _is_symlink_to(path: Path, target: Path) -> bool:
    if not path.is_symlink():
        return False
    try:
        return path.resolve() == target.resolve()
    except OSError:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Upgrade a Codex marketplace and reconcile the plugin cache"
    )
    parser.add_argument(
        "marketplace",
        nargs="?",
        default=DEFAULT_MARKETPLACE,
        help="Marketplace name to upgrade",
    )
    parser.add_argument(
        "--cache-root",
        type=Path,
        default=default_cache_root(),
        help="Codex plugin cache root",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        default=DEFAULT_WINDOW_DAYS,
        help="Preserve plugin versions published within this many days",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Git working tree root for the marketplace repository",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned changes without running upgrade or mutating cache",
    )
    args = parser.parse_args(argv)

    history = GitPluginHistory(repo_root=args.repo_root, window_days=args.window_days)
    result = preserve_during_upgrade(
        args.marketplace,
        cache_root=args.cache_root,
        dry_run=args.dry_run,
        history=history,
    )

    if result.upgrade_returncode != 0:
        print(
            f"error: marketplace upgrade failed with exit code {result.upgrade_returncode}",
            file=sys.stderr,
        )
        return result.upgrade_returncode

    print(
        "Codex cache preservation: "
        f"{len(result.linked_versions)} compatibility link(s), "
        f"{len(result.pruned_links)} pruned link(s), "
        f"{len(result.pruned_plugins)} pruned plugin(s)"
    )
    for plugin in result.skipped_plugins:
        print(f"warning: no current cache version found for {plugin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
