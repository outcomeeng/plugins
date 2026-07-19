"""Property tests for the manage-pr review-thread resolver."""

from __future__ import annotations

from outcomeeng_testing.harnesses.review_thread_resolver import (
    malformed_inputs_fail_before_github_calls,
)


def test_malformed_inputs_fail_before_github_calls() -> None:
    assert malformed_inputs_fail_before_github_calls()
