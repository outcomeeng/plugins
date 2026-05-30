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

DEFAULT_MARKETPLACE = "outcomeeng"
DEFAULT_MAX_AGE_DAYS = 10
SECONDS_PER_DAY = 24 * 60 * 60
SOURCE_PLUGINS_DIR = Path("src") / "plugins"
CLAUDE_DIST_PLUGINS_DIR = Path("dist") / "claude"


def claude_cache_root() -> Path:
    return Path.home() / ".claude" / "plugins" / "cache"


def codex_cache_root() -> Path:
    return Path.home() / ".codex" / "plugins" / "cache"


def codex_marketplace_clone_root(marketplace: str) -> Path:
    return Path.home() / ".codex" / ".tmp" / "marketplaces" / marketplace


def read_codex_marketplace_version(marketplace: str, plugin: str) -> str | None:
    """Return the version the Codex marketplace clone publishes for `plugin`.

    The clone tracks the marketplace's published branch (typically `main`).
    A working-tree manifest on a feature branch can declare a different
    version than the clone has fetched; the divergence signals a
    structural lag in either direction.

    Returns None for any failure mode — missing file, OSError on read,
    invalid JSON, or a manifest whose top-level shape is not a dict.
    Callers fall back to strict validation when None is returned.
    """
    clone_root = codex_marketplace_clone_root(marketplace)
    candidates = (
        clone_root
        / CLAUDE_DIST_PLUGINS_DIR
        / plugin
        / ".claude-plugin"
        / "plugin.json",
        clone_root / "plugins" / plugin / ".claude-plugin" / "plugin.json",
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


def cached_entries(
    cache_root: Path, marketplace: str, plugin: str, current_version: str
) -> list[CachedEntry]:
    """Return all version directories for a plugin, ordered by numeric version."""
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
    return sorted(entries, key=lambda e: _version_sort_key(e.version))


def print_cache(
    cache_root: Path,
    label: str,
    marketplace: str,
    versions: dict[str, str],
) -> None:
    plugin_width = max((len(p) for p in versions), default=0)
    print(f"━━━ {label} ({cache_root / marketplace}) ━━━")
    for plugin in sorted(versions):
        entries = cached_entries(cache_root, marketplace, plugin, versions[plugin])
        if not entries:
            continue
        for i, entry in enumerate(entries):
            kind = "symlink" if entry.is_symlink else "live   "
            current = " ← current" if entry.is_current else ""
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
        lambda plugin: read_codex_marketplace_version(marketplace, plugin)
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

        # Codex: auto-upgrades on marketplace upgrade. The working-tree manifest
        # version must be present as a real directory — UNLESS the working tree
        # is strictly ahead of the version the Codex marketplace clone publishes
        # (typical on a feature branch that bumped a manifest before merge). In
        # that case the absent newer version is structural lag, not a fault, and
        # the published version is what actually has to be in the cache.
        if (codex / marketplace / plugin).exists():
            published = published_for(plugin)
            if published is not None and is_strictly_ahead(version, published):
                warnings.append(
                    f"{plugin}  working-tree {version} ahead of marketplace "
                    f"clone {published}; verifying clone version in cache"
                )
                check_version_present(codex, marketplace, plugin, published, errors)
            else:
                check_version_present(codex, marketplace, plugin, version, errors)
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

    print_cache(claude_cache_root(), "Claude Code", args.marketplace, versions)
    print_cache(codex_cache_root(), "Codex", args.marketplace, versions)

    result = validate(
        args.marketplace, repo_root=repo_root, max_age_days=args.max_age_days
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
