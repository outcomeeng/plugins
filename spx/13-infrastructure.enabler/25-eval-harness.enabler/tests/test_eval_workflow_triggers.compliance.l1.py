"""Compliance evidence: the eval workflow starts only on operator dispatch."""

from __future__ import annotations

from outcomeeng_testing.harnesses.ci_triggers import (
    assert_eval_workflow_uses_global_budget_default,
    eval_workflow_trigger_events,
)


def test_eval_workflow_declares_no_pull_request_push_or_schedule_trigger() -> None:
    events = eval_workflow_trigger_events()

    assert "pull_request" not in events
    assert "push" not in events
    assert "schedule" not in events


def test_eval_workflow_dispatch_is_its_only_trigger() -> None:
    events = eval_workflow_trigger_events()

    assert events == ("workflow_dispatch",)


def test_eval_workflow_uses_global_budget_default() -> None:
    assert_eval_workflow_uses_global_budget_default()
