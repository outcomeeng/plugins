"""Mapping evidence for the audit consumer's run-journal adapter.

Covers the Testing assertion in ``../17-audit.adr.md``: the consumer-side
adapter (``journal_emit.py``) maps an audit wrapper verdict onto journal
events whose rolled-up overall equals the verdict toolchain's rollup over that
wrapper, so routing the verdict through the ``spx journal`` channel never
changes its outcome.

The oracle is the rollup rule applied independently to each wrapper's row and
child statuses — never read back from ``verdict.roll_up`` or from the adapter.
Cases exercise both representation paths: a ``FAIL`` row carrying a ``REJECT``
finding maps through a real finding, while a finding-less ``FAIL`` gate row and
every ``UNKNOWN`` contributor must be synthesized — ``verdict.py`` has no
``UNKNOWN`` finding severity and an orchestrator gate row carries no findings,
so the adapter cannot rely on a real finding to carry those outcomes.
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

import pytest
from outcomeeng_testing.harnesses.audit_journal_emit import (
    JOURNAL_EMIT_MODULE_PATH,
    load_journal_emit_module,
)
from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)
from outcomeeng_testing.harnesses.verdict_toolchain import load_verdict_module

je = load_journal_emit_module()
jp = load_journal_projection_module()
vmod = load_verdict_module()


def _reject_finding(name: str) -> Any:
    return vmod.Finding(
        id=f"{name}-1",
        file="a.py",
        line=1,
        rule=name,
        severity=vmod.Severity.REJECT,
        message="rejecting finding",
    )


def _info_finding(name: str) -> Any:
    return vmod.Finding(
        id=f"{name}-1",
        file="a.py",
        line=2,
        rule=name,
        severity=vmod.Severity.INFO,
        message="advisory finding",
    )


def _row(name: str, status: Any, findings: tuple[Any, ...] = ()) -> Any:
    return vmod.Row(name=name, status=status, findings=findings)


def _leaf_child(name: str, overall: Any, findings: tuple[Any, ...] = ()) -> Any:
    return vmod.Verdict(
        schema_version=vmod.SCHEMA_VERSION,
        skill=name,
        target=f"spx/{name}",
        overall=overall,
        rows=(_row(name, overall, findings),) if findings else (),
    )


def _expected_outcome(statuses: tuple[Any, ...]) -> Any:
    """The rollup rule applied independently to the contributor statuses."""
    string_statuses = [str(status) for status in statuses]
    if any(status in ("FAIL", "REJECTED") for status in string_statuses):
        return jp.Outcome.REJECTED
    if any(status == "UNKNOWN" for status in string_statuses):
        return jp.Outcome.UNKNOWN
    return jp.Outcome.APPROVED


def _wrapper(rows: tuple[Any, ...], children: tuple[Any, ...]) -> Any:
    contributor_statuses = tuple(row.status for row in rows) + tuple(
        child.overall for child in children
    )
    expected = _expected_outcome(contributor_statuses)
    overall = {
        jp.Outcome.REJECTED: vmod.Status.REJECTED,
        jp.Outcome.UNKNOWN: vmod.Status.UNKNOWN,
        jp.Outcome.APPROVED: vmod.Status.APPROVED,
    }[expected]
    return vmod.Verdict(
        schema_version=vmod.SCHEMA_VERSION,
        skill="audit",
        target="spx/example.enabler",
        overall=overall,
        rows=rows,
        children=children,
        metadata={
            jp.RUN_STATE_SCOPE_HASH: "abc123def456",
            jp.RUN_STATE_BRANCH_NAME: "work/example",
            jp.RUN_STATE_BRANCH_SLUG: "work__example",
            jp.RUN_STATE_HEAD_SHA: "1" * 40,
            jp.RUN_STATE_BASE_REF: "main",
            jp.RUN_STATE_BASE_SHA: "2" * 40,
            jp.RUN_STATE_CONFIG_DIGEST: "cfg-abc123",
            jp.RUN_STATE_PARTICIPANTS: json.dumps(["audit"]),
            jp.RUN_STATE_SCOPE: json.dumps({"include": ["src/example.py"]}),
            jp.RUN_STATE_STARTED_AT: "2026-06-22T00:00:00Z",
            jp.RUN_STATE_COMPLETED_AT: "2026-06-22T00:00:05Z",
            jp.RUN_STATE_OUTPUT_PATHS: json.dumps(["audit-results.json"]),
        },
    )


def _metadata(wrapper: Any) -> Any:
    return je.metadata_from_values(
        target=wrapper.target,
        scope_hash=wrapper.metadata[jp.RUN_STATE_SCOPE_HASH],
        branch_name=wrapper.metadata[jp.RUN_STATE_BRANCH_NAME],
        branch_slug=wrapper.metadata[jp.RUN_STATE_BRANCH_SLUG],
        head_sha=wrapper.metadata[jp.RUN_STATE_HEAD_SHA],
        base_ref=wrapper.metadata[jp.RUN_STATE_BASE_REF],
        base_sha=wrapper.metadata[jp.RUN_STATE_BASE_SHA],
        config_digest=wrapper.metadata[jp.RUN_STATE_CONFIG_DIGEST],
        participants=("audit",),
        scope={"include": ["src/example.py"]},
        started_at=wrapper.metadata[jp.RUN_STATE_STARTED_AT],
        completed_at=wrapper.metadata[jp.RUN_STATE_COMPLETED_AT],
        output_paths=("audit-results.json",),
        target_kind=jp.JournalTargetKind.BRANCH,
    )


def _pull_request_metadata(wrapper: Any) -> Any:
    return je.metadata_from_values(
        target=wrapper.target,
        scope_hash=wrapper.metadata[jp.RUN_STATE_SCOPE_HASH],
        branch_name=wrapper.metadata[jp.RUN_STATE_BRANCH_NAME],
        branch_slug=wrapper.metadata[jp.RUN_STATE_BRANCH_SLUG],
        head_sha=wrapper.metadata[jp.RUN_STATE_HEAD_SHA],
        base_ref=wrapper.metadata[jp.RUN_STATE_BASE_REF],
        base_sha=wrapper.metadata[jp.RUN_STATE_BASE_SHA],
        config_digest=wrapper.metadata[jp.RUN_STATE_CONFIG_DIGEST],
        participants=("audit",),
        scope={"include": ["src/example.py"]},
        started_at=wrapper.metadata[jp.RUN_STATE_STARTED_AT],
        completed_at=wrapper.metadata[jp.RUN_STATE_COMPLETED_AT],
        output_paths=("audit-results.json",),
        target_kind=jp.JournalTargetKind.PULL_REQUEST,
        pull_request_number=123,
    )


def _streamed_events(wrapper: Any) -> list[dict[str, object]]:
    now = "2026-06-22T00:00:00Z"
    metadata = _metadata(wrapper)
    events = [je.scope_entered_event(metadata, now=now)]
    for child in wrapper.children:
        events.append(je.scope_advanced_event(child.skill, now=now))
        events.extend(je.finding_events_for_child(child, now=now))
    if not wrapper.children:
        events.extend(je.finding_events_for_verdict(wrapper, now=now))
    events.append(
        je.run_completed_event(
            metadata,
            events,
            completed_at=wrapper.metadata[jp.RUN_STATE_COMPLETED_AT],
            now=now,
        )
    )
    return events


def _run_journal_emit_cli(*args: str, stdin: str = "") -> str:
    result = subprocess.run(  # noqa: S603 — fixed argv, no shell
        [sys.executable, str(JOURNAL_EMIT_MODULE_PATH), *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _json_lines(text: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in text.splitlines() if line]


def _journal_overall(wrapper: Any) -> Any:
    return jp.compute_overall(_streamed_events(wrapper))


# Each case names the wrapper structure and the contributor statuses the oracle
# rolls up independently. PASS/FAIL/UNKNOWN are the source-owned vocabulary
# (vmod.Status); the expected journal Outcome is derived from the rule, never
# read back from the adapter or verdict.roll_up.
_CASES = {
    "all-pass-rows": lambda: _wrapper(
        rows=(_row("gates", vmod.Status.PASS), _row("tests", vmod.Status.PASS)),
        children=(),
    ),
    "fail-row-with-reject-finding": lambda: _wrapper(
        rows=(_row("evidence", vmod.Status.FAIL, (_reject_finding("evidence"),)),),
        children=(),
    ),
    "fail-gate-row-no-findings": lambda: _wrapper(
        rows=(_row("gates", vmod.Status.FAIL),),
        children=(),
    ),
    "unknown-row-no-findings": lambda: _wrapper(
        rows=(_row("determinism", vmod.Status.UNKNOWN),),
        children=(),
    ),
    "unknown-row-with-pass-rows": lambda: _wrapper(
        rows=(_row("gates", vmod.Status.PASS), _row("scope", vmod.Status.UNKNOWN)),
        children=(),
    ),
    "fail-and-unknown-rows-reject-dominates": lambda: _wrapper(
        rows=(
            _row("evidence", vmod.Status.FAIL, (_reject_finding("evidence"),)),
            _row("scope", vmod.Status.UNKNOWN),
        ),
        children=(),
    ),
    "info-findings-only-approve": lambda: _wrapper(
        rows=(_row("style", vmod.Status.PASS, (_info_finding("style"),)),),
        children=(),
    ),
    "child-fail-with-reject-finding": lambda: _wrapper(
        rows=(_row("gates", vmod.Status.PASS),),
        children=(
            _leaf_child("audit-python", vmod.Status.FAIL, (_reject_finding("python"),)),
        ),
    ),
    "child-fail-no-findings": lambda: _wrapper(
        rows=(_row("gates", vmod.Status.PASS),),
        children=(_leaf_child("audit-typescript", vmod.Status.FAIL),),
    ),
    "child-unknown-no-findings": lambda: _wrapper(
        rows=(_row("gates", vmod.Status.PASS),),
        children=(_leaf_child("audit-rust", vmod.Status.UNKNOWN),),
    ),
    "all-pass-rows-and-children": lambda: _wrapper(
        rows=(_row("gates", vmod.Status.PASS),),
        children=(_leaf_child("audit-python", vmod.Status.PASS),),
    ),
}


_TERMINAL_STATUS_CASES = {
    "approved-wrapper": (
        lambda: _wrapper(rows=(_row("gates", vmod.Status.PASS),), children=()),
        jp.JournalRunStatus.APPROVED,
    ),
    "rejected-wrapper": (
        lambda: _wrapper(rows=(_row("gates", vmod.Status.FAIL),), children=()),
        jp.JournalRunStatus.REJECTED,
    ),
    "unknown-wrapper": (
        lambda: _wrapper(rows=(_row("gates", vmod.Status.UNKNOWN),), children=()),
        jp.JournalRunStatus.FAILED,
    ),
}


@pytest.mark.parametrize("case_name", sorted(_CASES))
def test_adapter_overall_equals_rollup(case_name: str) -> None:
    wrapper = _CASES[case_name]()
    contributor_statuses = tuple(row.status for row in wrapper.rows) + tuple(
        child.overall for child in wrapper.children
    )
    assert _journal_overall(wrapper) == _expected_outcome(contributor_statuses)


@pytest.mark.parametrize("case_name", sorted(_TERMINAL_STATUS_CASES))
def test_adapter_terminal_status_maps_wrapper_outcome(case_name: str) -> None:
    wrapper_factory, expected_status = _TERMINAL_STATUS_CASES[case_name]
    events = _streamed_events(wrapper_factory())
    data = events[-1]["data"]

    assert events[-1]["type"] == jp.RUN_COMPLETED
    assert data[jp.RUN_STATE_STATUS] == expected_status


def test_adapter_terminal_event_carries_core_run_state_identity() -> None:
    wrapper = _wrapper(rows=(_row("gates", vmod.Status.PASS),), children=())
    events = _streamed_events(wrapper)
    data = events[-1]["data"]

    assert events[-1]["type"] == jp.RUN_COMPLETED
    assert data[jp.RUN_STATE_BRANCH_NAME] == wrapper.metadata[jp.RUN_STATE_BRANCH_NAME]
    assert data[jp.RUN_STATE_BRANCH_SLUG] == wrapper.metadata[jp.RUN_STATE_BRANCH_SLUG]
    assert data[jp.RUN_STATE_HEAD_SHA] == wrapper.metadata[jp.RUN_STATE_HEAD_SHA]
    assert data[jp.RUN_STATE_BASE_REF] == wrapper.metadata[jp.RUN_STATE_BASE_REF]
    assert data[jp.RUN_STATE_BASE_SHA] == wrapper.metadata[jp.RUN_STATE_BASE_SHA]
    assert (
        data[jp.RUN_STATE_CONFIG_DIGEST] == wrapper.metadata[jp.RUN_STATE_CONFIG_DIGEST]
    )
    assert data[jp.RUN_STATE_PARTICIPANTS] == ["audit"]
    assert data[jp.RUN_STATE_SCOPE] == {"include": ["src/example.py"]}
    assert data[jp.RUN_STATE_STARTED_AT] == "2026-06-22T00:00:00Z"
    assert data[jp.RUN_STATE_COMPLETED_AT] == "2026-06-22T00:00:05Z"
    assert data[jp.RUN_STATE_OUTPUT_PATHS] == ["audit-results.json"]
    assert data[jp.RUN_STATE_STATUS] == jp.JournalRunStatus.APPROVED


def test_adapter_rejects_missing_head_identity() -> None:
    wrapper = _wrapper(rows=(_row("gates", vmod.Status.PASS),), children=())

    with pytest.raises(ValueError, match="headSha"):
        je.metadata_from_values(
            target=wrapper.target,
            scope_hash=wrapper.metadata[jp.RUN_STATE_SCOPE_HASH],
            branch_name=wrapper.metadata[jp.RUN_STATE_BRANCH_NAME],
            branch_slug=wrapper.metadata[jp.RUN_STATE_BRANCH_SLUG],
            head_sha="",
            base_ref=wrapper.metadata[jp.RUN_STATE_BASE_REF],
            base_sha=wrapper.metadata[jp.RUN_STATE_BASE_SHA],
            config_digest=wrapper.metadata[jp.RUN_STATE_CONFIG_DIGEST],
            participants=("audit",),
            scope={"include": ["src/example.py"]},
            started_at=wrapper.metadata[jp.RUN_STATE_STARTED_AT],
            completed_at=wrapper.metadata[jp.RUN_STATE_COMPLETED_AT],
            output_paths=("audit-results.json",),
            target_kind=jp.JournalTargetKind.BRANCH,
        )


def test_adapter_rejects_missing_base_identity() -> None:
    wrapper = _wrapper(rows=(_row("gates", vmod.Status.PASS),), children=())

    with pytest.raises(ValueError, match="baseSha"):
        je.metadata_from_values(
            target=wrapper.target,
            scope_hash=wrapper.metadata[jp.RUN_STATE_SCOPE_HASH],
            branch_name=wrapper.metadata[jp.RUN_STATE_BRANCH_NAME],
            branch_slug=wrapper.metadata[jp.RUN_STATE_BRANCH_SLUG],
            head_sha=wrapper.metadata[jp.RUN_STATE_HEAD_SHA],
            base_ref=wrapper.metadata[jp.RUN_STATE_BASE_REF],
            base_sha="",
            config_digest=wrapper.metadata[jp.RUN_STATE_CONFIG_DIGEST],
            participants=("audit",),
            scope={"include": ["src/example.py"]},
            started_at=wrapper.metadata[jp.RUN_STATE_STARTED_AT],
            completed_at=wrapper.metadata[jp.RUN_STATE_COMPLETED_AT],
            output_paths=("audit-results.json",),
            target_kind=jp.JournalTargetKind.BRANCH,
        )


def test_adapter_rejects_non_positive_pull_request_number() -> None:
    wrapper = _wrapper(rows=(_row("gates", vmod.Status.PASS),), children=())
    wrapper.metadata[jp.RUN_STATE_PULL_REQUEST_NUMBER] = "0"

    with pytest.raises(ValueError, match="positive integer"):
        je.metadata_from_values(
            target=wrapper.target,
            scope_hash=wrapper.metadata[jp.RUN_STATE_SCOPE_HASH],
            branch_name=wrapper.metadata[jp.RUN_STATE_BRANCH_NAME],
            branch_slug=wrapper.metadata[jp.RUN_STATE_BRANCH_SLUG],
            head_sha=wrapper.metadata[jp.RUN_STATE_HEAD_SHA],
            base_ref=wrapper.metadata[jp.RUN_STATE_BASE_REF],
            base_sha=wrapper.metadata[jp.RUN_STATE_BASE_SHA],
            config_digest=wrapper.metadata[jp.RUN_STATE_CONFIG_DIGEST],
            participants=("audit",),
            scope={"include": ["src/example.py"]},
            started_at=wrapper.metadata[jp.RUN_STATE_STARTED_AT],
            completed_at=wrapper.metadata[jp.RUN_STATE_COMPLETED_AT],
            output_paths=("audit-results.json",),
            target_kind=jp.JournalTargetKind.PULL_REQUEST,
            pull_request_number=0,
        )


def test_adapter_serializes_pull_request_run_metadata() -> None:
    wrapper = _wrapper(rows=(_row("gates", vmod.Status.PASS),), children=())

    metadata = _pull_request_metadata(wrapper)
    event = je.run_completed_event(
        metadata,
        [],
        completed_at=wrapper.metadata[jp.RUN_STATE_COMPLETED_AT],
        now="2026-06-22T00:00:00Z",
    )
    data = event["data"]

    assert data[jp.RUN_STATE_TARGET_KIND] == jp.JournalTargetKind.PULL_REQUEST
    assert data[jp.RUN_STATE_PULL_REQUEST_NUMBER] == 123


def test_adapter_cli_streams_and_renders_journal_prefix() -> None:
    wrapper = _wrapper(
        rows=(_row("gates", vmod.Status.PASS),),
        children=(
            _leaf_child("audit-python", vmod.Status.PASS),
            _leaf_child("audit-rust", vmod.Status.FAIL, (_reject_finding("rust"),)),
        ),
    )

    metadata_json = _run_journal_emit_cli(
        "metadata",
        "--target",
        wrapper.target,
        "--scope-hash",
        wrapper.metadata[jp.RUN_STATE_SCOPE_HASH],
        "--branch-name",
        wrapper.metadata[jp.RUN_STATE_BRANCH_NAME],
        "--branch-slug",
        wrapper.metadata[jp.RUN_STATE_BRANCH_SLUG],
        "--head-sha",
        wrapper.metadata[jp.RUN_STATE_HEAD_SHA],
        "--base-ref",
        wrapper.metadata[jp.RUN_STATE_BASE_REF],
        "--base-sha",
        wrapper.metadata[jp.RUN_STATE_BASE_SHA],
        "--config-digest",
        wrapper.metadata[jp.RUN_STATE_CONFIG_DIGEST],
        "--participants-json",
        json.dumps(["audit"]),
        "--scope-json",
        json.dumps({"include": ["src/example.py"]}),
        "--started-at",
        wrapper.metadata[jp.RUN_STATE_STARTED_AT],
        "--completed-at",
        wrapper.metadata[jp.RUN_STATE_COMPLETED_AT],
        "--output-paths-json",
        json.dumps(["audit-results.json"]),
    )
    events = [
        json.loads(
            _run_journal_emit_cli(
                "scope-entered",
                "--metadata",
                metadata_json,
                "--now",
                wrapper.metadata[jp.RUN_STATE_STARTED_AT],
            )
        )
    ]
    for child in wrapper.children:
        events.append(
            json.loads(
                _run_journal_emit_cli(
                    "scope-advanced",
                    "--unit",
                    child.skill,
                    "--now",
                    wrapper.metadata[jp.RUN_STATE_STARTED_AT],
                )
            )
        )
        events.extend(
            _json_lines(
                _run_journal_emit_cli(
                    "findings-reported",
                    "--now",
                    wrapper.metadata[jp.RUN_STATE_STARTED_AT],
                    stdin=vmod.dump_json(child),
                )
            )
        )
    events.append(
        json.loads(
            _run_journal_emit_cli(
                "run-completed",
                "--metadata",
                metadata_json,
                "--completed-at",
                wrapper.metadata[jp.RUN_STATE_COMPLETED_AT],
                "--now",
                wrapper.metadata[jp.RUN_STATE_COMPLETED_AT],
                stdin=json.dumps(events),
            )
        )
    )

    rendered = _run_journal_emit_cli("render", stdin=json.dumps(events))
    rendered_json = json.loads(rendered)
    terminal_data = events[-1]["data"]

    assert [event["type"] for event in events] == [
        jp.SCOPE_ENTERED,
        jp.SCOPE_ADVANCED,
        jp.SCOPE_ADVANCED,
        jp.FINDING_REPORTED,
        jp.RUN_COMPLETED,
    ]
    assert terminal_data[jp.RUN_STATE_STATUS] == jp.JournalRunStatus.REJECTED
    assert rendered_json["overall"] == jp.Outcome.REJECTED


def test_adapter_streams_partition_progress_before_terminal_event() -> None:
    wrapper = _wrapper(
        rows=(_row("gates", vmod.Status.PASS),),
        children=(
            _leaf_child("audit-python", vmod.Status.PASS),
            _leaf_child("audit-rust", vmod.Status.FAIL, (_reject_finding("rust"),)),
        ),
    )

    events = _streamed_events(wrapper)

    assert [event["type"] for event in events] == [
        jp.SCOPE_ENTERED,
        jp.SCOPE_ADVANCED,
        jp.SCOPE_ADVANCED,
        jp.FINDING_REPORTED,
        jp.RUN_COMPLETED,
    ]
    assert events[1]["data"]["unit"] == "audit-python"
    assert events[2]["data"]["unit"] == "audit-rust"
    assert events[3]["data"]["rule"] == "rust"
    assert jp.compute_overall(events) == jp.Outcome.REJECTED
