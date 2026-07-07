"""Compliance evidence for GitHub Actions workflow safety policy."""

from __future__ import annotations

from outcomeeng_testing.harnesses.github_actions_workflows import (
    active_generic_claude_callers,
    external_workflow_pin_violations,
)


def test_external_workflow_uses_are_pinned_to_sha_or_marked_beta_main() -> None:
    assert not external_workflow_pin_violations()


def test_generic_claude_callers_are_not_active_workflows() -> None:
    assert not active_generic_claude_callers()
