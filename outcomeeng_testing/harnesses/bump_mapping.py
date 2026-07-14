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

from typing import Final

from hypothesis import given, seed, settings

from outcomeeng.distribution.bump import (
    ChangedPath,
    Segment,
    Version,
    auto_segment,
    bump_version,
)
from outcomeeng_testing.generators.bump_mapping import (
    AUTO_SEGMENT_MAPPING_CASES,
    mixed_minor_triggering_changes,
    patch_only_changes,
    segments,
    versions,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

BUMP_SEGMENT_PROPERTY_EXAMPLES: Final = 100
BUMP_SEGMENT_PROPERTY_SEED: Final = 20260714
BUMP_SEGMENT_PROPERTY_REPLAY_PATH: Final = (
    "just test spx/32-distribution.enabler/21-bump.enabler/tests/"
    "test_bump.property.l1.py"
)


def segment_increment_property_holds() -> bool:
    run_replayable_property(
        _generated_segment_increment_property,
        seed_value=BUMP_SEGMENT_PROPERTY_SEED,
        replay_path=BUMP_SEGMENT_PROPERTY_REPLAY_PATH,
    )
    return True


@seed(BUMP_SEGMENT_PROPERTY_SEED)
@settings(
    max_examples=BUMP_SEGMENT_PROPERTY_EXAMPLES,
    deadline=None,
    print_blob=True,
)
@given(version=versions(), segment=segments())
def _generated_segment_increment_property(version: Version, segment: Segment) -> None:
    assert bump_version(version, segment) == _expected_bump(version, segment)


def _expected_bump(version: Version, segment: Segment) -> Version:
    if segment is Segment.PATCH:
        return Version(version.major, version.minor, version.patch + 1)
    if segment is Segment.MINOR:
        return Version(version.major, version.minor + 1, 0)
    if segment is Segment.MAJOR:
        return Version(version.major + 1, 0, 0)
    raise AssertionError(segment)


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
