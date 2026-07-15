"""Property evidence for lossless review-result serialization."""

from __future__ import annotations

from outcomeeng_testing.harnesses.reviewing_changes import (
    malformed_finding_ids_are_rejected,
    malformed_rule_citations_are_rejected,
    review_result_round_trip_holds,
)


def test_review_result_serialization_round_trip_is_lossless() -> None:
    assert review_result_round_trip_holds()


def test_malformed_finding_identifiers_are_rejected() -> None:
    assert malformed_finding_ids_are_rejected()


def test_malformed_rule_citations_are_rejected() -> None:
    assert malformed_rule_citations_are_rejected()
