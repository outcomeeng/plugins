"""Mapping evidence: eval definitions map to the workflow's trigger paths."""

from outcomeeng_testing.harnesses.ci_triggers import (
    assert_ci_policy_controls_trigger_contribution,
    assert_universal_paths_always_contribute,
)


def test_ci_policy_controls_trigger_contribution() -> None:
    assert_ci_policy_controls_trigger_contribution()


def test_universal_paths_always_contribute() -> None:
    assert_universal_paths_always_contribute()
