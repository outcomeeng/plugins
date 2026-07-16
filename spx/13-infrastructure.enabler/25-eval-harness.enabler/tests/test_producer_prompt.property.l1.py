"""Property evidence for producer-derived eval prompt materialization."""

from __future__ import annotations

from outcomeeng_testing.evals.producer_prompt import (
    assert_materialized_prompt_changes_only_with_selected_section,
)


def test_materialized_prompt_changes_only_with_selected_section() -> None:
    assert_materialized_prompt_changes_only_with_selected_section()
