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

from collections.abc import Callable
from typing import Final

from hypothesis import given, seed, settings

from outcomeeng.distribution.bump import Segment, Version
from outcomeeng_testing.generators.bump_mapping import segments, versions
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

BUMP_SEGMENT_PROPERTY_EXAMPLES: Final = 100
BUMP_SEGMENT_PROPERTY_SEED: Final = 20260714
BUMP_SEGMENT_PROPERTY_REPLAY_PATH: Final = (
    "just test spx/32-distribution.enabler/21-bump.enabler/tests/"
    "test_bump.property.l1.py"
)


def run_segment_increment_property(check: Callable[[Version, Segment], None]) -> None:
    """Drive `check` over generated version and segment pairs with replay notes."""

    @seed(BUMP_SEGMENT_PROPERTY_SEED)
    @settings(
        max_examples=BUMP_SEGMENT_PROPERTY_EXAMPLES,
        deadline=None,
        print_blob=True,
    )
    @given(version=versions(), segment=segments())
    def run(version: Version, segment: Segment) -> None:
        check(version, segment)

    run_replayable_property(
        run,
        seed_value=BUMP_SEGMENT_PROPERTY_SEED,
        replay_path=BUMP_SEGMENT_PROPERTY_REPLAY_PATH,
    )
