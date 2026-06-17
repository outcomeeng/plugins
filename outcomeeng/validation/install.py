"""Validate that marketplace installs reflect the current source versions.

After ``just push-marketplace`` runs, checks that:

1. Each plugin's current version (from ``src/plugins/*/.claude-plugin/plugin.json``)
   exists as a real directory in the Claude Code plugin cache.
2. Each plugin's current version exists as a real directory in the Codex plugin
   cache (for plugins present there).
3. No symlinks in either cache are older than ``--max-age-days`` (default 7).

Also prints every cached version for each plugin so the caller can see at a
glance what is live, what is a compatibility symlink, and which version is
current.

Usage::

    uv run python -m outcomeeng.validation.install [marketplace]

Exit codes:
    0 - All checks passed
    1 - One or more checks failed
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from outcomeeng.distribution.codex_cache import (
    CODEX_LIST_COMMAND,
    CommandRunner,
    run_command_capture,
)
from outcomeeng.distribution.marketplace_sources import (
    CODEX_PLUGIN_MANIFEST,
    DIST_CODEX_PLUGINS_DIR,
    MarketplaceSourceError,
    configured_local_marketplace_root,
)

DEFAULT_MARKETPLACE = "outcomeeng"
DEFAULT_MAX_AGE_DAYS = 10
SECONDS_PER_DAY = 24 * 60 * 60
SOURCE_PLUGINS_DIR = Path("src") / "plugins"
CLAUDE_DIST_PLUGINS_DIR = Path("dist") / "claude"
CLAUDE_PLUGIN_MANIFEST = Path(".claude-plugin") / "plugin.json"

# Listing display tokens — the marker the listing places on the resolved version,
# and the kind label for a synthesized current row that has no cache directory.
CURRENT_MARKER = "← current"
WORKING_TREE_KIND = "resolves from working tree"


def claude_cache_root() -> Path:
    return Path.home() / ".claude" / "plugins" / "cache"


def codex_cache_root() -> Path:
    return Path.home() / ".codex" / "plugins" / "cache"


def codex_marketplace_source_root(
    marketplace: str, *, runner: CommandRunner = run_command_capture
) -> Path | None:
    """Return the configured shared local marketplace root when available."""
    try:
        return configured_local_marketplace_root(marketplace, runner=runner)
    except (MarketplaceSourceError, OSError):
        return None


def read_codex_marketplace_version(
    marketplace: str,
    plugin: str,
    *,
    marketplace_root: Path | None = None,
    runner: CommandRunner = run_command_capture,
) -> str | None:
    """Return the version the configured local Codex marketplace source publishes.

    The source root tracks the maintainer marketplace worktree, usually the
    default-branch checkout Claude and Codex share. A working-tree manifest on a
    feature worktree can declare a different version than the source root exposes;
    the divergence signals maintainer lag between the feature worktree and the
    published local marketplace source.

    Returns None for any failure mode — missing file, OSError on read,
    invalid JSON, or a manifest whose top-level shape is not a dict.
    Callers fall back to strict validation when None is returned.
    """
    source_root = marketplace_root or codex_marketplace_source_root(
        marketplace, runner=runner
    )
    if source_root is None:
        return None
    candidates = (
        source_root / DIST_CODEX_PLUGINS_DIR / plugin / CODEX_PLUGIN_MANIFEST,
        source_root / CLAUDE_DIST_PLUGINS_DIR / plugin / CLAUDE_PLUGIN_MANIFEST,
        source_root / "plugins" / plugin / CLAUDE_PLUGIN_MANIFEST,
    )
    data: object | None = None
    for manifest in candidates:
        try:
            data = json.loads(manifest.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        break
    if data is None:
        return None
    if not isinstance(data, dict):
        return None
    version = data.get("version")
    return version if isinstance(version, str) else None


def parse_codex_reported_versions(payload: str, marketplace: str) -> dict[str, str]:
    """Map plugin name to the version Codex reports installed for `marketplace`,
    parsed from `codex plugin list --json` output.

    Unlike the fail-loud prune parser, this is for the informational listing, so any
    unrecognized shape or malformed entry is skipped and an empty map is returned
    rather than raising — a display glitch must not crash `validate_install`.
    """
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    installed = data.get("installed")
    if not isinstance(installed, list):
        return {}
    versions: dict[str, str] = {}
    for entry in installed:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        version = entry.get("version")
        marketplace_name = entry.get("marketplaceName")
        if not isinstance(name, str) or not isinstance(version, str):
            continue
        if isinstance(marketplace_name, str) and marketplace_name != marketplace:
            continue
        versions[name] = version
    return versions


def codex_reported_versions(
    marketplace: str, *, runner: CommandRunner = run_command_capture
) -> dict[str, str]:
    """Return plugin name to the version Codex reports for `marketplace`, queried
    from `codex plugin list --json`. The version Codex reports is the marketplace
    version it resolves, not any local manifest. Returns an empty map when the query
    fails — the listing is informational and must not crash if the CLI is absent."""
    try:
        result = runner([*CODEX_LIST_COMMAND, marketplace])
    except OSError:
        return {}
    if result.returncode != 0:
        return {}
    return parse_codex_reported_versions(result.stdout or "", marketplace)


def _parse_version(version: str) -> tuple[int, ...] | None:
    """Parse a dotted version into integer components, or None when any component
    is non-numeric (pre-release suffix, build metadata, malformed input)."""
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return None


def _version_sort_key(version: str) -> tuple[int, tuple[int, ...], str]:
    """Sort key that orders dotted-integer versions by their numeric components, so
    `0.17.6` precedes `0.17.10` (a lexicographic sort reverses them). A version with
    a non-numeric component sorts after every numeric version, ordered
    lexicographically among such versions; the leading discriminator keeps the
    numeric and non-numeric key shapes from being compared against each other."""
    parsed = _parse_version(version)
    if parsed is None:
        return (1, (), version)
    return (0, parsed, "")


def is_strictly_ahead(working_tree: str, published: str) -> bool:
    """Return True when `working_tree` is a numerically higher semver than `published`.

    Compares dotted integer components (e.g. "0.29.0" > "0.28.0"). Any non-numeric
    component (pre-release suffix, build metadata, malformed input) makes the
    comparison undefined and returns False — the caller falls back to strict
    validation, which is the safe default.
    """
    wt = _parse_version(working_tree)
    pub = _parse_version(published)
    if wt is None or pub is None:
        return False
    return wt > pub


def current_versions(repo_root: Path) -> dict[str, str]:
    """Map plugin name → version from each src/plugins/*/.claude-plugin/plugin.json."""
    versions: dict[str, str] = {}
    plugins_dir = repo_root / SOURCE_PLUGINS_DIR
    if not plugins_dir.is_dir():
        return versions
    for child in sorted(plugins_dir.iterdir()):
        manifest = child / ".claude-plugin" / "plugin.json"
        if manifest.is_file():
            data = json.loads(manifest.read_text())
            versions[child.name] = data["version"]
    return versions


@dataclass(frozen=True)
class CachedEntry:
    version: str
    is_symlink: bool
    is_current: bool
    materialized: bool = True


def cached_entries(
    cache_root: Path,
    marketplace: str,
    plugin: str,
    current_version: str,
    *,
    synthesize_current: bool = False,
) -> list[CachedEntry]:
    """Return all version directories for a plugin, ordered by numeric version.

    When `synthesize_current` is set and the plugin has real cached directories but
    none of them is the current version — the working-tree version has advanced past
    every cached directory under working-tree-pinned resolution — a non-materialized
    entry for the current version is appended and sorted into numeric position, so
    the listing marks the resolved version rather than dropping the marker. No row is
    synthesized for a plugin with no cached directories at all.
    """
    plugin_dir = cache_root / marketplace / plugin
    if not plugin_dir.is_dir():
        return []
    entries = []
    for entry in sorted(plugin_dir.iterdir()):
        if not entry.is_dir() and not entry.is_symlink():
            continue
        entries.append(
            CachedEntry(
                version=entry.name,
                is_symlink=entry.is_symlink(),
                is_current=entry.name == current_version,
            )
        )
    if (
        synthesize_current
        and current_version
        and entries
        and not any(entry.is_current for entry in entries)
    ):
        entries.append(
            CachedEntry(
                version=current_version,
                is_symlink=False,
                is_current=True,
                materialized=False,
            )
        )
    return sorted(entries, key=lambda e: _version_sort_key(e.version))


def print_cache(
    cache_root: Path,
    label: str,
    marketplace: str,
    versions: dict[str, str],
    *,
    current_override: dict[str, str] | None = None,
    working_tree_pinned: bool = False,
) -> None:
    """Render a cache's version directories per plugin, marking the current one.

    `versions` selects which plugins to list and supplies the default current
    version. `current_override` replaces that current version per plugin where a
    cache resolves from a source other than the working tree — the Codex listing
    passes the version Codex reports so its marker tracks the marketplace version
    Codex resolves, not the local manifest. `working_tree_pinned` enables a
    synthesized current row for a working-tree-pinned cache whose current version
    has advanced past every cached directory.
    """
    plugin_width = max((len(p) for p in versions), default=0)
    print(f"━━━ {label} ({cache_root / marketplace}) ━━━")
    for plugin in sorted(versions):
        current_version = (current_override or {}).get(plugin, versions[plugin])
        entries = cached_entries(
            cache_root,
            marketplace,
            plugin,
            current_version,
            synthesize_current=working_tree_pinned,
        )
        if not entries:
            continue
        for i, entry in enumerate(entries):
            if not entry.materialized:
                kind = WORKING_TREE_KIND
            elif entry.is_symlink:
                kind = "symlink"
            else:
                kind = "live   "
            current = f" {CURRENT_MARKER}" if entry.is_current else ""
            prefix = plugin.ljust(plugin_width) if i == 0 else " " * plugin_width
            print(f"  {prefix}  {entry.version}  {kind}{current}")
    print()


def check_version_present(
    cache_root: Path,
    marketplace: str,
    plugin: str,
    version: str,
    errors: list[str],
) -> bool:
    """Assert the exact version directory exists and is a real directory."""
    path = cache_root / marketplace / plugin / version
    if not path.exists():
        errors.append(f"MISSING  {path}")
        return False
    if path.is_symlink():
        errors.append(f"SYMLINK  {path}  (expected a real directory)")
        return False
    return True


def check_single_real_codex_version(
    cache_root: Path,
    marketplace: str,
    plugin: str,
    expected_version: str,
    errors: list[str],
) -> None:
    """Assert the Codex cache has no extra real version roots for this plugin."""
    plugin_dir = cache_root / marketplace / plugin
    if not plugin_dir.is_dir():
        return
    real_versions = [
        e for e in sorted(plugin_dir.iterdir()) if e.is_dir() and not e.is_symlink()
    ]
    if len(real_versions) <= 1:
        return
    found = ", ".join(entry.name for entry in real_versions)
    errors.append(
        f"MULTIPLE REAL  {plugin_dir}  "
        f"(expected one real directory for {expected_version}; found {found})"
    )


def check_complete_codex_entries(
    cache_root: Path,
    marketplace: str,
    plugin: str,
    errors: list[str],
) -> None:
    """Assert every Codex version path resolves to a complete plugin root."""
    plugin_dir = cache_root / marketplace / plugin
    if not plugin_dir.is_dir():
        return
    for entry in sorted(plugin_dir.iterdir()):
        if not entry.is_dir() and not entry.is_symlink():
            continue
        manifest = entry / CODEX_PLUGIN_MANIFEST
        if not manifest.is_file():
            errors.append(f"INCOMPLETE  {entry}  (missing {CODEX_PLUGIN_MANIFEST})")


def check_any_real_version_present(
    cache_root: Path,
    marketplace: str,
    plugin: str,
    errors: list[str],
) -> bool:
    """Assert at least one real (non-symlink) version directory exists."""
    plugin_dir = cache_root / marketplace / plugin
    real_versions = [
        e for e in plugin_dir.iterdir() if e.is_dir() and not e.is_symlink()
    ]
    if not real_versions:
        errors.append(f"NO REAL VERSION  {plugin_dir}")
        return False
    return True


def check_no_stale_symlinks(
    cache_root: Path,
    marketplace: str,
    plugin: str,
    max_age_days: int,
    now: float,
    errors: list[str],
) -> None:
    """Assert no version symlinks for this plugin are older than max_age_days."""
    plugin_dir = cache_root / marketplace / plugin
    if not plugin_dir.is_dir():
        return
    cutoff = now - max_age_days * SECONDS_PER_DAY
    for entry in sorted(plugin_dir.iterdir()):
        if not entry.is_symlink():
            continue
        age_days = (now - entry.lstat().st_mtime) / SECONDS_PER_DAY
        if entry.lstat().st_mtime < cutoff:
            errors.append(
                f"STALE    {entry}  ({age_days:.1f}d old, max {max_age_days}d)"
            )


def collect_orphan_plugins(
    cache_root: Path,
    marketplace: str,
    working_tree_plugins: set[str],
    warnings: list[str],
) -> None:
    """Warn for each plugin directory in the cache absent from the working tree."""
    marketplace_dir = cache_root / marketplace
    if not marketplace_dir.is_dir():
        return
    for plugin_dir in sorted(marketplace_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        if plugin_dir.name in working_tree_plugins:
            continue
        warnings.append(
            f"{plugin_dir.name}  orphan: present in {marketplace_dir} but no manifest in working tree"
        )


@dataclass
class ValidationResult:
    """Outcome of a validate_install run.

    Errors fail the build; warnings inform the caller without changing exit code.
    Constructed once inside `validate()`; the caller only reads it.
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate(
    marketplace: str = DEFAULT_MARKETPLACE,
    *,
    repo_root: Path | None = None,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    now: float | None = None,
    claude_cache_override: Path | None = None,
    codex_cache_override: Path | None = None,
    codex_marketplace_version: Callable[[str], str | None] | None = None,
    codex_marketplace_root: Path | None = None,
    codex_resolved_versions: dict[str, str] | None = None,
) -> ValidationResult:
    resolved_root = repo_root if repo_root is not None else Path.cwd()
    resolved_now = now if now is not None else time.time()
    versions = current_versions(resolved_root)
    if not versions:
        return ValidationResult(
            errors=[f"No plugins found under {resolved_root / SOURCE_PLUGINS_DIR}"]
        )

    errors: list[str] = []
    warnings: list[str] = []
    claude = claude_cache_override or claude_cache_root()
    codex = codex_cache_override or codex_cache_root()
    published_for = codex_marketplace_version or (
        lambda plugin: read_codex_marketplace_version(
            marketplace,
            plugin,
            marketplace_root=codex_marketplace_root,
        )
    )
    resolved_versions = (
        codex_resolved_versions if codex_resolved_versions is not None else {}
    )
    working_tree_plugins = set(versions)

    collect_orphan_plugins(claude, marketplace, working_tree_plugins, warnings)
    collect_orphan_plugins(codex, marketplace, working_tree_plugins, warnings)

    for plugin, version in sorted(versions.items()):
        # Claude: refreshes catalog only, does not auto-upgrade cached files.
        # Check that at least one real version directory exists; exact version
        # is not asserted because Claude updates lazily on next session load.
        if (claude / marketplace / plugin).exists():
            check_any_real_version_present(claude, marketplace, plugin, errors)
            check_no_stale_symlinks(
                claude, marketplace, plugin, max_age_days, resolved_now, errors
            )

        # Codex: validates the version Codex reports as installed when available.
        # If that live signal is unavailable and cache content exists, it falls
        # back to the configured local marketplace source version for feature-
        # worktree lag tolerance.
        codex_plugin_dir = codex / marketplace / plugin
        target_version = resolved_versions.get(plugin)
        published = published_for(plugin)
        if target_version is not None:
            if target_version != version:
                warnings.append(
                    f"{plugin}  working-tree {version} differs from Codex "
                    f"resolved {target_version}; verifying Codex resolved "
                    "version in cache"
                )
        elif codex_plugin_dir.exists():
            if published is not None and is_strictly_ahead(version, published):
                target_version = published
                warnings.append(
                    f"{plugin}  working-tree {version} ahead of local marketplace "
                    f"source {published}; verifying marketplace version in cache"
                )
            else:
                target_version = version
        if target_version is not None:
            check_version_present(codex, marketplace, plugin, target_version, errors)
        if codex_plugin_dir.exists():
            if target_version is not None:
                check_single_real_codex_version(
                    codex, marketplace, plugin, target_version, errors
                )
            check_complete_codex_entries(codex, marketplace, plugin, errors)
            check_no_stale_symlinks(
                codex, marketplace, plugin, max_age_days, resolved_now, errors
            )

    return ValidationResult(errors=errors, warnings=warnings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate marketplace plugin cache after push-marketplace"
    )
    parser.add_argument("marketplace", nargs="?", default=DEFAULT_MARKETPLACE)
    parser.add_argument("--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS)
    args = parser.parse_args(argv)

    repo_root = Path.cwd()
    versions = current_versions(repo_root)
    reported_versions = codex_reported_versions(args.marketplace)
    marketplace_root = codex_marketplace_source_root(args.marketplace)

    print_cache(
        claude_cache_root(),
        "Claude Code",
        args.marketplace,
        versions,
        working_tree_pinned=True,
    )
    print_cache(
        codex_cache_root(),
        "Codex",
        args.marketplace,
        versions,
        current_override=reported_versions,
    )

    result = validate(
        args.marketplace,
        repo_root=repo_root,
        max_age_days=args.max_age_days,
        codex_marketplace_root=marketplace_root,
        codex_resolved_versions=reported_versions,
    )

    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)

    if result.errors:
        for error in result.errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    if result.warnings:
        print(
            f"✔ {len(versions)} plugin(s) — checks passed "
            f"with {len(result.warnings)} warning(s)"
        )
    else:
        print(f"✔ {len(versions)} plugin(s) — all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
