"""Compliance wrapper for append-only eval history."""

from outcomeeng_testing.harnesses.eval_history import assert_history_compliance


def test_history_compliance() -> None:
    assert_history_compliance()
