"""Mapping evidence for the run-journal projection's ``compute_overall``.

Covers the mapping assertion in ``../journal-projection.md``: an event
prefix's outcomes roll up to the run's overall — any rejecting/failing
outcome to rejected, else any unknown to unknown, else approved.
"""

from __future__ import annotations

import pytest

from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)

jp = load_journal_projection_module()


def _events_with(severities: tuple) -> list:
    findings = tuple(
        jp.Finding(file="f.py", line=None, rule="r", severity=severity, message="m")
        for severity in severities
    )
    run = jp.RunResult(
        target="t",
        scope_hash="h",
        branch_name="b",
        branch_slug="b",
        head_sha="1" * 40,
        base_ref="main",
        config_digest="cfg",
        participants=("audit",),
        scope={"include": ["f.py"]},
        started_at="2026-06-22T00:00:00Z",
        completed_at="2026-06-22T00:00:01Z",
        output_paths=(),
        findings=findings,
    )
    return jp.build_events(run, now="2026-06-22T00:00:00Z")


# Severities are the source-owned domain (jp.Severity); the expected overall
# is derived independently from the rollup rule, never read back from the
# projection. Cases cover each outcome branch and the rejecting-dominates and
# unknown-over-approved precedence.
@pytest.mark.parametrize(
    ("severities", "expected"),
    [
        ((), jp.Outcome.APPROVED),
        ((jp.Severity.INFO,), jp.Outcome.APPROVED),
        ((jp.Severity.WARNING, jp.Severity.INFO), jp.Outcome.APPROVED),
        ((jp.Severity.UNKNOWN,), jp.Outcome.UNKNOWN),
        ((jp.Severity.INFO, jp.Severity.UNKNOWN), jp.Outcome.UNKNOWN),
        ((jp.Severity.REJECT,), jp.Outcome.REJECTED),
        ((jp.Severity.INFO, jp.Severity.REJECT), jp.Outcome.REJECTED),
        ((jp.Severity.REJECT, jp.Severity.UNKNOWN), jp.Outcome.REJECTED),
    ],
)
def test_compute_overall_rolls_up_severities(
    severities: tuple, expected: object
) -> None:
    assert jp.compute_overall(_events_with(severities)) == expected
