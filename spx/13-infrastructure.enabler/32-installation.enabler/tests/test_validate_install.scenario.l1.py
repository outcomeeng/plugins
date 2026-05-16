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

import pytest

from outcomeeng.validation import install as validate_install

MARKETPLACE_NAME = "outcomeeng"
PLUGIN_NAME = "demo-plugin"
ORPHAN_PLUGIN_NAME = "removed-plugin"
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
    ahead-only tolerance does not cover an in-sync version with an incomplete cache."""
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


def test_missing_codex_marketplace_manifest_falls_back_to_strict_check(
    tmp_path: Path,
) -> None:
    """When the Codex marketplace clone has no manifest for the plugin (the lookup
    returns None), validate_install applies strict validation against the working-tree
    version — no warning, and a missing directory is an error."""
    repo_root = tmp_path / "repo"
    codex_cache = tmp_path / "codex_cache"
    _write_manifest(repo_root, PLUGIN_NAME, WORKING_TREE_VERSION)
    _seed_cache(codex_cache, PLUGIN_NAME, PUBLISHED_VERSION)

    def no_published_version(plugin: str) -> str | None:
        return None

    result = validate_install.validate(
        MARKETPLACE_NAME,
        repo_root=repo_root,
        codex_cache_override=codex_cache,
        claude_cache_override=tmp_path / "empty_claude_cache",
        codex_marketplace_version=no_published_version,
    )

    assert result.warnings == [], f"unexpected warnings: {result.warnings}"
    assert len(result.errors) == 1
    assert WORKING_TREE_VERSION in result.errors[0]


def test_main_exits_zero_when_working_tree_ahead_of_marketplace_clone(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """End-to-end through main(): when the working tree advances past the marketplace
    clone, the script exits zero and writes a warning to stderr naming the plugin and
    both versions."""
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(repo)

    _write_manifest(repo, PLUGIN_NAME, WORKING_TREE_VERSION)
    codex_cache = home / ".codex" / "plugins" / "cache"
    _seed_cache(codex_cache, PLUGIN_NAME, PUBLISHED_VERSION)

    clone_manifest = (
        home
        / ".codex"
        / ".tmp"
        / "marketplaces"
        / MARKETPLACE_NAME
        / "plugins"
        / PLUGIN_NAME
        / ".claude-plugin"
        / "plugin.json"
    )
    clone_manifest.parent.mkdir(parents=True)
    clone_manifest.write_text(
        json.dumps({"name": PLUGIN_NAME, "version": PUBLISHED_VERSION})
    )

    exit_code = validate_install.main([MARKETPLACE_NAME])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert PLUGIN_NAME in captured.err
    assert WORKING_TREE_VERSION in captured.err
    assert PUBLISHED_VERSION in captured.err
    assert "warning:" in captured.err


def test_codex_cache_missing_when_working_tree_older_is_an_error(
    tmp_path: Path,
) -> None:
    """When the working-tree manifest is older than the marketplace clone (e.g., after
    reverting a version bump) and the cache lacks that version, the missing directory
    is an error — the ahead-only tolerance does not cover the inverse direction."""
    repo_root = tmp_path / "repo"
    codex_cache = tmp_path / "codex_cache"
    older_version = "0.0.1"
    _write_manifest(repo_root, PLUGIN_NAME, older_version)
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

    assert result.warnings == [], f"unexpected warnings: {result.warnings}"
    assert len(result.errors) == 1
    assert older_version in result.errors[0]


def test_orphan_plugin_in_cache_emits_warning(tmp_path: Path) -> None:
    """When the cache contains a plugin directory absent from the working tree,
    the orphan is reported as a warning that names the plugin; errors are unchanged.
    """
    repo_root = tmp_path / "repo"
    codex_cache = tmp_path / "codex_cache"
    _write_manifest(repo_root, PLUGIN_NAME, PUBLISHED_VERSION)
    _seed_cache(codex_cache, PLUGIN_NAME, PUBLISHED_VERSION)
    _seed_cache(codex_cache, ORPHAN_PLUGIN_NAME, PUBLISHED_VERSION)

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
    orphan_warnings = [w for w in result.warnings if ORPHAN_PLUGIN_NAME in w]
    assert len(orphan_warnings) == 1, (
        f"expected one orphan warning naming {ORPHAN_PLUGIN_NAME}, "
        f"got: {result.warnings}"
    )


@pytest.mark.parametrize(
    ("working_tree", "published", "expected"),
    [
        ("0.2.0", "0.1.0", True),
        ("0.1.0", "0.1.0", False),
        ("0.0.1", "0.1.0", False),
        ("1.0.0", "0.99.99", True),
        # Tuple-prefix semantics: shorter tuples compare component-by-component,
        # so ("1", "0") is strictly greater than ("0", "9", "0").
        ("1.0", "0.9.0", True),
        # ("0", "9") and ("0", "9", "0") compare as () == () then 0==0 then
        # 9==9 then StopIteration on the shorter — Python returns False.
        ("0.9", "0.9.0", False),
        # Non-numeric component (pre-release, build metadata) is undefined ordering;
        # falls back to False so the caller applies strict validation.
        ("0.2.0-alpha", "0.1.0", False),
        ("0.2.0", "abc", False),
        ("", "0.1.0", False),
    ],
)
def test_is_strictly_ahead_compares_dotted_integer_versions(
    working_tree: str, published: str, expected: bool
) -> None:
    """is_strictly_ahead returns True only when working_tree's dotted-integer tuple
    compares strictly greater than published's. Non-numeric components yield False
    (callers fall back to strict validation)."""
    assert validate_install.is_strictly_ahead(working_tree, published) is expected
