"""Mapping evidence for the run-journal projection.

Covers the two mapping assertions in ``../journal-projection.md``:

- an event prefix's finding severities roll up to the run's overall — any
  rejecting outcome to rejected, else any unknown to unknown, else approved;
- a finding's optional ``concern``/``action``/``unit``/``tracked`` map into the
  finding event and rendered line when present (``unit`` beside the location,
  ``TRACKED`` after the severity) and are omitted when absent.
"""

from __future__ import annotations

import pytest

from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)

jp = load_journal_projection_module()


def _events_for(findings: tuple) -> list:
    run = jp.RunResult(
        target="t",
        scope_hash="h",
        branch_name="b",
        branch_slug="b",
        head_sha="1" * 40,
        base_ref="main",
        config_digest="cfg",
        participants=("review",),
        scope={"include": ["f.py"]},
        started_at="2026-06-22T00:00:00Z",
        completed_at="2026-06-22T00:00:01Z",
        output_paths=(),
    )
    now = "2026-06-22T00:00:00Z"
    events = [jp.scope_entered_event(run, now=now)]
    for finding in findings:
        events.append(jp.finding_reported_event(finding, now=now))
    status = jp.terminal_status(jp.compute_overall(events))
    events.append(jp.run_completed_event(run, status=status, now=now))
    return events


def _events_with(severities: tuple) -> list:
    return _events_for(
        jp.Finding(file="f.py", line=None, rule="r", severity=severity, message="m")
        for severity in severities
    )


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


# The optional concern/action are a finite source-owned domain: present (the
# review kind sets them) or absent (the audit kind leaves them None). Each
# state maps to whether the event data and rendered line carry the two fields.
# The expected carry/omit derives from the input state, not from the projection.
@pytest.mark.parametrize(
    ("concern", "action", "present"),
    [
        ("security", "set a TTL", True),
        (None, None, False),
    ],
)
def test_optional_concern_action_map_into_event_and_surface(
    concern: str | None, action: str | None, present: bool
) -> None:
    finding = jp.Finding(
        file="f.py",
        line=42,
        rule="r",
        severity=jp.Severity.REJECT,
        message="token never expires",
        concern=concern,
        action=action,
    )
    events = _events_for((finding,))
    data = next(e for e in events if e["type"] == jp.FINDING_REPORTED)["data"]
    line = next(ln for ln in jp.render_surface(events).splitlines() if "f.py:42" in ln)

    assert ("concern" in data) is present
    assert ("action" in data) is present
    if present:
        assert data["concern"] == concern
        assert data["action"] == action
        assert concern in line
        assert f"Required: {action}" in line
    else:
        assert "Required:" not in line


# The optional unit/tracked are a finite source-owned domain: unit present or
# absent, tracked True, False, or absent. The expected carry/omit and rendered
# form derive from the input state: unit renders in parentheses beside the
# location, tracked True renders the TRACKED label after the severity, and an
# absent field leaves both event data and line as the prior shape.
@pytest.mark.parametrize(
    ("unit", "tracked"),
    [
        ("Journal Projection", True),
        ("Journal Projection", False),
        (None, None),
    ],
)
def test_optional_unit_tracked_map_into_event_and_surface(
    unit: str | None, tracked: bool | None
) -> None:
    finding = jp.Finding(
        file="f.py",
        line=42,
        rule="r",
        severity=jp.Severity.WARNING,
        message="stale entry",
        unit=unit,
        tracked=tracked,
    )
    events = _events_for((finding,))
    data = next(e for e in events if e["type"] == jp.FINDING_REPORTED)["data"]
    line = next(ln for ln in jp.render_surface(events).splitlines() if "f.py:42" in ln)

    assert ("unit" in data) is (unit is not None)
    assert ("tracked" in data) is (tracked is not None)
    if unit is not None:
        assert data["unit"] == unit
        assert f"f.py:42 ({unit})" in line
    else:
        assert "(" not in line.split("f.py:42", 1)[1].split("—", 1)[0]
    if tracked is not None:
        assert data["tracked"] is tracked
    severity_label = line.split("]", 1)[0]
    assert severity_label.startswith("- [" + jp.Severity.WARNING.value)
    assert ("TRACKED" in severity_label) is (tracked is True)
    if tracked is True:
        assert severity_label.index("TRACKED") > severity_label.index(
            jp.Severity.WARNING.value
        )
