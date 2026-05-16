"""Pre-state independence property for the Codex plugin cache preservation step.

The product invariant under test: the post-run cache state is a pure function
of git history and the working-tree manifests, independent of cache state
observed before the recipe ran.

Hypothesis generates a variable set of pre-state cache shapes (stale symlinks
pointing at non-existent versions, leftover symlinks for versions outside the
window, empty cache directories) and asserts that the post-preservation
symlink set is identical across all pre-states paired with the same git
history and the same working-tree manifest.

The codex subprocess runner is stubbed for safety (Stage 5 exception 4 per
``plugins/spec-tree/skills/testing/references/methodology.md``). The history
walker runs unstubbed against a real ephemeral git repository.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from outcomeeng.distribution.codex_cache import (
    DEFAULT_MARKETPLACE,
    GitPluginHistory,
    preserve_during_upgrade,
)
from outcomeeng_testing.harnesses.marketplace_repo import (
    ManifestCommit,
    with_marketplace_repo,
)

PLUGIN_NAME = "spec-tree"
OLDER_VERSION = "0.26.5"
CURRENT_VERSION = "0.26.6"


def _quiet_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 0)


def _seed_real_current(cache_root: Path) -> None:
    """The post-codex-upgrade baseline: only the current version is real."""
    current_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME / CURRENT_VERSION
    (current_dir / "skills" / "x").mkdir(parents=True)


def _seed_pre_state(cache_root: Path, pre_state: frozenset[str]) -> None:
    """Add the requested set of stale symlinks at the plugin path.

    `pre_state` is a set of version strings. Each becomes a symlink whose
    target is the current version directory name (which may or may not yet
    exist on disk). This mirrors the shapes the cache can reach after past
    runs of the script under varying preservation logic.
    """
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME
    plugin_dir.mkdir(parents=True, exist_ok=True)
    for version in pre_state:
        if version == CURRENT_VERSION:
            continue
        link = plugin_dir / version
        if link.exists() or link.is_symlink():
            continue
        link.symlink_to(CURRENT_VERSION, target_is_directory=True)


def _snapshot(cache_root: Path) -> frozenset[tuple[str, str | None]]:
    """Return a deterministic snapshot of the plugin directory contents.

    Each entry is `(name, resolution)` where `resolution` is the symlink
    target name (relative) or None for a real directory.
    """
    plugin_dir = cache_root / DEFAULT_MARKETPLACE / PLUGIN_NAME
    if not plugin_dir.is_dir():
        return frozenset()
    entries: set[tuple[str, str | None]] = set()
    for entry in plugin_dir.iterdir():
        if entry.is_symlink():
            entries.add((entry.name, str(entry.readlink())))
        else:
            entries.add((entry.name, None))
    return frozenset(entries)


def _arbitrary_pre_state() -> st.SearchStrategy[frozenset[str]]:
    """Variable pre-state shapes: any subset of plausible version strings.

    Includes versions that are out of window (stale symlinks left behind by
    a prior run that used a different window) and versions that never existed
    (artifacts of manual cache tampering).
    """
    candidates = st.sampled_from(
        ["0.10.0", "0.20.0", "0.26.0", OLDER_VERSION, "0.99.0"],
    )
    return st.frozensets(candidates, max_size=4)


@given(pre_state=_arbitrary_pre_state())
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_post_run_cache_state_is_independent_of_pre_state(
    tmp_path_factory: pytest.TempPathFactory,
    pre_state: frozenset[str],
) -> None:
    """For a fixed git history and working tree, every pre-state cache
    shape leads to the same post-run cache state.
    """
    tmp_a = tmp_path_factory.mktemp("a")
    cache_a = tmp_a / "cache"
    _seed_real_current(cache_a)
    _seed_pre_state(cache_a, pre_state)

    tmp_b = tmp_path_factory.mktemp("b")
    cache_b = tmp_b / "cache"
    _seed_real_current(cache_b)

    with with_marketplace_repo(
        tmp_a,
        [
            ManifestCommit(plugin=PLUGIN_NAME, version=OLDER_VERSION, days_ago=5),
            ManifestCommit(plugin=PLUGIN_NAME, version=CURRENT_VERSION, days_ago=0),
        ],
    ) as repo_a:
        history_a = GitPluginHistory(repo_root=repo_a.root, window_days=10)
        preserve_during_upgrade(
            DEFAULT_MARKETPLACE,
            cache_root=cache_a,
            history=history_a,
            runner=_quiet_runner,
        )

    with with_marketplace_repo(
        tmp_b,
        [
            ManifestCommit(plugin=PLUGIN_NAME, version=OLDER_VERSION, days_ago=5),
            ManifestCommit(plugin=PLUGIN_NAME, version=CURRENT_VERSION, days_ago=0),
        ],
    ) as repo_b:
        history_b = GitPluginHistory(repo_root=repo_b.root, window_days=10)
        preserve_during_upgrade(
            DEFAULT_MARKETPLACE,
            cache_root=cache_b,
            history=history_b,
            runner=_quiet_runner,
        )

    assert _snapshot(cache_a) == _snapshot(cache_b), (
        f"post-run cache state differs across pre-states\n"
        f"pre_state: {sorted(pre_state)}\n"
        f"with-pre-state: {sorted(_snapshot(cache_a))}\n"
        f"clean: {sorted(_snapshot(cache_b))}"
    )
