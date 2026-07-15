"""Property evidence for lossless review-result serialization."""

from __future__ import annotations

from outcomeeng_testing.harnesses.reviewing_changes import (
    review_result_round_trip_holds,
)


def test_review_result_serialization_round_trip_is_lossless() -> None:
    assert review_result_round_trip_holds()
