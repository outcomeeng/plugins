"""Mapping tests for deterministic merge-gate policy helpers."""

from __future__ import annotations

import pytest

from outcomeeng.merging_policy import (
    AUDITOR_BLOCKING_FINDING_VERDICTS,
    AUDITOR_BLOCKING_OVERALLS,
    AUDITOR_BLOCKING_ROW_STATUSES,
    CHECK_RUN_NON_TERMINAL_STATUSES,
    CHECK_RUN_SUCCESS_CONCLUSIONS,
    CHECK_RUN_TERMINAL_NOT_SUCCESS_CONCLUSIONS,
    CHECK_RUN_TERMINAL_STATUS,
    FIELD_CONCLUSION,
    FIELD_FINDINGS,
    FIELD_IN_PR_DIFF,
    FIELD_KIND,
    FIELD_OVERALL,
    FIELD_PRESENT,
    FIELD_ROWS,
    FIELD_STATE,
    FIELD_STATUS,
    FIELD_VERDICT,
    STATUS_CONTEXT_NON_TERMINAL_STATES,
    STATUS_CONTEXT_SUCCESS_STATES,
    STATUS_CONTEXT_TERMINAL_NOT_SUCCESS_STATES,
    AuditorFindingVerdict,
    AuditorOverall,
    AuditorRequiredAction,
    AuditorRowStatus,
    CheckRunConclusion,
    CheckRunStatus,
    MergeAction,
    ProductionReadiness,
    RequiredCheckClassification,
    RequiredCheckKind,
    classify_required_check,
    decide_auditor_verdict,
    decide_production_readiness,
)


@pytest.mark.parametrize("conclusion", sorted(CHECK_RUN_SUCCESS_CONCLUSIONS))
def test_check_run_completed_success_maps_to_terminal_green(
    conclusion: CheckRunConclusion,
) -> None:
    decision = classify_required_check(
        {
            FIELD_KIND: RequiredCheckKind.CHECK_RUN,
            FIELD_PRESENT: True,
            FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
            FIELD_CONCLUSION: conclusion,
        }
    )

    assert decision.terminal_green is True
    assert decision.classification is RequiredCheckClassification.TERMINAL_GREEN


@pytest.mark.parametrize("status", sorted(CHECK_RUN_NON_TERMINAL_STATUSES))
def test_check_run_non_terminal_status_maps_to_not_terminal(
    status: CheckRunStatus,
) -> None:
    decision = classify_required_check(
        {
            FIELD_KIND: RequiredCheckKind.CHECK_RUN,
            FIELD_PRESENT: True,
            FIELD_STATUS: status,
            FIELD_CONCLUSION: None,
        }
    )

    assert decision.terminal_green is False
    assert decision.classification is RequiredCheckClassification.NOT_TERMINAL


@pytest.mark.parametrize(
    "conclusion",
    sorted(CHECK_RUN_TERMINAL_NOT_SUCCESS_CONCLUSIONS),
)
def test_check_run_completed_non_success_maps_to_terminal_not_success(
    conclusion: CheckRunConclusion,
) -> None:
    decision = classify_required_check(
        {
            FIELD_KIND: RequiredCheckKind.CHECK_RUN,
            FIELD_PRESENT: True,
            FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
            FIELD_CONCLUSION: conclusion,
        }
    )

    assert decision.terminal_green is False
    assert decision.classification is RequiredCheckClassification.TERMINAL_NOT_SUCCESS


def test_absent_required_check_maps_to_absent() -> None:
    decision = classify_required_check(
        {FIELD_KIND: RequiredCheckKind.CHECK_RUN, FIELD_PRESENT: False}
    )

    assert decision.terminal_green is False
    assert decision.classification is RequiredCheckClassification.ABSENT


@pytest.mark.parametrize("state", sorted(STATUS_CONTEXT_SUCCESS_STATES))
def test_status_context_success_maps_to_terminal_green(
    state: object,
) -> None:
    decision = classify_required_check(
        {
            FIELD_KIND: RequiredCheckKind.STATUS_CONTEXT,
            FIELD_PRESENT: True,
            FIELD_STATE: state,
        }
    )

    assert decision.terminal_green is True
    assert decision.classification is RequiredCheckClassification.TERMINAL_GREEN


@pytest.mark.parametrize("state", sorted(STATUS_CONTEXT_NON_TERMINAL_STATES))
def test_status_context_non_terminal_state_maps_to_not_terminal(
    state: object,
) -> None:
    decision = classify_required_check(
        {
            FIELD_KIND: RequiredCheckKind.STATUS_CONTEXT,
            FIELD_PRESENT: True,
            FIELD_STATE: state,
        }
    )

    assert decision.terminal_green is False
    assert decision.classification is RequiredCheckClassification.NOT_TERMINAL


@pytest.mark.parametrize("state", sorted(STATUS_CONTEXT_TERMINAL_NOT_SUCCESS_STATES))
def test_status_context_terminal_non_success_maps_to_terminal_not_success(
    state: object,
) -> None:
    decision = classify_required_check(
        {
            FIELD_KIND: RequiredCheckKind.STATUS_CONTEXT,
            FIELD_PRESENT: True,
            FIELD_STATE: state,
        }
    )

    assert decision.terminal_green is False
    assert decision.classification is RequiredCheckClassification.TERMINAL_NOT_SUCCESS


@pytest.mark.parametrize(
    ("recognition_mechanism_declared", "production_relevant", "operator_approved"),
    (
        (False, None, False),
        (True, False, False),
        (True, True, True),
    ),
)
def test_production_readiness_permissive_or_approved_inputs_map_to_merge(
    recognition_mechanism_declared: bool,
    production_relevant: bool | None,
    operator_approved: bool,
) -> None:
    decision = decide_production_readiness(
        recognition_mechanism_declared=recognition_mechanism_declared,
        production_relevant=production_relevant,
        operator_approved=operator_approved,
    )

    assert decision.production_readiness is ProductionReadiness.HOLD
    assert decision.merge_action is MergeAction.MERGE


def test_production_relevant_unapproved_change_maps_to_await_approval() -> None:
    decision = decide_production_readiness(
        recognition_mechanism_declared=True,
        production_relevant=True,
        operator_approved=False,
    )

    assert decision.production_readiness is ProductionReadiness.WITHHOLD
    assert decision.merge_action is MergeAction.AWAIT_APPROVAL


@pytest.mark.parametrize("overall", sorted(AUDITOR_BLOCKING_OVERALLS))
def test_auditor_blocking_overall_maps_to_fix_before_merge(
    overall: AuditorOverall,
) -> None:
    decision = decide_auditor_verdict(
        {
            FIELD_IN_PR_DIFF: True,
            FIELD_OVERALL: overall,
            FIELD_ROWS: [{FIELD_STATUS: AuditorRowStatus.PASS}],
            FIELD_FINDINGS: [],
        }
    )

    assert decision.required_action is AuditorRequiredAction.FIX_BEFORE_MERGE
    assert decision.merge_blocked is True


@pytest.mark.parametrize("status", sorted(AUDITOR_BLOCKING_ROW_STATUSES))
def test_auditor_blocking_row_maps_to_fix_before_merge(
    status: AuditorRowStatus,
) -> None:
    decision = decide_auditor_verdict(
        {
            FIELD_IN_PR_DIFF: True,
            FIELD_OVERALL: AuditorOverall.APPROVED,
            FIELD_ROWS: [{FIELD_STATUS: status}],
            FIELD_FINDINGS: [],
        }
    )

    assert decision.required_action is AuditorRequiredAction.FIX_BEFORE_MERGE
    assert decision.merge_blocked is True


@pytest.mark.parametrize("verdict", sorted(AUDITOR_BLOCKING_FINDING_VERDICTS))
def test_auditor_blocking_finding_maps_to_fix_before_merge(
    verdict: AuditorFindingVerdict,
) -> None:
    decision = decide_auditor_verdict(
        {
            FIELD_IN_PR_DIFF: True,
            FIELD_OVERALL: AuditorOverall.APPROVED,
            FIELD_ROWS: [{FIELD_STATUS: AuditorRowStatus.PASS}],
            FIELD_FINDINGS: [{FIELD_VERDICT: verdict}],
        }
    )

    assert decision.required_action is AuditorRequiredAction.FIX_BEFORE_MERGE
    assert decision.merge_blocked is True


def test_auditor_non_blocking_verdict_maps_to_no_repair() -> None:
    decision = decide_auditor_verdict(
        {
            FIELD_IN_PR_DIFF: True,
            FIELD_OVERALL: AuditorOverall.APPROVED,
            FIELD_ROWS: [{FIELD_STATUS: AuditorRowStatus.PASS}],
            FIELD_FINDINGS: [
                {FIELD_VERDICT: AuditorFindingVerdict.INFO},
                {FIELD_VERDICT: AuditorFindingVerdict.WARNING},
            ],
        }
    )

    assert decision.required_action is AuditorRequiredAction.NO_REPAIR
    assert decision.merge_blocked is False


def test_auditor_out_of_pr_verdict_maps_to_track_out_of_pr() -> None:
    decision = decide_auditor_verdict(
        {
            FIELD_IN_PR_DIFF: False,
            FIELD_OVERALL: AuditorOverall.REJECTED,
            FIELD_ROWS: [{FIELD_STATUS: AuditorRowStatus.FAIL}],
            FIELD_FINDINGS: [{FIELD_VERDICT: AuditorFindingVerdict.REJECT}],
        }
    )

    assert decision.required_action is AuditorRequiredAction.TRACK_OUT_OF_PR
    assert decision.merge_blocked is False
