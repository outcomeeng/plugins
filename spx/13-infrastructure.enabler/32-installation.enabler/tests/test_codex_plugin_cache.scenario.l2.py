"""Level 2 scenarios for the Codex plugin cache preservation CLI.

The CLI surface tested here is the production entrypoint that
``just sync-marketplace`` invokes:

    python -m outcomeeng.distribution.codex_cache <marketplace>

Tests construct an ephemeral marketplace git repository, an isolated cache
root, and a fake ``codex`` binary on PATH whose only behavior is to exit 0
(Stage 5 exception 4 / Safety, per the methodology — real Codex mutates
``~/.codex/`` shared admin state). They then spawn the CLI as a real
subprocess with the working directory set to the ephemeral repository and
inspect the resulting symlink topology under ``cache_root``.

This file exists because the ``l1`` tests stub the codex subprocess and call
``preserve_during_upgrade`` directly, bypassing ``main()``'s argument
parsing, ``GitPluginHistory(repo_root=...)`` construction, and the
``python -m`` module-resolution path. Regressions in any of those wiring
points stay invisible to ``l1`` tests; this file catches them.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from outcomeeng.distribution.codex_cache import DEFAULT_MARKETPLACE
from outcomeeng_testing.harnesses.marketplace_repo import (
    ManifestCommit,
    with_marketplace_repo,
)

PLUGIN_NAME = "spec-tree"
OLDER_VERSION = "0.26.5"
CURRENT_VERSION = "0.26.6"


def _make_cache_with_current(cache_root: Path, plugin: str, version: str) -> Path:
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / plugin / version
    (plugin_dir / "skills" / "x").mkdir(parents=True)
    return plugin_dir


def _install_fake_codex(bin_dir: Path) -> None:
    """Place a fake `codex` executable in `bin_dir` that exits 0."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    fake = bin_dir / "codex"
    fake.write_text("#!/bin/sh\nexit 0\n")
    fake.chmod(0o755)


def _run_cli(
    repo_root: Path,
    cache_root: Path,
    fake_bin_dir: Path,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin_dir}{os.pathsep}{env.get('PATH', '')}"
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "outcomeeng.distribution.codex_cache",
            DEFAULT_MARKETPLACE,
            "--cache-root",
            str(cache_root),
            "--repo-root",
            str(repo_root),
        ],
        env=env,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_invoked_from_working_tree_writes_symlinks_for_in_window_history(
    tmp_path: Path,
) -> None:
    """End-to-end: invoking the CLI from a marketplace working tree produces
    a symlink topology that reflects each working-tree plugin's manifest
    history within the configured window. The CLI consults the working tree
    it was invoked from, regardless of the invoking shell's earlier `cd`
    history.
    """
    cache_root = tmp_path / "cache"
    current_dir = _make_cache_with_current(cache_root, PLUGIN_NAME, CURRENT_VERSION)
    older_path = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME / OLDER_VERSION
    fake_bin_dir = tmp_path / "fake-bin"
    _install_fake_codex(fake_bin_dir)

    with with_marketplace_repo(
        tmp_path,
        [
            ManifestCommit(plugin=PLUGIN_NAME, version=OLDER_VERSION, days_ago=5),
            ManifestCommit(plugin=PLUGIN_NAME, version=CURRENT_VERSION, days_ago=0),
        ],
    ) as repo:
        result = _run_cli(repo.root, cache_root, fake_bin_dir)

    assert result.returncode == 0, (
        f"CLI exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert older_path.is_symlink(), (
        f"expected {older_path} symlink after CLI run\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert older_path.resolve() == current_dir.resolve()


def test_cli_respects_repo_root_argument_over_cwd_for_plugin_discovery(
    tmp_path: Path,
) -> None:
    """The CLI's `--repo-root` argument selects the working tree the history
    walker consults. When `--repo-root` points at one ephemeral repo and the
    process cwd points at another (unrelated) directory, the resulting
    symlink topology reflects the `--repo-root` repository's manifest history,
    not the cwd.
    """
    cache_root = tmp_path / "cache"
    current_dir = _make_cache_with_current(cache_root, PLUGIN_NAME, CURRENT_VERSION)
    older_path = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME / OLDER_VERSION
    fake_bin_dir = tmp_path / "fake-bin"
    _install_fake_codex(fake_bin_dir)
    unrelated_cwd = tmp_path / "unrelated"
    unrelated_cwd.mkdir()

    with with_marketplace_repo(
        tmp_path,
        [
            ManifestCommit(plugin=PLUGIN_NAME, version=OLDER_VERSION, days_ago=5),
            ManifestCommit(plugin=PLUGIN_NAME, version=CURRENT_VERSION, days_ago=0),
        ],
    ) as repo:
        env = os.environ.copy()
        env["PATH"] = f"{fake_bin_dir}{os.pathsep}{env.get('PATH', '')}"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "outcomeeng.distribution.codex_cache",
                DEFAULT_MARKETPLACE,
                "--cache-root",
                str(cache_root),
                "--repo-root",
                str(repo.root),
            ],
            env=env,
            cwd=unrelated_cwd,
            capture_output=True,
            text=True,
            check=False,
        )

    assert result.returncode == 0, (
        f"CLI exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert older_path.is_symlink(), (
        f"expected {older_path} symlink even when cwd={unrelated_cwd}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert older_path.resolve() == current_dir.resolve()
