"""Compliance evidence for producer-derived eval prompt drift checks."""

from __future__ import annotations

from outcomeeng_testing.evals.producer_prompt import (
    assert_check_accepts_current_materialized_prompt,
    assert_check_rejects_stale_materialized_prompt,
    assert_cli_materializes_and_checks_prompt_drift,
)


def test_check_accepts_current_materialized_prompt() -> None:
    assert_check_accepts_current_materialized_prompt()


def test_check_rejects_stale_materialized_prompt() -> None:
    assert_check_rejects_stale_materialized_prompt()


def test_cli_materializes_and_checks_prompt_drift() -> None:
    assert_cli_materializes_and_checks_prompt_drift()
