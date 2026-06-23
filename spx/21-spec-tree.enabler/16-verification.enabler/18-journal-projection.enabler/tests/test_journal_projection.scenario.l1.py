"""Scenario evidence for the run-journal projection's ``build_events`` and
``render_surface``.

Covers the scenario assertions in ``../journal-projection.md``: given a
verification run's results, ``build_events`` yields a scope-entered event,
one finding-reported event per finding, and a terminal run-completed event,
each a valid channel append input; and given a sealed event prefix,
``render_surface`` produces a heading from the scope-entered event, one
severity-prefixed location line per finding, and an overall footer from the
run-completed event.
"""

from __future__ import annotations

from typing import Any

from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)

jp = load_journal_projection_module()


def _run_with(findings: tuple[Any, ...]) -> Any:
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


def test_build_events_terminal_event_carries_core_run_state() -> None:
    findings = (
        jp.Finding(
            file="a.py",
            line=10,
            rule="r",
            severity=jp.Severity.UNKNOWN,
            message="cannot decide",
        ),
    )
    events = jp.build_events(_run_with(findings), now="2026-06-22T00:00:06Z")
    completed = events[-1]
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
    assert data[jp.RUN_STATE_STATUS] == jp.JournalRunStatus.FAILED


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


def test_render_surface_heads_lists_findings_and_footers() -> None:
    findings = (
        jp.Finding(
            file="a.py", line=7, rule="r1", severity=jp.Severity.REJECT, message="boom"
        ),
        jp.Finding(
            file="b.py", line=None, rule="r2", severity=jp.Severity.INFO, message="note"
        ),
    )
    events = jp.build_events(_run_with(findings), now="2026-06-22T00:00:00Z")
    surface = jp.render_surface(events)
    lines = surface.splitlines()

    # The heading line is rendered from the scope-entered event and names the
    # run target, read back from the event the projection itself emitted.
    assert lines[0].startswith("# ")
    assert events[0]["data"]["target"] in lines[0]

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
