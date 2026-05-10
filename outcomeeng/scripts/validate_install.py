"""Validate that marketplace installs reflect the current source versions.

After ``just push-marketplace`` runs, checks that:

1. Each plugin's current version (from ``plugins/*/.claude-plugin/plugin.json``)
   exists as a real directory in the Claude Code plugin cache.
2. Each plugin's current version exists as a real directory in the Codex plugin
   cache (for plugins present there).
3. No symlinks in either cache are older than ``--max-age-days`` (default 7).

Also prints every cached version for each plugin so the caller can see at a
glance what is live, what is a compatibility symlink, and which version is
current.

Usage::

    uv run python -m outcomeeng.scripts.validate_install [marketplace]

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
DEFAULT_MAX_AGE_DAYS = 7
SECONDS_PER_DAY = 24 * 60 * 60


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
    manifest = (
        codex_marketplace_clone_root(marketplace)
        / "plugins"
        / plugin
        / ".claude-plugin"
        / "plugin.json"
    )
    try:
        data = json.loads(manifest.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    version = data.get("version")
    return version if isinstance(version, str) else None


def current_versions(repo_root: Path) -> dict[str, str]:
    """Map plugin name → version from each plugins/*/.claude-plugin/plugin.json."""
    versions: dict[str, str] = {}
    plugins_dir = repo_root / "plugins"
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
    """Return all version directories for a plugin, sorted by version string."""
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
    return sorted(entries, key=lambda e: e.version)


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


@dataclass
class ValidationResult:
    """Outcome of a validate_install run.

    Errors fail the build; warnings inform the caller without changing exit code.
    The dataclass is constructed once inside `validate()` and never mutated by
    callers — `frozen=True` would mislead because the list fields stay mutable.
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
            errors=[f"No plugins found under {resolved_root / 'plugins'}"]
        )

    errors: list[str] = []
    warnings: list[str] = []
    claude = claude_cache_override or claude_cache_root()
    codex = codex_cache_override or codex_cache_root()
    published_for = codex_marketplace_version or (
        lambda plugin: read_codex_marketplace_version(marketplace, plugin)
    )

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
        # version must be present as a real directory — UNLESS the Codex
        # marketplace clone publishes a different version. That divergence
        # means the marketplace's tracked branch and the working tree are out
        # of sync, which is structural (e.g., feature-branch development), not
        # a fault. Verify the published version is present instead.
        if (codex / marketplace / plugin).exists():
            published = published_for(plugin)
            if published is not None and published != version:
                warnings.append(
                    f"MISMATCH  {plugin}  working-tree {version} vs marketplace "
                    f"clone {published} — verifying clone version in cache"
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
        suffix = (
            f" with {len(result.warnings)} warning(s)"
            if len(result.warnings) > 1
            else " with 1 warning"
        )
        print(f"✔ {len(versions)} plugin(s) — checks passed{suffix}")
    else:
        print(f"✔ {len(versions)} plugin(s) — all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
