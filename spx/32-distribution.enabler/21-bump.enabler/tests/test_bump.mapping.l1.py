"""Level-1 mapping evidence for `spx/32-distribution.enabler/21-bump.enabler/`.

Covers the two mapping assertions in `bump.md`:

- The segment-increment semantics: PATCH increments the third semver
  component; MINOR increments the second and resets the third to 0;
  MAJOR increments the first and resets the second and third to 0.
- The auto-detection (file-status, path-pattern) → segment mapping:
  `A`/`D`/`R` on `skills/<slug>/SKILL.md`, `commands/<slug>.md`,
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
    FileStatus,
    Segment,
    Version,
    auto_segment,
)

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
    # Minor-triggering: A/D/R on structural surfaces.
    (FileStatus.ADDED, "src/plugins/foo/skills/new-skill/SKILL.md", Segment.MINOR),
    (FileStatus.DELETED, "src/plugins/foo/skills/old-skill/SKILL.md", Segment.MINOR),
    (FileStatus.RENAMED, "src/plugins/foo/skills/renamed/SKILL.md", Segment.MINOR),
    (FileStatus.ADDED, "src/plugins/foo/commands/new-command.md", Segment.MINOR),
    (FileStatus.DELETED, "src/plugins/foo/commands/old-command.md", Segment.MINOR),
    (FileStatus.ADDED, "src/plugins/foo/agents/new-agent.md", Segment.MINOR),
    (FileStatus.ADDED, "src/plugins/foo/.claude-plugin/plugin.json", Segment.MINOR),
    (FileStatus.ADDED, "src/plugins/foo/.codex-plugin/plugin.json", Segment.MINOR),
    # Patch-only: M on anything (status is the disqualifier).
    (FileStatus.MODIFIED, "src/plugins/foo/skills/existing/SKILL.md", Segment.PATCH),
    (FileStatus.MODIFIED, "src/plugins/foo/commands/existing.md", Segment.PATCH),
    (FileStatus.MODIFIED, "src/plugins/foo/.claude-plugin/plugin.json", Segment.PATCH),
    # Patch-only: A/D/R on non-structural paths.
    (
        FileStatus.ADDED,
        "src/plugins/foo/skills/existing/scripts/helper.py",
        Segment.PATCH,
    ),
    (
        FileStatus.ADDED,
        "src/plugins/foo/skills/existing/references/notes.md",
        Segment.PATCH,
    ),
    (FileStatus.ADDED, "src/plugins/foo/templates/new-template.md", Segment.PATCH),
    (FileStatus.ADDED, "src/plugins/foo/hooks/hooks.json", Segment.PATCH),
    (FileStatus.DELETED, "src/plugins/foo/.gitignore", Segment.PATCH),
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
        ChangedPath(FileStatus.MODIFIED, "src/plugins/foo/.claude-plugin/plugin.json"),
        ChangedPath(FileStatus.MODIFIED, "src/plugins/foo/skills/existing/SKILL.md"),
        ChangedPath(FileStatus.ADDED, "src/plugins/foo/skills/new/SKILL.md"),
    )
    assert auto_segment(changes) == Segment.MINOR


def test_auto_segment_returns_patch_when_no_change_triggers_minor() -> None:
    changes = (
        ChangedPath(FileStatus.MODIFIED, "src/plugins/foo/.claude-plugin/plugin.json"),
        ChangedPath(FileStatus.MODIFIED, "src/plugins/foo/skills/existing/SKILL.md"),
        ChangedPath(FileStatus.ADDED, "src/plugins/foo/templates/foo.md"),
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
