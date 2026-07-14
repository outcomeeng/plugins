"""Harness-owned mapping evidence for bump segment classification.

Covers the segment-increment and auto-detection mapping assertions:

- The segment-increment semantics: PATCH increments the third semver
  component; MINOR increments the second and resets the third to 0;
  MAJOR increments the first and resets the second and third to 0.
- The auto-detection (file-status, path-pattern) → segment mapping:
  `A`/`C`/`D`/`R` on `skills/<slug>/SKILL.md`, `agents/<slug>.md`,
  or `{.claude,.codex}-plugin/plugin.json` yields
  `MINOR`; everything else yields `PATCH`.

Evidence is exercised against the `Version` and `auto_segment` source
contracts directly, not through the `bump()` orchestration.
"""

from __future__ import annotations

from outcomeeng.distribution.bump import (
    ChangedPath,
    Segment,
    Version,
    auto_segment,
)
from outcomeeng_testing.generators.bump_mapping import (
    AUTO_SEGMENT_MAPPING_CASES,
    SEGMENT_DISPATCH,
    SEGMENT_MAPPING_CASES,
    mixed_minor_triggering_changes,
    patch_only_changes,
)


def segment_increment_matches_mapping() -> bool:
    for (
        segment,
        input_major,
        input_minor,
        input_patch,
        expected,
    ) in SEGMENT_MAPPING_CASES:
        start = Version(major=input_major, minor=input_minor, patch=input_patch)
        if SEGMENT_DISPATCH[segment](start) != expected:
            return False
    return True


def auto_segment_classifies_each_status_and_path_pattern() -> bool:
    return all(
        auto_segment([ChangedPath(status=status, path=path)]) == expected
        for status, path, expected in AUTO_SEGMENT_MAPPING_CASES
    )


def auto_segment_returns_minor_when_any_change_is_minor_triggering() -> bool:
    return auto_segment(mixed_minor_triggering_changes()) == Segment.MINOR


def auto_segment_returns_patch_when_no_change_triggers_minor() -> bool:
    return auto_segment(patch_only_changes()) == Segment.PATCH


def auto_segment_never_returns_major() -> bool:
    results = {
        auto_segment([ChangedPath(status=status, path=path)])
        for status, path, _ in AUTO_SEGMENT_MAPPING_CASES
    }
    return results <= {Segment.PATCH, Segment.MINOR} and Segment.MAJOR not in results
