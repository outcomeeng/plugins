"""Mapping evidence: eval definitions map to the workflow's trigger paths."""

from __future__ import annotations

import pytest

from outcomeeng_evals.definition import CiPolicy
from outcomeeng_testing.harnesses.ci_triggers import (
    assert_ci_policy_controls_trigger_contribution,
    assert_universal_paths_always_contribute,
)


@pytest.mark.parametrize("policy", tuple(CiPolicy))
def test_ci_policy_controls_trigger_contribution(policy: CiPolicy) -> None:
    assert_ci_policy_controls_trigger_contribution(policy)


def test_universal_paths_always_contribute() -> None:
    assert_universal_paths_always_contribute()
