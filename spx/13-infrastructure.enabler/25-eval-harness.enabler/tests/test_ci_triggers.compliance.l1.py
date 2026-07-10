"""Compliance evidence: the trigger drift check rejects a stale workflow."""

from __future__ import annotations

from outcomeeng_testing.harnesses.ci_triggers import (
    assert_check_fails_when_a_trigger_path_is_removed,
    assert_check_fails_when_an_unowned_trigger_path_is_added,
    assert_check_passes_when_workflow_is_current,
    assert_every_trigger_block_receives_the_same_paths,
)


def test_check_passes_when_workflow_is_current() -> None:
    assert_check_passes_when_workflow_is_current()


def test_check_fails_when_a_trigger_path_is_removed() -> None:
    assert_check_fails_when_a_trigger_path_is_removed()


def test_check_fails_when_an_unowned_trigger_path_is_added() -> None:
    assert_check_fails_when_an_unowned_trigger_path_is_added()


def test_every_trigger_block_receives_the_same_paths() -> None:
    assert_every_trigger_block_receives_the_same_paths()
