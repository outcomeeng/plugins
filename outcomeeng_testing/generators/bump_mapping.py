"""Generator-owned mapping cases for bump segment tests."""

from __future__ import annotations

from collections.abc import Callable

from outcomeeng.distribution.bump import (
    ChangedPath,
    DIST_CLAUDE_PLUGINS_DIR,
    DIST_CODEX_PLUGINS_DIR,
    FileStatus,
    Segment,
    SOURCE_PLUGINS_DIR,
    Version,
)
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    CLAUDE_PLUGIN_SUBDIR_NAME,
    CODEX_PLUGIN_SUBDIR_NAME,
    MARKDOWN_FILE_SUFFIX,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
)
from outcomeeng_testing.generators.bump import distribution_relpath

SEGMENT_DISPATCH: dict[Segment, Callable[[Version], Version]] = {
    Segment.PATCH: Version.bump_patch,
    Segment.MINOR: Version.bump_minor,
    Segment.MAJOR: Version.bump_major,
}

SEGMENT_MAPPING_CASES: tuple[tuple[Segment, int, int, int, Version], ...] = (
    (Segment.PATCH, 0, 4, 1, Version(major=0, minor=4, patch=2)),
    (Segment.PATCH, 1, 2, 9, Version(major=1, minor=2, patch=10)),
    (Segment.PATCH, 0, 0, 0, Version(major=0, minor=0, patch=1)),
    (Segment.MINOR, 0, 4, 1, Version(major=0, minor=5, patch=0)),
    (Segment.MINOR, 1, 2, 9, Version(major=1, minor=3, patch=0)),
    (Segment.MINOR, 0, 0, 5, Version(major=0, minor=1, patch=0)),
    (Segment.MAJOR, 0, 4, 1, Version(major=1, minor=0, patch=0)),
    (Segment.MAJOR, 1, 2, 9, Version(major=2, minor=0, patch=0)),
    (Segment.MAJOR, 0, 0, 0, Version(major=1, minor=0, patch=0)),
)

AUTO_SEGMENT_MAPPING_CASES: tuple[tuple[FileStatus, str, Segment], ...] = (
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/new-skill/{SKILL_FILENAME}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.COPIED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/copied-skill/{SKILL_FILENAME}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.DELETED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/old-skill/{SKILL_FILENAME}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.RENAMED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/renamed/{SKILL_FILENAME}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{AGENTS_SUBDIR_NAME}/new-agent{MARKDOWN_FILE_SUFFIX}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{CLAUDE_PLUGIN_SUBDIR_NAME}/plugin.json",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{CODEX_PLUGIN_SUBDIR_NAME}/plugin.json",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            DIST_CLAUDE_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/generated-skill/{SKILL_FILENAME}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            DIST_CODEX_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/generated-skill/{SKILL_FILENAME}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.MODIFIED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/existing/{SKILL_FILENAME}",
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.MODIFIED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{CLAUDE_PLUGIN_SUBDIR_NAME}/plugin.json",
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.MODIFIED,
        distribution_relpath(
            DIST_CODEX_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/generated-skill/{SKILL_FILENAME}",
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR, "foo", "skills/existing/scripts/helper.py"
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.COPIED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR, "foo", "skills/existing/scripts/copied_helper.py"
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR, "foo", "skills/existing/references/notes.md"
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "templates/new-template.md"),
        Segment.PATCH,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "hooks/hooks.json"),
        Segment.PATCH,
    ),
    (
        FileStatus.DELETED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", ".gitignore"),
        Segment.PATCH,
    ),
)


def mixed_minor_triggering_changes() -> tuple[ChangedPath, ...]:
    return (
        ChangedPath(
            FileStatus.MODIFIED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR, "foo", ".claude-plugin/plugin.json"
            ),
        ),
        ChangedPath(
            FileStatus.MODIFIED,
            distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "skills/existing/SKILL.md"),
        ),
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(DIST_CODEX_PLUGINS_DIR, "foo", "skills/new/SKILL.md"),
        ),
    )


def patch_only_changes() -> tuple[ChangedPath, ...]:
    return (
        ChangedPath(
            FileStatus.MODIFIED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR, "foo", ".claude-plugin/plugin.json"
            ),
        ),
        ChangedPath(
            FileStatus.MODIFIED,
            distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "skills/existing/SKILL.md"),
        ),
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(DIST_CLAUDE_PLUGINS_DIR, "foo", "templates/foo.md"),
        ),
    )
