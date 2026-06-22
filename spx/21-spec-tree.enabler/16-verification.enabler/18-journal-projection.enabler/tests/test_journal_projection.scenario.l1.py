"""Scenario evidence for the run-journal projection's ``build_events``.

Covers the scenario assertion in ``../journal-projection.md``: given a
verification run's results, ``build_events`` yields a scope-entered event,
one finding-reported event per finding, and a terminal run-completed event,
each a valid channel append input.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)

jp = load_journal_projection_module()


def _run_with(findings: tuple) -> object:
    return jp.RunResult(
        target="spx/example.enabler",
        scope_hash="abc123def456",
        branch="work/example",
        findings=tuple(findings),
    )


def test_build_events_emits_scope_findings_run_in_order() -> None:
    findings = (
        jp.Finding(
            file="a.py", line=1, rule="r1", severity=jp.Severity.INFO, message="m1"
        ),
        jp.Finding(
            file="b.py", line=None, rule="r2", severity=jp.Severity.REJECT, message="m2"
        ),
    )
    events = jp.build_events(_run_with(findings), now="2026-06-22T00:00:00Z", attempt=1)

    types = [event["type"] for event in events]
    assert types[0] == jp.SCOPE_ENTERED
    assert types[-1] == jp.RUN_COMPLETED
    assert types.count(jp.FINDING_REPORTED) == len(findings)
    # The generic core is exactly scope-entered + one-per-finding + run-completed.
    assert len(events) == len(findings) + 2


def test_build_events_emits_valid_channel_inputs() -> None:
    findings = (
        jp.Finding(
            file="a.py", line=10, rule="r", severity=jp.Severity.WARNING, message="m"
        ),
    )
    events = jp.build_events(_run_with(findings), now="2026-06-22T00:00:00Z", attempt=2)

    for event in events:
        for field in jp.EVENT_INPUT_STRING_FIELDS:
            value = event[field]
            assert isinstance(value, str) and value, (
                f"{field} must be a non-empty string"
            )
        # attempt is an integer (and not a bool, which is an int subclass).
        assert isinstance(event["attempt"], int) and not isinstance(
            event["attempt"], bool
        )
        assert isinstance(event["data"], dict)
