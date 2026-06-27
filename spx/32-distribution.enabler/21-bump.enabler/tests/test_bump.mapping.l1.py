"""Level-1 mapping evidence for `spx/32-distribution.enabler/21-bump.enabler/`.

Covers the two mapping assertions in `bump.md`:

- The segment-increment semantics: PATCH increments the third semver
  component; MINOR increments the second and resets the third to 0;
  MAJOR increments the first and resets the second and third to 0.
- The auto-detection (file-status, path-pattern) → segment mapping:
  `A`/`C`/`D`/`R` on `skills/<slug>/SKILL.md`, `commands/<slug>.md`,
  `agents/<slug>.md`, or `{.claude,.codex}-plugin/plugin.json` yields
  `MINOR`; everything else yields `PATCH`.

Evidence is exercised against the `Version` and `auto_segment` source
contracts directly, not through the `bump()` orchestration.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from outcomeeng.distribution.bump import (
    ChangedPath,
    DIST_CLAUDE_PLUGINS_DIR,
    DIST_CODEX_PLUGINS_DIR,
    FileStatus,
    Segment,
    SOURCE_PLUGINS_DIR,
    Version,
    auto_segment,
)
from outcomeeng_testing.generators.bump import distribution_relpath

SEGMENT_DISPATCH: dict[Segment, Callable[[Version], Version]] = {
    Segment.PATCH: Version.bump_patch,
    Segment.MINOR: Version.bump_minor,
    Segment.MAJOR: Version.bump_major,
}

# Each row: (segment, input_major, input_minor, input_patch, expected output)
MAPPING_CASES: tuple[tuple[Segment, int, int, int, Version], ...] = (
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


@pytest.mark.parametrize(
    ("segment", "input_major", "input_minor", "input_patch", "expected"),
    MAPPING_CASES,
)
def test_segment_increment_matches_mapping(
    segment: Segment,
    input_major: int,
    input_minor: int,
    input_patch: int,
    expected: Version,
) -> None:
    start = Version(major=input_major, minor=input_minor, patch=input_patch)
    actual = SEGMENT_DISPATCH[segment](start)
    assert actual == expected


# Each row: (status, path-relative-to-repo-root, expected segment for a
# plugin whose only change is this one path).
AUTO_SEGMENT_CASES: tuple[tuple[FileStatus, str, Segment], ...] = (
    # Minor-triggering: A/C/D/R on structural surfaces.
    (
        FileStatus.ADDED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "skills/new-skill/SKILL.md"),
        Segment.MINOR,
    ),
    (
        FileStatus.COPIED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "skills/copied-skill/SKILL.md"),
        Segment.MINOR,
    ),
    (
        FileStatus.DELETED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "skills/old-skill/SKILL.md"),
        Segment.MINOR,
    ),
    (
        FileStatus.RENAMED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "skills/renamed/SKILL.md"),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "commands/new-command.md"),
        Segment.MINOR,
    ),
    (
        FileStatus.DELETED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "commands/old-command.md"),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "agents/new-agent.md"),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", ".claude-plugin/plugin.json"),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", ".codex-plugin/plugin.json"),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            DIST_CLAUDE_PLUGINS_DIR,
            "foo",
            "skills/generated-skill/SKILL.md",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            DIST_CODEX_PLUGINS_DIR,
            "foo",
            "skills/generated-skill/SKILL.md",
        ),
        Segment.MINOR,
    ),
    # Patch-only: M on anything (status is the disqualifier).
    (
        FileStatus.MODIFIED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "skills/existing/SKILL.md"),
        Segment.PATCH,
    ),
    (
        FileStatus.MODIFIED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "commands/existing.md"),
        Segment.PATCH,
    ),
    (
        FileStatus.MODIFIED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", ".claude-plugin/plugin.json"),
        Segment.PATCH,
    ),
    (
        FileStatus.MODIFIED,
        distribution_relpath(
            DIST_CODEX_PLUGINS_DIR,
            "foo",
            "skills/generated-skill/SKILL.md",
        ),
        Segment.PATCH,
    ),
    # Patch-only: A/C/D/R on non-structural paths.
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            "skills/existing/scripts/helper.py",
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.COPIED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            "skills/existing/scripts/copied_helper.py",
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            "skills/existing/references/notes.md",
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


@pytest.mark.parametrize(("status", "path", "expected"), AUTO_SEGMENT_CASES)
def test_auto_segment_classifies_each_status_and_path_pattern(
    status: FileStatus,
    path: str,
    expected: Segment,
) -> None:
    assert auto_segment([ChangedPath(status=status, path=path)]) == expected


def test_auto_segment_returns_minor_when_any_change_is_minor_triggering() -> None:
    """Aggregation: a single minor-triggering change in a set of mostly
    patch changes still yields MINOR for the plugin.
    """
    changes = (
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
    assert auto_segment(changes) == Segment.MINOR


def test_auto_segment_returns_patch_when_no_change_triggers_minor() -> None:
    changes = (
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
    assert auto_segment(changes) == Segment.PATCH


def test_auto_segment_never_returns_major() -> None:
    """Auto-detection chooses only between PATCH and MINOR — every input
    pattern in the mapping table must produce a segment in
    `{PATCH, MINOR}`, never MAJOR.
    """
    results = {
        auto_segment([ChangedPath(status=status, path=path)])
        for status, path, _ in AUTO_SEGMENT_CASES
    }
    assert results <= {Segment.PATCH, Segment.MINOR}
    assert Segment.MAJOR not in results
