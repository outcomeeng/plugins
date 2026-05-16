"""Ephemeral marketplace git repo for tests that exercise GitPluginHistory.

The harness builds a real git repository on disk with a controlled manifest
commit history, then yields its working-tree path so production code that
reads from `git log` and the working-tree manifest exercises the real code
path. There are no stubs — `outcomeeng.distribution.codex_cache.GitPluginHistory`
sees a real `.git/` directory, real `plugins/<plugin>/.claude-plugin/plugin.json`
files, and real `git log` output.

Stage 4 viability: git is `l1` infrastructure per the methodology and the
adjacent ADR. Temp directories are `l1`. The harness produces deterministic
output because every commit's author and committer dates are pinned by the
caller in days-ago units.

Exception cases per `plugins/spec-tree/skills/testing/references/methodology.md`:
no test double is introduced by this harness — it provisions a real git repo
so the production history walker runs against actual `git log` results.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class ManifestCommit:
    """One plugin-manifest commit at a controlled relative date.

    `version` lands in `plugins/<plugin>/.claude-plugin/plugin.json` and the
    commit's author and committer dates are set to `days_ago` days before now.
    The last commit for a plugin determines its working-tree version.
    """

    plugin: str
    version: str
    days_ago: int


@dataclass(frozen=True)
class MarketplaceRepo:
    """Handle to an ephemeral marketplace repo."""

    root: Path

    def manifest_path(self, plugin: str) -> Path:
        return self.root / "plugins" / plugin / ".claude-plugin" / "plugin.json"


@contextmanager
def with_marketplace_repo(
    base: Path,
    commits: Sequence[ManifestCommit],
) -> Iterator[MarketplaceRepo]:
    """Create a real git repo with the given manifest commit history.

    `base` is the parent directory the test owns (typically pytest's `tmp_path`).
    The repo lives at `base / "repo"`. Commits land in the order given; for each
    commit, the plugin's `.claude-plugin/plugin.json` is rewritten to the new
    version, staged, and committed at the requested relative date.
    """
    root = base / "repo"
    root.mkdir()
    _git(root, "init", "-q", "--initial-branch=main")
    _git(root, "config", "user.email", "harness@outcomeeng.test")
    _git(root, "config", "user.name", "Test Harness")
    _git(root, "config", "commit.gpgsign", "false")

    for commit in commits:
        manifest_dir = root / "plugins" / commit.plugin / ".claude-plugin"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest = manifest_dir / "plugin.json"
        manifest.write_text(
            json.dumps({"name": commit.plugin, "version": commit.version}) + "\n",
        )
        _git(root, "add", "-A")
        date = (datetime.now(tz=UTC) - timedelta(days=commit.days_ago)).strftime(
            "%Y-%m-%dT%H:%M:%S%z",
        )
        _git(
            root,
            "commit",
            "-q",
            "-m",
            f"{commit.plugin}={commit.version}",
            env_overrides={
                "GIT_AUTHOR_DATE": date,
                "GIT_COMMITTER_DATE": date,
            },
        )

    yield MarketplaceRepo(root=root)


def _git(
    cwd: Path,
    *args: str,
    env_overrides: dict[str, str] | None = None,
) -> None:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    subprocess.run(["git", *args], cwd=cwd, env=env, check=True)


__all__ = ["ManifestCommit", "MarketplaceRepo", "with_marketplace_repo"]
