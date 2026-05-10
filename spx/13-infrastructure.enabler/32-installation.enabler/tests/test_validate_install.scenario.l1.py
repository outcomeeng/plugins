"""Level 1 installation scenarios for validate_install's feature-branch lag tolerance.

When a working-tree plugin manifest bumps to a new version on a feature branch but
the Codex marketplace clone (which tracks the marketplace's published branch) is
still on the prior version, the new version directory is absent from the Codex
cache by design. validate_install demotes that absence to a warning rather than
treating it as a hard error.
"""

from __future__ import annotations

import json
from pathlib import Path

from outcomeeng.scripts import validate_install

MARKETPLACE_NAME = "outcomeeng"
PLUGIN_NAME = "demo-plugin"
WORKING_TREE_VERSION = "0.2.0"
PUBLISHED_VERSION = "0.1.0"


def _write_manifest(repo_root: Path, plugin: str, version: str) -> None:
    manifest = repo_root / "plugins" / plugin / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": plugin, "version": version}))


def _seed_cache(cache_root: Path, plugin: str, version: str) -> None:
    plugin_dir = cache_root / MARKETPLACE_NAME / plugin / version
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "marker.txt").write_text("seed")


def test_lagging_codex_marketplace_version_emits_warning_not_error(
    tmp_path: Path,
) -> None:
    """When the Codex marketplace clone publishes an older version than the working tree,
    the missing newer-version directory is reported as a warning that names the plugin
    and both versions; the validation result records zero errors."""
    repo_root = tmp_path / "repo"
    codex_cache = tmp_path / "codex_cache"
    _write_manifest(repo_root, PLUGIN_NAME, WORKING_TREE_VERSION)
    _seed_cache(codex_cache, PLUGIN_NAME, PUBLISHED_VERSION)

    def published_version(plugin: str) -> str | None:
        return PUBLISHED_VERSION if plugin == PLUGIN_NAME else None

    result = validate_install.validate(
        MARKETPLACE_NAME,
        repo_root=repo_root,
        codex_cache_override=codex_cache,
        claude_cache_override=tmp_path / "empty_claude_cache",
        codex_marketplace_version=published_version,
    )

    assert result.errors == [], f"unexpected errors: {result.errors}"
    assert len(result.warnings) == 1, (
        f"expected one warning, got {len(result.warnings)}: {result.warnings}"
    )
    warning = result.warnings[0]
    assert PLUGIN_NAME in warning
    assert WORKING_TREE_VERSION in warning
    assert PUBLISHED_VERSION in warning


def test_codex_cache_missing_published_version_is_an_error(tmp_path: Path) -> None:
    """When the working-tree and marketplace-published versions agree yet the
    Codex cache lacks that version, the missing directory is an error — the
    mismatch tolerance applies only to divergent versions, not to a stale or
    incomplete cache for an in-sync version."""
    repo_root = tmp_path / "repo"
    codex_cache = tmp_path / "codex_cache"
    _write_manifest(repo_root, PLUGIN_NAME, PUBLISHED_VERSION)
    _seed_cache(codex_cache, PLUGIN_NAME, "0.0.1")

    def published_version(plugin: str) -> str | None:
        return PUBLISHED_VERSION if plugin == PLUGIN_NAME else None

    result = validate_install.validate(
        MARKETPLACE_NAME,
        repo_root=repo_root,
        codex_cache_override=codex_cache,
        claude_cache_override=tmp_path / "empty_claude_cache",
        codex_marketplace_version=published_version,
    )

    assert result.warnings == [], f"unexpected warnings: {result.warnings}"
    assert len(result.errors) == 1
    assert PUBLISHED_VERSION in result.errors[0]
