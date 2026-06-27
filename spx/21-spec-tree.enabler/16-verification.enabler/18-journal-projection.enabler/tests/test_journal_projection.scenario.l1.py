"""Scenario evidence for the run-journal projection's per-event builders and
``render_surface``.

Covers the scenario assertions in ``../journal-projection.md``: given the data
for one domain event the run has reached, each builder yields one valid channel
append input — a scope-entered event carrying the run's identity, a
scope-advanced event naming the unit just examined, a finding-reported event
carrying the raised finding, or a terminal run-completed event carrying the
core run-state record; and given any event prefix — partial and in-flight, or
sealed — ``render_surface`` produces a heading from the scope-entered event, a
progress line per scope-advanced event, one severity-prefixed location line per
finding-reported event, and an overall footer only once a run-completed event
is present.
"""

from __future__ import annotations

from typing import Any

from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)

jp = load_journal_projection_module()

NOW = "2026-06-22T00:00:00Z"


def _run_identity() -> Any:
    """The run identity a streaming run carries — no findings; they stream."""
    return jp.RunResult(
        target="spx/example.enabler",
        scope_hash="abc123def456",
        branch_name="work/example",
        branch_slug="work__example",
        head_sha="1" * 40,
        base_ref="main",
        base_sha="2" * 40,
        config_digest="cfg-abc123",
        participants=("audit",),
        scope={"include": ["src/example.py"]},
        started_at="2026-06-22T00:00:00Z",
        completed_at="2026-06-22T00:00:05Z",
        output_paths=("audit-results.json",),
    )


def _streamed_events(
    run: Any, units: tuple[str, ...], findings: tuple[Any, ...]
) -> list[dict]:
    """Assemble the event sequence a streaming run appends as it advances.

    scope-entered, then one scope-advanced per unit examined, then one
    finding-reported per finding raised, then the terminal run-completed whose
    status the consumer derives from the appended finding events.
    """
    events: list[dict] = [jp.scope_entered_event(run, now=NOW)]
    for unit in units:
        events.append(jp.scope_advanced_event(unit, now=NOW))
    for finding in findings:
        events.append(jp.finding_reported_event(finding, now=NOW))
    status = jp.terminal_status(jp.compute_overall(events))
    events.append(jp.run_completed_event(run, status=status, now=NOW))
    return events


def test_scope_entered_event_carries_run_identity() -> None:
    run = _run_identity()
    event = jp.scope_entered_event(run, now=NOW)

    assert event["source"] == jp.EVENT_SOURCE
    assert event["type"] == jp.SCOPE_ENTERED
    data = event["data"]
    assert data["target"] == "spx/example.enabler"
    assert data[jp.RUN_STATE_BRANCH_NAME] == "work/example"
    assert data[jp.RUN_STATE_BRANCH_SLUG] == "work__example"
    assert data[jp.RUN_STATE_HEAD_SHA] == "1" * 40
    assert data[jp.RUN_STATE_BASE_REF] == "main"


def test_scope_advanced_event_names_the_unit() -> None:
    event = jp.scope_advanced_event("src/example.py", now=NOW)

    assert event["type"] == jp.SCOPE_ADVANCED
    assert event["data"]["unit"] == "src/example.py"


def test_finding_reported_event_carries_the_finding() -> None:
    finding = jp.Finding(
        file="a.py", line=10, rule="r", severity=jp.Severity.WARNING, message="m"
    )
    event = jp.finding_reported_event(finding, now=NOW)

    assert event["type"] == jp.FINDING_REPORTED
    data = event["data"]
    assert data["file"] == "a.py"
    assert data["line"] == 10
    assert data["rule"] == "r"
    assert data["severity"] == str(jp.Severity.WARNING)
    assert data["message"] == "m"


def test_run_completed_event_carries_core_run_state() -> None:
    finding = jp.Finding(
        file="a.py",
        line=10,
        rule="r",
        severity=jp.Severity.UNKNOWN,
        message="cannot decide",
    )
    run = _run_identity()
    finding_event = jp.finding_reported_event(finding, now=NOW)
    status = jp.terminal_status(jp.compute_overall([finding_event]))
    completed = jp.run_completed_event(run, status=status, now=NOW)
    data = completed["data"]

    assert completed["source"] == jp.EVENT_SOURCE
    assert completed["type"] == jp.RUN_COMPLETED
    assert data[jp.RUN_STATE_BRANCH_NAME] == "work/example"
    assert data[jp.RUN_STATE_BRANCH_SLUG] == "work__example"
    assert data[jp.RUN_STATE_TARGET_KIND] == jp.JournalTargetKind.BRANCH
    assert data[jp.RUN_STATE_HEAD_SHA] == "1" * 40
    assert data[jp.RUN_STATE_BASE_REF] == "main"
    assert data[jp.RUN_STATE_BASE_SHA] == "2" * 40
    assert data[jp.RUN_STATE_CONFIG_DIGEST] == "cfg-abc123"
    assert data[jp.RUN_STATE_PARTICIPANTS] == ["audit"]
    assert data[jp.RUN_STATE_SCOPE] == {"include": ["src/example.py"]}
    assert data[jp.RUN_STATE_STARTED_AT] == "2026-06-22T00:00:00Z"
    assert data[jp.RUN_STATE_COMPLETED_AT] == "2026-06-22T00:00:05Z"
    assert data[jp.RUN_STATE_OUTPUT_PATHS] == ["audit-results.json"]
    # An UNKNOWN finding rolls up to a FAILED terminal status.
    assert data[jp.RUN_STATE_STATUS] == jp.JournalRunStatus.FAILED


def test_every_builder_yields_a_valid_channel_input() -> None:
    run = _run_identity()
    findings = (
        jp.Finding(
            file="a.py", line=10, rule="r", severity=jp.Severity.WARNING, message="m"
        ),
    )
    events = _streamed_events(run, ("src/example.py",), findings)

    types = [event["type"] for event in events]
    assert types[0] == jp.SCOPE_ENTERED
    assert types[-1] == jp.RUN_COMPLETED
    assert types.count(jp.SCOPE_ADVANCED) == 1
    assert types.count(jp.FINDING_REPORTED) == len(findings)

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


def test_render_surface_over_sealed_prefix_heads_progresses_lists_and_footers() -> None:
    findings = (
        jp.Finding(
            file="a.py", line=7, rule="r1", severity=jp.Severity.REJECT, message="boom"
        ),
        jp.Finding(
            file="b.py", line=None, rule="r2", severity=jp.Severity.INFO, message="note"
        ),
    )
    run = _run_identity()
    events = _streamed_events(run, ("a.py", "b.py"), findings)
    surface = jp.render_surface(events)
    lines = surface.splitlines()

    # The heading line is rendered from the scope-entered event and names the
    # run target, read back from the event the projection itself emitted.
    assert lines[0].startswith("# ")
    assert events[0]["data"]["target"] in lines[0]

    # A progress line per scope-advanced event names the unit examined.
    assert any("a.py" in line and line.startswith("- examined") for line in lines)
    assert any("b.py" in line and line.startswith("- examined") for line in lines)

    # One severity-prefixed location line per finding: a pinned finding renders
    # file:line, and a whole-file finding (line is None) renders the file alone.
    assert any(
        str(jp.Severity.REJECT) in line and "a.py:7" in line and "boom" in line
        for line in lines
    )
    assert any(
        str(jp.Severity.INFO) in line
        and "b.py" in line
        and "b.py:" not in line
        and line.rstrip().endswith("note")
        for line in lines
    )

    # The footer carries the projection's verdict rollup and the core terminal
    # status read from the run-completed event.
    status = events[-1]["data"][jp.RUN_STATE_STATUS]
    assert f"**Overall: {jp.compute_overall(events)} (status: {status})**" in surface


def test_render_surface_over_partial_in_flight_prefix_omits_footer() -> None:
    # A reader resuming from a cursor mid-run sees a prefix with no
    # run-completed event yet: heading, the units examined so far, and the
    # findings raised so far — but no overall footer.
    run = _run_identity()
    in_flight = [
        jp.scope_entered_event(run, now=NOW),
        jp.scope_advanced_event("a.py", now=NOW),
        jp.finding_reported_event(
            jp.Finding(
                file="a.py",
                line=7,
                rule="r1",
                severity=jp.Severity.REJECT,
                message="boom",
            ),
            now=NOW,
        ),
    ]
    surface = jp.render_surface(in_flight)
    lines = surface.splitlines()

    assert lines[0].startswith("# ")
    assert any(line.startswith("- examined a.py") for line in lines)
    assert any("a.py:7" in line and "boom" in line for line in lines)
    # No run-completed event in the prefix, so no overall footer.
    assert "Overall:" not in surface
