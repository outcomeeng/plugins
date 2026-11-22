"""Compliance evidence: the eval workflow declares workflow_dispatch as its only trigger."""

from __future__ import annotations

from outcomeeng_testing.harnesses.eval_workflow import (
    observe_workflow_triggers,
    violating_trigger_workflow_paths,
)

FORBIDDEN_TRIGGERS = frozenset({"pull_request", "push", "schedule"})
DISPATCH_TRIGGER = "workflow_dispatch"


def test_trigger_detection_flags_every_violating_workflow() -> None:
    violating_paths = violating_trigger_workflow_paths()

    assert violating_paths
    for path in violating_paths:
        observed = observe_workflow_triggers(path)
        assert observed & FORBIDDEN_TRIGGERS, path.name


def test_committed_eval_workflow_declares_only_workflow_dispatch() -> None:
    observed = observe_workflow_triggers()

    assert observed == {DISPATCH_TRIGGER}
    assert not observed & FORBIDDEN_TRIGGERS
