"""Refresh installed Codex plugins and reconcile compatibility cache links.

The maintainer refresh path requires Codex to use the same local marketplace
source as Claude Code, reinstalls each installed plugin from that local source,
then reconciles the cache for each refreshed plugin. The symlink target is the
complete real cache directory named with the version Codex reports as installed
for that plugin. Every version already present in the cache other than the
installed one becomes a symlink pointing at it -- a present version is never
removed for falling outside the publication window, so a session started on it
keeps resolving its advertised skill cache path. Versions published within the
configured window (default ten days) but absent from the cache are recreated as
symlinks for chain recovery, and plugins absent from the refreshed set have
their cache directory pruned in full. Each preserved symlink's modification time
is refreshed on every run so a stale-symlink check measures time since the last
reconciliation, not time since publication. When refresh leaves no complete real
directory for the Codex-reported installed version, every compatibility symlink
for the plugin is removed and none is created -- a symlink to a non-current
directory would resolve a version to stale content. The preservation set is
derived from the versions present in the cache and the published git history,
not from a hardcoded list. A single bypassed recipe invocation has no permanent
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

from outcomeeng.distribution.marketplace_sources import (
    CODEX_PLUGIN_MANIFEST as _CODEX_PLUGIN_MANIFEST,
    DEFAULT_MARKETPLACE as _DEFAULT_MARKETPLACE,
    MarketplaceSourceError,
    available_codex_plugins,
    configured_local_marketplace_root,
)

DEFAULT_WINDOW_DAYS = 10
CODEX_PLUGIN_ADD_COMMAND = ("codex", "plugin", "add")
CODEX_LIST_COMMAND = ("codex", "plugin", "list", "--json", "--marketplace")
SOURCE_PLUGINS_DIR = Path("src") / "plugins"

type MarketplaceRootResolver = Callable[[str], Path]


class CommandRunner(Protocol):
    """Runs a Codex command, optionally from a scoped working directory."""

    def __call__(
        self, command: list[str], *, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]: ...


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
        # falls outside the window. It belongs in the published-window set even
        # when the live target comes from Codex's installed-version report.
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
class CacheRefreshResult:
    """Observable results from one local Codex refresh wrapper run."""

    linked_versions: tuple[Path, ...]
    pruned_links: tuple[Path, ...]
    pruned_plugins: tuple[str, ...]
    refresh_returncode: int


def default_cache_root() -> Path:
    return Path.home() / ".codex" / "plugins" / "cache"


def run_command(
    command: list[str], *, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command, check=False, text=True, capture_output=True, cwd=cwd
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result


def run_command_capture(
    command: list[str], *, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True, capture_output=True, cwd=cwd)


class InstalledSetError(RuntimeError):
    """The Codex installed-set query failed or returned an unrecognized shape.

    Raised rather than returning an empty set so a failed query is never mistaken
    for "no plugins installed" -- the latter would prune every cache directory.
    Preservation propagates this to abort before any cache mutation.
    """


class InstalledPlugins(Protocol):
    """Source-of-truth for which plugins Codex considers installed."""

    def installed_plugin_versions(self, marketplace: str) -> dict[str, str]: ...


def parse_installed_plugin_versions(payload: str, marketplace: str) -> dict[str, str]:
    """Extract installed plugin name to version for `marketplace` from `codex plugin
    list --json` output.

    The contract is the CLI's documented shape: a JSON object with an ``installed``
    array whose entries each carry string ``name`` and ``version`` fields and may
    carry a ``marketplaceName``. Entries naming a different marketplace are excluded
    so the set is scoped even when the caller omits the ``--marketplace`` filter. Any
    departure from the contract -- unparseable text, a non-object payload, a missing
    or non-list ``installed`` key, or an entry without string ``name`` and
    ``version`` fields -- raises ``InstalledSetError`` rather than yielding a silent
    empty set or stale target.
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
    versions: dict[str, str] = {}
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
        version = entry.get("version")
        if not isinstance(version, str):
            raise InstalledSetError(
                "codex plugin list 'installed' entry has no string 'version'"
            )
        entry_marketplace = entry.get("marketplaceName")
        if isinstance(entry_marketplace, str) and entry_marketplace != marketplace:
            continue
        versions[name] = version
    return versions


@dataclass(frozen=True)
class CodexCliInstalled:
    """Default InstalledPlugins: queries the Codex CLI for installed versions.

    Reads the authoritative installed set and resolved versions from `codex plugin
    list --json --marketplace <marketplace>` rather than from
    `~/.codex/config.toml`, so a changed CLI contract surfaces as a parse failure
    instead of a silent misread or stale target.
    """

    runner: CommandRunner = run_command_capture

    def installed_plugin_versions(self, marketplace: str) -> dict[str, str]:
        result = self.runner([*CODEX_LIST_COMMAND, marketplace])
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            detail = f": {stderr}" if stderr else ""
            raise InstalledSetError(
                f"codex plugin list exited {result.returncode} "
                f"for marketplace {marketplace}{detail}"
            )
        return parse_installed_plugin_versions(result.stdout or "", marketplace)


def refresh_installed_plugins(
    marketplace: str = _DEFAULT_MARKETPLACE,
    *,
    cache_root: Path | None = None,
    repo_root: Path | None = None,
    runner: CommandRunner = run_command,
    dry_run: bool = False,
    history: PluginHistory | None = None,
    installed: InstalledPlugins | None = None,
) -> CacheRefreshResult:
    """Refresh installed local Codex plugins and reconcile the cache against history.

    When an ``installed`` provider is supplied and this is not a dry run,
    refresh is scoped to generated Codex plugins exposed under ``dist/codex``.
    The installed-set provider supplies resolved versions for post-refresh cache
    reconciliation; it does not decide which generated plugins are refreshed.
    The recipe's ``main`` supplies the real ``CodexCliInstalled`` provider. A dry
    run skips the installed-set query and plugin add commands, so the preview
    needs no Codex CLI present and mutates nothing; when ``installed`` is ``None``
    no scoping is applied either. In both cases every working-tree plugin is
    treated as wanted.
    """
    resolved_cache_root = cache_root if cache_root is not None else default_cache_root()
    resolved_repo_root = repo_root if repo_root is not None else Path.cwd()
    resolved_history = (
        history
        if history is not None
        else GitPluginHistory(repo_root=resolved_repo_root)
    )

    marketplace_dir = resolved_cache_root / marketplace
    working_tree_plugins = resolved_history.working_tree_plugins()
    refresh_returncode = 0
    prune_orphan_plugins = True

    if installed is not None and not dry_run:
        # Query the installed set before the first prune so the recipe is
        # all-or-nothing: a failed or unrecognized query raises here and no cache
        # directory has been touched, so a degraded signal never drives a deletion.
        installed_versions = installed.installed_plugin_versions(marketplace)
        addable_plugins = {
            plugin.name for plugin in available_codex_plugins(resolved_repo_root)
        }
        wanted = working_tree_plugins & addable_plugins
        refreshed_plugins: set[str] = set()
        for plugin in sorted(wanted):
            refresh_result = runner(
                [*CODEX_PLUGIN_ADD_COMMAND, f"{plugin}@{marketplace}"]
            )
            if refresh_result.returncode != 0:
                refresh_returncode = refresh_result.returncode
                prune_orphan_plugins = False
                break
            refreshed_plugins.add(plugin)
        if refreshed_plugins:
            # Codex reports the post-add version as the installed target. Re-query
            # after successful local refreshes so reconciliation targets the newly
            # materialized real cache root instead of the pre-refresh snapshot.
            installed_versions = installed.installed_plugin_versions(marketplace)
            if refresh_returncode != 0:
                wanted &= frozenset(refreshed_plugins)
        else:
            wanted = frozenset()
    else:
        # A dry run reports planned changes without querying the installed set, so
        # the preview needs no Codex CLI present and mutates nothing; it treats
        # every working-tree plugin as wanted. Absent an installed provider, no
        # scoping is applied either.
        installed_versions = {}
        wanted = working_tree_plugins

    # A cache directory for any plugin outside the wanted set is pruned in full --
    # a working-tree-absent orphan and a not-installed plugin are pruned by the
    # same rule.
    pruned_plugins = (
        _prune_orphan_plugins(marketplace_dir, wanted, dry_run=dry_run)
        if prune_orphan_plugins
        else []
    )

    linked_versions: list[Path] = []
    pruned_links: list[Path] = []

    for plugin in sorted(wanted):
        plugin_dir = marketplace_dir / plugin
        if not plugin_dir.is_dir():
            # Working-tree plugin absent from the Codex cache: nothing to reconcile.
            continue
        in_window = resolved_history.published_versions(plugin)
        current_version = installed_versions.get(
            plugin
        ) or resolved_history.current_version(plugin)
        current_real = _current_real_version_dir(plugin_dir, current_version)
        if current_real is None:
            # The refresh completed without materializing the current
            # version as a complete real directory. No compatibility symlink can
            # point at current content, so remove every compatibility symlink and
            # every non-target real directory for the plugin rather than let any
            # version resolve to non-current content. validate_install reports the
            # absent or incomplete current version.
            pruned_links.extend(_prune_all_symlinks(plugin_dir, dry_run=dry_run))
            pruned_links.extend(
                _prune_non_target_real_dirs(
                    plugin_dir,
                    current_version,
                    keep_versions=frozenset(),
                    dry_run=dry_run,
                )
            )
            continue

        # Preserve every version already present in the cache by retargeting it to
        # a symlink at the installed version, and recreate any in-window version
        # absent from the cache (chain recovery). A present version is never pruned
        # for falling outside the publication window, so a session started on that
        # version keeps resolving its advertised skill cache path.
        # Only versioned directories and symlinks are cache entries; skip a stray
        # regular file (e.g. .DS_Store) so it is never treated as a version.
        present_versions = {
            entry.name
            for entry in plugin_dir.iterdir()
            if entry.is_symlink() or entry.is_dir()
        }
        ensure_versions = (present_versions | in_window) - {current_real.name}
        linked_versions.extend(
            _ensure_compatibility_symlinks(
                plugin_dir, current_real, ensure_versions, dry_run=dry_run
            )
        )

    return CacheRefreshResult(
        linked_versions=tuple(linked_versions),
        pruned_links=tuple(pruned_links),
        pruned_plugins=tuple(pruned_plugins),
        refresh_returncode=refresh_returncode,
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
    if (
        candidate.is_dir()
        and not candidate.is_symlink()
        and _is_complete_plugin_root(candidate)
    ):
        return candidate
    return None


def _is_complete_plugin_root(path: Path) -> bool:
    return (path / _CODEX_PLUGIN_MANIFEST).is_file()


def _prune_all_symlinks(plugin_dir: Path, *, dry_run: bool) -> list[Path]:
    pruned: list[Path] = []
    for entry in sorted(plugin_dir.iterdir()):
        if not entry.is_symlink():
            # Real directories are pruned by the caller once the target version
            # is known; this step only removes stale compatibility links.
            continue
        if not dry_run:
            entry.unlink()
        pruned.append(entry)
    return pruned


def _prune_non_target_real_dirs(
    plugin_dir: Path,
    target_version: str | None,
    *,
    keep_versions: frozenset[str],
    dry_run: bool,
) -> list[Path]:
    pruned: list[Path] = []
    for entry in sorted(plugin_dir.iterdir()):
        if entry.is_symlink() or not entry.is_dir():
            continue
        if target_version is not None and entry.name == target_version:
            continue
        if entry.name in keep_versions and target_version is not None:
            # In-window, non-target versions must become symlinks to the target
            # later in the reconciliation pass.
            continue
        if not dry_run:
            shutil.rmtree(entry)
        pruned.append(entry)
    return pruned


def _ensure_compatibility_symlinks(
    plugin_dir: Path,
    current_real: Path,
    versions: set[str],
    *,
    dry_run: bool,
) -> list[Path]:
    linked: list[Path] = []
    for version in sorted(versions):
        if version == current_real.name:
            continue
        target_path = plugin_dir / version
        if _is_symlink_to(target_path, current_real):
            # Already correct. Refresh the symlink's own modification time so a
            # stale-symlink check measures time since this reconciliation rather
            # than time since the version was published -- without the refresh an
            # infrequently-bumped plugin's preserved links would age past the
            # stale cutoff and fail validation.
            if not dry_run:
                os.utime(target_path, follow_symlinks=False)
            linked.append(target_path)
            continue
        if os.path.lexists(target_path):
            if not target_path.is_symlink():
                if not dry_run:
                    shutil.rmtree(target_path)
            elif not dry_run:
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


def _resolve_refresh_repo_root(
    marketplace: str,
    *,
    explicit_repo_root: Path | None,
    dry_run: bool,
    marketplace_root_resolver: MarketplaceRootResolver,
) -> Path:
    if dry_run:
        return explicit_repo_root if explicit_repo_root is not None else Path.cwd()
    configured_root = marketplace_root_resolver(marketplace)
    if explicit_repo_root is not None and _normalized_path(
        explicit_repo_root
    ) != _normalized_path(configured_root):
        raise MarketplaceSourceError(
            f"--repo-root {explicit_repo_root} does not match configured local "
            f"marketplace root {configured_root}"
        )
    return configured_root


def _normalized_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def main(
    argv: list[str] | None = None,
    *,
    marketplace_root_resolver: MarketplaceRootResolver = configured_local_marketplace_root,
) -> int:
    parser = argparse.ArgumentParser(
        description="Refresh local Codex plugins and reconcile the plugin cache"
    )
    parser.add_argument(
        "marketplace",
        nargs="?",
        default=_DEFAULT_MARKETPLACE,
        help="Marketplace name to refresh",
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
        default=None,
        help="Git working tree root for the marketplace repository",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned changes without refreshing plugins or mutating cache",
    )
    args = parser.parse_args(argv)

    try:
        repo_root = _resolve_refresh_repo_root(
            args.marketplace,
            explicit_repo_root=args.repo_root,
            dry_run=args.dry_run,
            marketplace_root_resolver=marketplace_root_resolver,
        )
    except MarketplaceSourceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    history = GitPluginHistory(repo_root=repo_root, window_days=args.window_days)
    # refresh_installed_plugins skips the query on a dry run, so a dry run never
    # shells out to the Codex CLI even though the provider is constructed here.
    try:
        result = refresh_installed_plugins(
            args.marketplace,
            cache_root=args.cache_root,
            repo_root=repo_root,
            dry_run=args.dry_run,
            history=history,
            installed=CodexCliInstalled(),
        )
    except InstalledSetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if result.refresh_returncode != 0:
        print(
            f"error: Codex plugin refresh failed with exit code {result.refresh_returncode}",
            file=sys.stderr,
        )
        return result.refresh_returncode

    print(
        "Codex local refresh: "
        f"{len(result.linked_versions)} compatibility link(s), "
        f"{len(result.pruned_links)} pruned link(s), "
        f"{len(result.pruned_plugins)} pruned plugin(s)"
    )
    return 0


__all__ = [
    "CODEX_LIST_COMMAND",
    "CODEX_PLUGIN_ADD_COMMAND",
    "DEFAULT_WINDOW_DAYS",
    "CacheRefreshResult",
    "CodexCliInstalled",
    "CommandRunner",
    "GitPluginHistory",
    "InstalledPlugins",
    "InstalledSetError",
    "PluginHistory",
    "default_cache_root",
    "main",
    "parse_installed_plugin_versions",
    "refresh_installed_plugins",
    "run_command",
    "run_command_capture",
]


if __name__ == "__main__":
    raise SystemExit(main())
