"""Mapping evidence for the audit consumer's run-journal adapter.

Covers the Testing assertion in ``../17-auditing.adr.md``: the consumer-side
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
from typing import Any

import pytest
from outcomeeng_testing.harnesses.audit_journal_emit import load_journal_emit_module
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


def _journal_overall(wrapper: Any) -> Any:
    events = je.events_for_wrapper(wrapper, now="2026-06-22T00:00:00Z")
    return jp.compute_overall(events)


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


@pytest.mark.parametrize("case_name", sorted(_CASES))
def test_adapter_overall_equals_rollup(case_name: str) -> None:
    wrapper = _CASES[case_name]()
    contributor_statuses = tuple(row.status for row in wrapper.rows) + tuple(
        child.overall for child in wrapper.children
    )
    assert _journal_overall(wrapper) == _expected_outcome(contributor_statuses)


def test_adapter_terminal_event_carries_core_run_state_identity() -> None:
    wrapper = _wrapper(rows=(_row("gates", vmod.Status.PASS),), children=())
    events = je.events_for_wrapper(wrapper, now="2026-06-22T00:00:06Z")
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
    del wrapper.metadata[jp.RUN_STATE_HEAD_SHA]

    with pytest.raises(ValueError, match=jp.RUN_STATE_HEAD_SHA):
        je.events_for_wrapper(wrapper, now="2026-06-22T00:00:06Z")


def test_adapter_rejects_missing_base_identity() -> None:
    wrapper = _wrapper(rows=(_row("gates", vmod.Status.PASS),), children=())
    del wrapper.metadata[jp.RUN_STATE_BASE_SHA]

    with pytest.raises(ValueError, match=jp.RUN_STATE_BASE_SHA):
        je.events_for_wrapper(wrapper, now="2026-06-22T00:00:06Z")
