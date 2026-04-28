"""Level 1 installation scenarios for preserving stale Codex plugin cache paths."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from outcomeeng.scripts import preserve_codex_plugin_cache

MARKETPLACE_NAME = "outcomeeng"
PLUGIN_NAME = "spec-tree"
OLD_VERSION = "0.26.5"
NEW_VERSION = "0.26.6"
OLD_SKILL_TEXT = "old skill"
NEW_SKILL_TEXT = "new skill"
STALE_AGE_DAYS = 8
MAX_AGE_DAYS = 7
SECONDS_PER_DAY = 24 * 60 * 60
COMMAND_OK = 0


def _skill_file(cache_root: Path, version: str) -> Path:
    return (
        cache_root
        / MARKETPLACE_NAME
        / PLUGIN_NAME
        / version
        / "skills"
        / "contextualizing"
        / "SKILL.md"
    )


def _write_skill(cache_root: Path, version: str, text: str) -> None:
    skill_file = _skill_file(cache_root, version)
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text(text)


def test_upgrade_restores_removed_version_path_as_symlink(
    tmp_path: Path,
) -> None:
    cache_root = tmp_path / "cache"
    _write_skill(cache_root, OLD_VERSION, OLD_SKILL_TEXT)
    old_version_dir = cache_root / MARKETPLACE_NAME / PLUGIN_NAME / OLD_VERSION
    new_version_dir = cache_root / MARKETPLACE_NAME / PLUGIN_NAME / NEW_VERSION
    commands: list[list[str]] = []

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        old_version_dir.rename(tmp_path / "removed-old-version")
        _write_skill(cache_root, NEW_VERSION, NEW_SKILL_TEXT)
        return subprocess.CompletedProcess(command, COMMAND_OK)

    result = preserve_codex_plugin_cache.preserve_during_upgrade(
        MARKETPLACE_NAME,
        cache_root=cache_root,
        max_age_days=MAX_AGE_DAYS,
        runner=runner,
    )

    assert commands == [["codex", "plugin", "marketplace", "upgrade", MARKETPLACE_NAME]]
    assert old_version_dir.is_symlink()
    assert old_version_dir.resolve() == new_version_dir
    assert _skill_file(cache_root, OLD_VERSION).read_text() == NEW_SKILL_TEXT
    assert result.linked_versions == (old_version_dir,)


def test_upgrade_prunes_stale_version_symlinks(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    _write_skill(cache_root, NEW_VERSION, NEW_SKILL_TEXT)
    plugin_dir = cache_root / MARKETPLACE_NAME / PLUGIN_NAME
    stale_link = plugin_dir / OLD_VERSION
    stale_link.symlink_to(NEW_VERSION, target_is_directory=True)
    stale_mtime = preserve_codex_plugin_cache.current_time() - (
        STALE_AGE_DAYS * SECONDS_PER_DAY
    )
    os.utime(stale_link, (stale_mtime, stale_mtime), follow_symlinks=False)

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, COMMAND_OK)

    result = preserve_codex_plugin_cache.preserve_during_upgrade(
        MARKETPLACE_NAME,
        cache_root=cache_root,
        max_age_days=MAX_AGE_DAYS,
        runner=runner,
    )

    assert not stale_link.exists()
    assert result.pruned_links == (stale_link,)
