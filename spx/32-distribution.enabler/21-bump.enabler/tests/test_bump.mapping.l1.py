"""Level-1 mapping evidence for `spx/32-distribution.enabler/21-bump.enabler/`.

Covers the mapping assertion in `bump.md` that names the segment-increment
semantics: PATCH increments the third semver component; MINOR increments
the second and resets the third to 0; MAJOR increments the first and
resets the second and third to 0.

Evidence is exercised against the `Version` source contract directly, not
through the `bump()` orchestration — the mapping is the pure-logic
contract that the orchestration relies on.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from outcomeeng.distribution.bump import Segment, Version

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
