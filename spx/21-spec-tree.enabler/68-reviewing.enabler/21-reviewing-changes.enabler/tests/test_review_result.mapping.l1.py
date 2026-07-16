"""Mapping evidence for review-result wire vocabulary."""

from __future__ import annotations

from outcomeeng_testing.harnesses.reviewing_changes import (
    review_wire_vocabulary_mapping_holds,
)


def test_review_enums_map_to_wire_values() -> None:
    assert review_wire_vocabulary_mapping_holds()
