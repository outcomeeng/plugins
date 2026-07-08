"""Compliance evidence for GitHub Actions workflow safety policy."""

from __future__ import annotations

from outcomeeng_testing.harnesses.github_actions_workflows import (
    UNPINNED_QUOTED_USES_VALUE,
    active_generic_claude_callers,
    block_scalar_uses_text_pin_violations,
    external_workflow_pin_violations,
    quoted_uses_key_pin_violations,
    renovate_beta_main_exemption_violations,
    sonar_beta_main_exclusion_violations,
)


def test_external_workflow_uses_are_pinned_to_sha_or_marked_beta_main() -> None:
    assert not external_workflow_pin_violations()


def test_external_workflow_pin_scanner_reads_quoted_uses_keys() -> None:
    assert quoted_uses_key_pin_violations() == (UNPINNED_QUOTED_USES_VALUE,)


def test_external_workflow_pin_scanner_ignores_block_scalar_uses_text() -> None:
    assert not block_scalar_uses_text_pin_violations()


def test_sonar_excludes_only_marked_beta_main_callers() -> None:
    assert not sonar_beta_main_exclusion_violations()


def test_renovate_exempts_only_marked_beta_main_callers() -> None:
    assert not renovate_beta_main_exemption_violations()


def test_generic_claude_callers_are_not_active_workflows() -> None:
    assert not active_generic_claude_callers()
