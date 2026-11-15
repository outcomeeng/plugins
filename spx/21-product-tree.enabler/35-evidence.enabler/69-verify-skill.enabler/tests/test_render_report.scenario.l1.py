"""Reachability evidence: the /verify report script checks structured results and renders the report table.

The script is the deterministic half of `report-from-result`. These tests run
its entry point on one spec-assertion result and one decision-rule result,
pin every field of each through the rendered row, and show that a record
lacking any field fails. The cases come from the `verify-result` Evaluate
table of this Node's spec: `cli-state-input` for the spec assertion,
`failed-route` for the decision rule, and `unsupported-tag` for a blocked
result whose null fields render as em dashes.

Design record.

Assertion: the script renders one report row per structured result, path and
line in Subject and nulls as em dashes, and rejects a record lacking a field.
Production subject: the script's entry point, run on a results file.
Case provenance: the `verify-result` table rows named above.
Oracle owner: the rendering contract `report-from-result` states.
Rejected mutation: a row that drops a field, shows a null other than as an em
dash, or a record lacking a field that renders.
Failure observation: the exit code, a rendered row, or the stderr defect line
differs from the expected one.
"""

from __future__ import annotations

import pytest

from outcomeeng_testing.harnesses.verify_report import load_script, run

script = load_script()
Result = script.ResultField
Subject = script.SubjectField

SPEC_ASSERTION = {
    Result.SUBJECT: {
        Subject.PATH: "spx/40-report.capability/report.spec.md",
        Subject.LINE: 9,
        Subject.TEXT: "- state-readout: ALWAYS: the report shows the State that spx spec status --format json prints for the node",
    },
    Result.VERIFICATION_TYPE: "test",
    Result.SPECIALIST: "/test",
    Result.STATUS: "routed",
    Result.EVIDENCE_SHAPE: "path-bearing",
    Result.REASON: "tests/test_state_readout.compliance.l1.py",
}
DECISION_RULE = {
    Result.SUBJECT: {
        Subject.PATH: "spx/20-export.capability/15-publication.adr.md",
        Subject.LINE: 9,
        Subject.TEXT: "- atomic-rename: ALWAYS: publishing an export renames a temporary file onto its path",
    },
    Result.VERIFICATION_TYPE: "test",
    Result.SPECIALIST: "/test",
    Result.STATUS: "capability-required",
    Result.EVIDENCE_SHAPE: "requirement",
    Result.REASON: "/test is not installed",
}
UNSUPPORTED_TAG = {
    Result.SUBJECT: {
        Subject.PATH: "spx/10-build.capability/build.spec.md",
        Subject.LINE: 14,
        Subject.TEXT: None,
    },
    Result.VERIFICATION_TYPE: None,
    Result.SPECIALIST: None,
    Result.STATUS: "blocked",
    Result.EVIDENCE_SHAPE: None,
    Result.REASON: "unsupported-tag-shape",
}


def test_a_spec_assertion_and_a_decision_rule_render_one_row_each_with_every_field() -> (
    None
):
    observed = run([SPEC_ASSERTION, DECISION_RULE, UNSUPPORTED_TAG])

    assert observed.exit_code == 0, observed.stderr
    assert observed.stdout.splitlines() == [
        "| Subject | Verification type | Specialist | Evidence shape | Status | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
        "| spx/40-report.capability/report.spec.md:9 - state-readout: ALWAYS: the report shows the State that spx spec status --format json prints for the node | test | /test | path-bearing | routed | tests/test_state_readout.compliance.l1.py |",
        "| spx/20-export.capability/15-publication.adr.md:9 - atomic-rename: ALWAYS: publishing an export renames a temporary file onto its path | test | /test | requirement | capability-required | /test is not installed |",
        "| spx/10-build.capability/build.spec.md:14 | — | — | — | blocked | unsupported-tag-shape |",
    ]


@pytest.mark.parametrize("missing", list(Result))
def test_a_record_lacking_a_field_fails_and_names_the_field(missing: str) -> None:
    record = {name: value for name, value in DECISION_RULE.items() if name != missing}

    observed = run([record])

    assert observed.exit_code != 0
    assert observed.stdout == ""
    assert f"lacks {missing}" in observed.stderr
