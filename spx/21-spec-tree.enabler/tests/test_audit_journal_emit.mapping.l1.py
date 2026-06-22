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
        metadata={"branch": "work/example", "scope_hash": "abc123def456"},
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
