"""Mapping evidence for review-result wire vocabulary."""

from __future__ import annotations

from outcomeeng_testing.harnesses.reviewing_changes import load_review_result_module


def test_severity_members_map_to_wire_values() -> None:
    review_result = load_review_result_module()
    assert {member.value for member in review_result.Severity} == {
        review_result.SEVERITY_BLOCKING,
        review_result.SEVERITY_DEBT,
    }


def test_concern_members_map_to_wire_values() -> None:
    review_result = load_review_result_module()
    assert {member.value for member in review_result.Concern} == {
        review_result.CONCERN_CONSISTENCY,
        review_result.CONCERN_SECURITY,
        review_result.CONCERN_PERFORMANCE,
        review_result.CONCERN_EVIDENCE,
        review_result.CONCERN_ARCHITECTURE,
    }
