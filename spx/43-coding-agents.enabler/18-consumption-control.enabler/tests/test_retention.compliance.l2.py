"""Recognized reports and alerts expire while operator-owned files survive."""

from outcomeeng_testing.harnesses.consumption_control import (
    retention_observation,
    workspace,
)


def test_retention_bounds_recognized_artifacts() -> None:
    with workspace() as work:
        observed = retention_observation(work)
        assert observed.remaining <= observed.ceiling
        assert observed.preserved_foreign
        assert observed.report_gaps
        assert observed.alerts_before
        assert observed.alerts_after == observed.expected_after
