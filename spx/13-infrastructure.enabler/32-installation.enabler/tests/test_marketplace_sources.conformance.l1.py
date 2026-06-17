"""Level 1 conformance tests for local marketplace source discovery.

The maintainer sync path reads the configured Claude and Codex marketplace
sources before refreshing Codex plugins. These tests pin the JSON contract and
the local-source gate without invoking either runtime CLI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from outcomeeng.distribution.marketplace_sources import (
    CODEX_PLUGIN_MANIFEST,
    DEFAULT_MARKETPLACE,
    DIST_CODEX_PLUGINS_DIR,
    MarketplaceSourceError,
    available_codex_plugins,
    parse_claude_marketplace_sources,
    parse_codex_marketplace_sources,
    require_matching_local_sources,
)


def test_parse_codex_marketplace_sources_accepts_local_source(
    tmp_path: Path,
) -> None:
    marketplace_root = tmp_path / "marketplace"
    payload = json.dumps(
        [
            {
                "name": DEFAULT_MARKETPLACE,
                "sourceType": "local",
                "path": str(marketplace_root),
            }
        ]
    )

    sources = parse_codex_marketplace_sources(payload)

    assert sources[DEFAULT_MARKETPLACE].source_type == "local"
    assert sources[DEFAULT_MARKETPLACE].path == marketplace_root


def test_parse_codex_marketplace_sources_accepts_nested_local_source(
    tmp_path: Path,
) -> None:
    marketplace_root = tmp_path / "marketplace"
    installed_root = tmp_path / "installed"
    payload = json.dumps(
        {
            "marketplaces": [
                {
                    "name": DEFAULT_MARKETPLACE,
                    "root": str(installed_root),
                    "marketplaceSource": {
                        "sourceType": "local",
                        "source": str(marketplace_root),
                    },
                }
            ]
        }
    )

    sources = parse_codex_marketplace_sources(payload)

    assert sources[DEFAULT_MARKETPLACE].source_type == "local"
    assert sources[DEFAULT_MARKETPLACE].path == marketplace_root


def test_parse_claude_marketplace_sources_normalizes_directory_source(
    tmp_path: Path,
) -> None:
    marketplace_root = tmp_path / "marketplace"
    payload = json.dumps(
        [
            {
                "name": DEFAULT_MARKETPLACE,
                "source": "Directory",
                "path": str(marketplace_root),
            }
        ]
    )

    sources = parse_claude_marketplace_sources(payload)

    assert sources[DEFAULT_MARKETPLACE].source_type == "local"
    assert sources[DEFAULT_MARKETPLACE].path == marketplace_root


def test_parse_codex_marketplace_sources_accepts_nested_git_source() -> None:
    payload = json.dumps(
        {
            "marketplaces": [
                {
                    "name": DEFAULT_MARKETPLACE,
                    "root": "/Users/example/.codex/.tmp/marketplaces/outcomeeng",
                    "marketplaceSource": {
                        "sourceType": "git",
                        "source": "https://github.com/outcomeeng/plugins.git",
                    },
                }
            ]
        }
    )

    sources = parse_codex_marketplace_sources(payload)

    assert sources[DEFAULT_MARKETPLACE].source_type == "git"
    assert (
        sources[DEFAULT_MARKETPLACE].url == "https://github.com/outcomeeng/plugins.git"
    )


def test_parse_codex_marketplace_sources_accepts_empty_marketplace_array() -> None:
    sources = parse_codex_marketplace_sources(json.dumps({"marketplaces": []}))

    assert sources == {}


def test_require_matching_local_sources_rejects_git_backed_codex(
    tmp_path: Path,
) -> None:
    marketplace_root = tmp_path / "marketplace"
    claude_sources = parse_claude_marketplace_sources(
        json.dumps(
            [
                {
                    "name": DEFAULT_MARKETPLACE,
                    "source": "Directory",
                    "path": str(marketplace_root),
                }
            ]
        )
    )
    codex_sources = parse_codex_marketplace_sources(
        json.dumps(
            [
                {
                    "name": DEFAULT_MARKETPLACE,
                    "sourceType": "git",
                    "url": "https://github.com/outcomeeng/plugins.git",
                }
            ]
        )
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        require_matching_local_sources(
            DEFAULT_MARKETPLACE,
            claude_sources=claude_sources,
            codex_sources=codex_sources,
        )

    message = str(exc_info.value)
    assert DEFAULT_MARKETPLACE in message
    assert "local" in message
    assert "git" in message


def test_require_matching_local_sources_rejects_path_mismatch(
    tmp_path: Path,
) -> None:
    claude_root = tmp_path / "claude-marketplace"
    codex_root = tmp_path / "codex-marketplace"
    claude_sources = parse_claude_marketplace_sources(
        json.dumps(
            [
                {
                    "name": DEFAULT_MARKETPLACE,
                    "source": "Directory",
                    "path": str(claude_root),
                }
            ]
        )
    )
    codex_sources = parse_codex_marketplace_sources(
        json.dumps(
            [
                {
                    "name": DEFAULT_MARKETPLACE,
                    "sourceType": "local",
                    "path": str(codex_root),
                }
            ]
        )
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        require_matching_local_sources(
            DEFAULT_MARKETPLACE,
            claude_sources=claude_sources,
            codex_sources=codex_sources,
        )

    message = str(exc_info.value)
    assert str(claude_root) in message
    assert str(codex_root) in message


def test_available_codex_plugins_are_read_from_dist_codex(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    _write_codex_manifest(repo_root, "zeta", "0.2.0")
    _write_codex_manifest(repo_root, "alpha", "0.1.0")
    (repo_root / DIST_CODEX_PLUGINS_DIR / "missing-manifest").mkdir(parents=True)

    plugins = available_codex_plugins(repo_root)

    assert [(plugin.name, plugin.version) for plugin in plugins] == [
        ("alpha", "0.1.0"),
        ("zeta", "0.2.0"),
    ]


def _write_codex_manifest(repo_root: Path, plugin: str, version: str) -> None:
    manifest = repo_root / DIST_CODEX_PLUGINS_DIR / plugin / CODEX_PLUGIN_MANIFEST
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": plugin, "version": version}))
