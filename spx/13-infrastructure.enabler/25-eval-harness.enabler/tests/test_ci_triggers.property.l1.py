"""Property evidence: trigger-path minimization preserves selection coverage."""

from __future__ import annotations

from outcomeeng_testing.harnesses.ci_triggers import (
    assert_minimization_is_a_subset_of_its_input,
    assert_minimization_preserves_coverage,
)


def test_minimization_preserves_coverage() -> None:
    assert_minimization_preserves_coverage()


def test_minimization_is_a_subset_of_its_input() -> None:
    assert_minimization_is_a_subset_of_its_input()
