"""Upgrade a Codex marketplace while preserving stale plugin cache paths.

Codex replaces marketplace cache versions during upgrade. Skills listed in an
active conversation can still point at the removed version directory, so this
wrapper restores those old version directories as short-lived symlinks to the
newly installed version of the same plugin.

Usage::

    uv run python -m outcomeeng.scripts.preserve_codex_plugin_cache outcomeeng
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MARKETPLACE = "outcomeeng"
DEFAULT_MAX_AGE_DAYS = 7
SECONDS_PER_DAY = 24 * 60 * 60
CODEX_UPGRADE_COMMAND = ("codex", "plugin", "marketplace", "upgrade")

type CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class CachedVersion:
    """One plugin version directory found in the marketplace cache."""

    plugin: str
    version: str
    path: Path
    files: tuple[Path, ...]
    is_symlink: bool
    modified_at: float


@dataclass(frozen=True)
class CacheSnapshot:
    """A point-in-time snapshot of marketplace plugin versions and files."""

    marketplace_dir: Path
    versions: tuple[CachedVersion, ...]

    @classmethod
    def capture(cls, cache_root: Path, marketplace: str) -> CacheSnapshot:
        marketplace_dir = cache_root / marketplace
        versions: list[CachedVersion] = []
        if not marketplace_dir.is_dir():
            return cls(marketplace_dir=marketplace_dir, versions=())

        for plugin_dir in sorted(marketplace_dir.iterdir()):
            if not plugin_dir.is_dir():
                continue
            for version_dir in sorted(plugin_dir.iterdir()):
                if not version_dir.is_dir():
                    continue
                is_symlink = version_dir.is_symlink()
                versions.append(
                    CachedVersion(
                        plugin=plugin_dir.name,
                        version=version_dir.name,
                        path=version_dir,
                        files=_snapshot_files(version_dir),
                        is_symlink=is_symlink,
                        modified_at=_modified_at(version_dir, is_symlink),
                    )
                )

        return cls(marketplace_dir=marketplace_dir, versions=tuple(versions))

    def real_versions_by_plugin(self) -> dict[str, tuple[CachedVersion, ...]]:
        grouped: dict[str, list[CachedVersion]] = defaultdict(list)
        for version in self.versions:
            if not version.is_symlink:
                grouped[version.plugin].append(version)
        return {
            plugin: tuple(sorted(versions, key=lambda item: item.modified_at))
            for plugin, versions in grouped.items()
        }


@dataclass(frozen=True)
class CachePreservationResult:
    """Observable results from one marketplace upgrade wrapper run."""

    linked_versions: tuple[Path, ...]
    pruned_links: tuple[Path, ...]
    skipped_plugins: tuple[str, ...]
    upgrade_returncode: int


def default_cache_root() -> Path:
    return Path.home() / ".codex" / "plugins" / "cache"


def current_time() -> float:
    return time.time()


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True)


def preserve_during_upgrade(
    marketplace: str = DEFAULT_MARKETPLACE,
    *,
    cache_root: Path | None = None,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    runner: CommandRunner = run_command,
    dry_run: bool = False,
) -> CachePreservationResult:
    """Run the marketplace upgrade and preserve cache paths removed by it."""
    resolved_cache_root = cache_root if cache_root is not None else default_cache_root()
    before = CacheSnapshot.capture(resolved_cache_root, marketplace)
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
            skipped_plugins=(),
            upgrade_returncode=upgrade_result.returncode,
        )

    after = CacheSnapshot.capture(resolved_cache_root, marketplace)
    now = current_time()
    linked_versions, skipped_plugins = restore_missing_version_links(
        before,
        after,
        max_age_days=max_age_days,
        now=now,
        dry_run=dry_run,
    )
    pruned_links = prune_old_version_symlinks(
        after.marketplace_dir,
        max_age_days=max_age_days,
        now=now,
        dry_run=dry_run,
    )

    return CachePreservationResult(
        linked_versions=linked_versions,
        pruned_links=pruned_links,
        skipped_plugins=skipped_plugins,
        upgrade_returncode=upgrade_result.returncode,
    )


def restore_missing_version_links(
    before: CacheSnapshot,
    after: CacheSnapshot,
    *,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    now: float | None = None,
    dry_run: bool = False,
) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    """Link removed old version paths to the newest current version."""
    current_versions = after.real_versions_by_plugin()
    cutoff = (now if now is not None else current_time()) - (
        max_age_days * SECONDS_PER_DAY
    )
    linked: list[Path] = []
    skipped: set[str] = set()

    for cached_version in before.versions:
        if _path_exists(cached_version.path):
            continue
        if cached_version.is_symlink and cached_version.modified_at < cutoff:
            continue

        target = _newest_version_for_plugin(current_versions, cached_version.plugin)
        if target is None:
            skipped.add(cached_version.plugin)
            continue

        if not dry_run:
            cached_version.path.parent.mkdir(parents=True, exist_ok=True)
            cached_version.path.symlink_to(target.path.name, target_is_directory=True)
        linked.append(cached_version.path)

    return tuple(linked), tuple(sorted(skipped))


def prune_old_version_symlinks(
    marketplace_dir: Path,
    *,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    now: float | None = None,
    dry_run: bool = False,
) -> tuple[Path, ...]:
    """Remove version-directory compatibility symlinks older than max_age_days."""
    if not marketplace_dir.is_dir():
        return ()

    cutoff = (now if now is not None else current_time()) - (
        max_age_days * SECONDS_PER_DAY
    )
    pruned: list[Path] = []

    for plugin_dir in sorted(marketplace_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        for version_dir in sorted(plugin_dir.iterdir()):
            if not version_dir.is_symlink():
                continue
            if version_dir.lstat().st_mtime >= cutoff:
                continue
            if not dry_run:
                version_dir.unlink()
            pruned.append(version_dir)

    return tuple(pruned)


def _snapshot_files(version_dir: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for path in sorted(version_dir.rglob("*")):
        if path.is_dir() and not path.is_symlink():
            continue
        files.append(path.relative_to(version_dir))
    return tuple(files)


def _modified_at(version_dir: Path, is_symlink: bool) -> float:
    if is_symlink:
        return version_dir.lstat().st_mtime
    return version_dir.stat().st_mtime


def _path_exists(path: Path) -> bool:
    return os.path.lexists(path)


def _newest_version_for_plugin(
    versions_by_plugin: dict[str, tuple[CachedVersion, ...]],
    plugin: str,
) -> CachedVersion | None:
    versions = versions_by_plugin.get(plugin)
    if not versions:
        return None
    return versions[-1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Upgrade a Codex marketplace while preserving stale cache paths"
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
        "--max-age-days",
        type=int,
        default=DEFAULT_MAX_AGE_DAYS,
        help="Prune compatibility symlinks older than this many days",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Snapshot and report without running upgrade or changing symlinks",
    )
    args = parser.parse_args(argv)

    result = preserve_during_upgrade(
        args.marketplace,
        cache_root=args.cache_root,
        max_age_days=args.max_age_days,
        dry_run=args.dry_run,
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
        f"{len(result.pruned_links)} pruned link(s)"
    )
    for plugin in result.skipped_plugins:
        print(f"warning: no compatible current cache version found for {plugin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
