"""Harnesses for Codex cache reconciliation tests."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from outcomeeng.distribution.codex_cache import CODEX_PLUGIN_ADD_COMMAND
from outcomeeng.distribution.marketplace_sources import (
    CODEX_PLUGIN_MANIFEST,
    DEFAULT_MARKETPLACE,
    DIST_CODEX_PLUGINS_DIR,
    available_codex_plugins,
)


@dataclass(frozen=True)
class CodexCacheWorkspace:
    repo_root: Path
    cache_root: Path


@dataclass
class MaterializingAddRunner:
    """Runner stub that materializes cache roots for local Codex plugin adds.

    Stage 5 exception 2 (interaction-protocol DI): the production path invokes
    `codex plugin add <plugin>@<marketplace>` and observes Codex's filesystem
    side effect. The L1 test records the command sequence and materializes the
    same side effect deterministically.
    """

    cache_root: Path
    versions: dict[str, str]
    calls: list[tuple[str, ...]] = field(default_factory=list)

    @classmethod
    def from_dist_manifests(
        cls, *, cache_root: Path, repo_root: Path
    ) -> "MaterializingAddRunner":
        return cls(
            cache_root=cache_root,
            versions={
                plugin.name: plugin.version
                for plugin in available_codex_plugins(repo_root)
            },
        )

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        command_tuple = tuple(command)
        self.calls.append(command_tuple)
        if command_tuple[: len(CODEX_PLUGIN_ADD_COMMAND)] == CODEX_PLUGIN_ADD_COMMAND:
            plugin_ref = command_tuple[len(CODEX_PLUGIN_ADD_COMMAND)]
            plugin, separator, marketplace = plugin_ref.partition("@")
            if separator != "@" or marketplace != DEFAULT_MARKETPLACE:
                return subprocess.CompletedProcess(command, 64)
            write_plugin_root(
                self.cache_root,
                plugin,
                self.versions[plugin],
                f"{plugin} materialized content",
            )
        return subprocess.CompletedProcess(command, 0)


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
    "MaterializingAddRunner",
    "codex_cache_workspace",
    "write_dist_codex_manifest",
    "write_plugin_root",
]
