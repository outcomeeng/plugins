"""Harnesses for Codex cache reconciliation tests."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.marketplace_sources import (
    CODEX_PLUGIN_MANIFEST,
    DEFAULT_MARKETPLACE,
    DIST_CODEX_PLUGINS_DIR,
)


@dataclass(frozen=True)
class CodexCacheWorkspace:
    repo_root: Path
    cache_root: Path


@contextmanager
def codex_cache_workspace() -> Iterator[CodexCacheWorkspace]:
    """Create an isolated repository/cache pair for one generated example."""
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        yield CodexCacheWorkspace(
            repo_root=workspace / "repo",
            cache_root=workspace / "cache",
        )


def write_plugin_root(
    cache_root: Path,
    plugin: str,
    version: str,
    text: str,
) -> None:
    plugin_root = cache_root / DEFAULT_MARKETPLACE / plugin / version
    skill_file = plugin_root / "skills" / "contextualize" / "SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(text)
    manifest = plugin_root / CODEX_PLUGIN_MANIFEST
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"name": plugin, "version": version}))


def write_dist_codex_manifest(
    repo_root: Path,
    plugin: str,
    version: str,
) -> None:
    manifest = repo_root / DIST_CODEX_PLUGINS_DIR / plugin / CODEX_PLUGIN_MANIFEST
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"name": plugin, "version": version}))


__all__ = [
    "CodexCacheWorkspace",
    "codex_cache_workspace",
    "write_dist_codex_manifest",
    "write_plugin_root",
]
