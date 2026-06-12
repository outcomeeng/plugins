"""Upgrade a Codex marketplace and reconcile the plugin cache against history.

After the upgrade, the cache for each plugin in the working tree is reconciled
against the set of versions published to the plugin's manifest within the
configured window (default ten days). The symlink target is the cache directory
named with the plugin's current working-tree version; in-window versions other
than the current one become symlinks pointing at it, versions outside the window
are removed, and plugins absent from the working tree have their cache directory
pruned in full. When the upgrade leaves no real directory for the current
version, every compatibility symlink for the plugin is removed and none is
created -- a symlink to a non-current directory would resolve a version to stale
content. The preservation set is derived from git history, not from the
pre-upgrade cache snapshot. A single bypassed recipe invocation has no permanent
effect -- the next invocation reconstructs the symlink set from the same
authoritative source.

Usage::

    uv run python -m outcomeeng.distribution.codex_cache outcomeeng
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
CODEX_LIST_COMMAND = ("codex", "plugin", "list", "--json", "--marketplace")
SOURCE_PLUGINS_DIR = Path("src") / "plugins"

type CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


class PluginHistory(Protocol):
    """Source-of-truth for which versions to preserve."""

    def working_tree_plugins(self) -> frozenset[str]: ...

    def published_versions(self, plugin: str) -> frozenset[str]: ...

    def current_version(self, plugin: str) -> str | None: ...


@dataclass(frozen=True)
class GitPluginHistory:
    """Default PluginHistory: walks ``git log`` of each plugin's manifest."""

    repo_root: Path
    window_days: int = DEFAULT_WINDOW_DAYS

    def working_tree_plugins(self) -> frozenset[str]:
        plugins_dir = self.repo_root / SOURCE_PLUGINS_DIR
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
        manifest_rel = f"{SOURCE_PLUGINS_DIR}/{plugin}/.claude-plugin/plugin.json"
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

    def current_version(self, plugin: str) -> str | None:
        manifest_rel = f"{SOURCE_PLUGINS_DIR}/{plugin}/.claude-plugin/plugin.json"
        return self._read_working_tree_version(manifest_rel)

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
    upgrade_returncode: int


def default_cache_root() -> Path:
    return Path.home() / ".codex" / "plugins" / "cache"


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True)


def run_command_capture(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True, capture_output=True)


class InstalledSetError(RuntimeError):
    """The Codex installed-set query failed or returned an unrecognized shape.

    Raised rather than returning an empty set so a failed query is never mistaken
    for "no plugins installed" -- the latter would prune every cache directory.
    Preservation propagates this to abort before any cache mutation.
    """


class InstalledPlugins(Protocol):
    """Source-of-truth for which plugins Codex considers installed."""

    def installed_plugins(self, marketplace: str) -> frozenset[str]: ...


def parse_installed_plugins(payload: str, marketplace: str) -> frozenset[str]:
    """Extract the installed plugin names for `marketplace` from `codex plugin list
    --json` output.

    The contract is the CLI's documented shape: a JSON object with an ``installed``
    array whose entries each carry a string ``name`` and may carry a
    ``marketplaceName``. Entries naming a different marketplace are excluded so the
    set is scoped even when the caller omits the ``--marketplace`` filter. Any
    departure from the contract -- unparseable text, a non-object payload, a missing
    or non-list ``installed`` key, or an entry without a string ``name`` -- raises
    ``InstalledSetError`` rather than yielding a silent empty set.
    """
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise InstalledSetError(
            f"codex plugin list output is not valid JSON: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise InstalledSetError("codex plugin list output is not a JSON object")
    installed = data.get("installed")
    if not isinstance(installed, list):
        raise InstalledSetError("codex plugin list output has no 'installed' array")
    names: set[str] = set()
    for entry in installed:
        if not isinstance(entry, dict):
            raise InstalledSetError(
                "codex plugin list 'installed' entry is not an object"
            )
        name = entry.get("name")
        if not isinstance(name, str):
            raise InstalledSetError(
                "codex plugin list 'installed' entry has no string 'name'"
            )
        entry_marketplace = entry.get("marketplaceName")
        if isinstance(entry_marketplace, str) and entry_marketplace != marketplace:
            continue
        names.add(name)
    return frozenset(names)


@dataclass(frozen=True)
class CodexCliInstalled:
    """Default InstalledPlugins: queries the Codex CLI for its installed set.

    Reads the authoritative installed set from `codex plugin list --json
    --marketplace <marketplace>` rather than from `~/.codex/config.toml`, so a
    changed CLI contract surfaces as a parse failure instead of a silent misread.
    """

    runner: CommandRunner = run_command_capture

    def installed_plugins(self, marketplace: str) -> frozenset[str]:
        result = self.runner([*CODEX_LIST_COMMAND, marketplace])
        if result.returncode != 0:
            raise InstalledSetError(
                f"codex plugin list exited {result.returncode} for marketplace {marketplace}"
            )
        return parse_installed_plugins(result.stdout or "", marketplace)


def preserve_during_upgrade(
    marketplace: str = DEFAULT_MARKETPLACE,
    *,
    cache_root: Path | None = None,
    runner: CommandRunner = run_command,
    dry_run: bool = False,
    history: PluginHistory | None = None,
    installed: InstalledPlugins | None = None,
) -> CachePreservationResult:
    """Run the marketplace upgrade and reconcile the cache against history.

    When an ``installed`` provider is supplied and this is not a dry run,
    preservation is scoped to the plugins Codex reports as installed: a plugin
    present in the working tree but absent from the installed set has its entire
    cache directory pruned, the same treatment as a working-tree-absent orphan.
    The recipe's ``main`` supplies the real ``CodexCliInstalled`` provider. A dry
    run skips the installed-set query, so the preview needs no Codex CLI present
    and mutates nothing; when ``installed`` is ``None`` no scoping is applied
    either. In both cases every working-tree plugin is treated as wanted.
    """
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
            upgrade_returncode=upgrade_result.returncode,
        )

    marketplace_dir = resolved_cache_root / marketplace
    working_tree_plugins = resolved_history.working_tree_plugins()

    if installed is not None and not dry_run:
        # Query the installed set before the first prune so the recipe is
        # all-or-nothing: a failed or unrecognized query raises here and no cache
        # directory has been touched, so a degraded signal never drives a deletion.
        installed_set = installed.installed_plugins(marketplace)
        wanted = working_tree_plugins & installed_set
    else:
        # A dry run reports planned changes without querying the installed set, so
        # the preview needs no Codex CLI present and mutates nothing; it treats
        # every working-tree plugin as wanted. Absent an installed provider, no
        # scoping is applied either.
        wanted = working_tree_plugins

    # A cache directory for any plugin outside the wanted set is pruned in full --
    # a working-tree-absent orphan and a not-installed plugin are pruned by the
    # same rule.
    pruned_plugins = _prune_orphan_plugins(marketplace_dir, wanted, dry_run=dry_run)

    linked_versions: list[Path] = []
    pruned_links: list[Path] = []

    for plugin in sorted(wanted):
        plugin_dir = marketplace_dir / plugin
        if not plugin_dir.is_dir():
            # Working-tree plugin absent from the Codex cache: nothing to reconcile.
            continue
        in_window = resolved_history.published_versions(plugin)
        current_version = resolved_history.current_version(plugin)
        current_real = _current_real_version_dir(plugin_dir, current_version)
        if current_real is None:
            # The upgrade exited successfully without materializing the current
            # version as a real directory. No compatibility symlink can point at
            # current content, so remove every compatibility symlink for the
            # plugin -- leaving only real directories -- rather than let any
            # version resolve to a non-current directory. validate_install reports
            # the absent current version.
            pruned_links.extend(_prune_all_symlinks(plugin_dir, dry_run=dry_run))
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


def _current_real_version_dir(
    plugin_dir: Path, current_version: str | None
) -> Path | None:
    if current_version is None:
        return None
    candidate = plugin_dir / current_version
    if candidate.is_dir() and not candidate.is_symlink():
        return candidate
    return None


def _prune_all_symlinks(plugin_dir: Path, *, dry_run: bool) -> list[Path]:
    pruned: list[Path] = []
    for entry in sorted(plugin_dir.iterdir()):
        if not entry.is_symlink():
            # Real version directories are left alone -- only Codex creates or
            # removes them, and removing them risks data loss.
            continue
        if not dry_run:
            entry.unlink()
        pruned.append(entry)
    return pruned


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
    # preserve_during_upgrade skips the query on a dry run, so a dry run never
    # shells out to the Codex CLI even though the provider is constructed here.
    try:
        result = preserve_during_upgrade(
            args.marketplace,
            cache_root=args.cache_root,
            dry_run=args.dry_run,
            history=history,
            installed=CodexCliInstalled(),
        )
    except InstalledSetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
