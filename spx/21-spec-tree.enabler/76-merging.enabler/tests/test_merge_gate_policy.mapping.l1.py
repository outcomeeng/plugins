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
    FIELD_SKIP_CAUSE,
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
    DeliveryAction,
    DeliveryReadiness,
    MergeAction,
    ProductionReadiness,
    RequiredCheckClassification,
    RequiredCheckKind,
    ReviewCheckAction,
    ReviewCheckSkipCause,
    classify_required_check,
    decide_auditor_verdict,
    decide_deploy_action,
    decide_production_readiness,
    decide_release_action,
    decide_review_check,
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


def test_successful_review_check_maps_to_surface_inspection() -> None:
    decision = decide_review_check(
        {
            FIELD_KIND: RequiredCheckKind.CHECK_RUN,
            FIELD_PRESENT: True,
            FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
            FIELD_CONCLUSION: CheckRunConclusion.SUCCESS,
        }
    )

    assert decision.required_action is ReviewCheckAction.INSPECT_REVIEW_SURFACES


def test_absent_review_check_maps_to_wait_for_review() -> None:
    decision = decide_review_check(
        {FIELD_KIND: RequiredCheckKind.CHECK_RUN, FIELD_PRESENT: False}
    )

    assert decision.required_action is ReviewCheckAction.WAIT_FOR_REVIEW


@pytest.mark.parametrize("status", sorted(CHECK_RUN_NON_TERMINAL_STATUSES))
def test_non_terminal_review_check_maps_to_wait_for_review(
    status: CheckRunStatus,
) -> None:
    decision = decide_review_check(
        {
            FIELD_KIND: RequiredCheckKind.CHECK_RUN,
            FIELD_PRESENT: True,
            FIELD_STATUS: status,
            FIELD_CONCLUSION: None,
        }
    )

    assert decision.required_action is ReviewCheckAction.WAIT_FOR_REVIEW


@pytest.mark.parametrize(
    "conclusion",
    sorted(CHECK_RUN_TERMINAL_NOT_SUCCESS_CONCLUSIONS - {CheckRunConclusion.SKIPPED}),
)
def test_failed_review_check_maps_to_merge_blocked(
    conclusion: CheckRunConclusion,
) -> None:
    decision = decide_review_check(
        {
            FIELD_KIND: RequiredCheckKind.CHECK_RUN,
            FIELD_PRESENT: True,
            FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
            FIELD_CONCLUSION: conclusion,
        }
    )

    assert (
        decision.required_action is ReviewCheckAction.MERGE_BLOCKED_REVIEW_CHECK_FAILED
    )


def test_non_design_skipped_review_check_maps_to_merge_blocked() -> None:
    decision = decide_review_check(
        {
            FIELD_KIND: RequiredCheckKind.CHECK_RUN,
            FIELD_PRESENT: True,
            FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
            FIELD_CONCLUSION: CheckRunConclusion.SKIPPED,
            FIELD_SKIP_CAUSE: ReviewCheckSkipCause.PATH_FILTER,
        }
    )

    assert (
        decision.required_action is ReviewCheckAction.MERGE_BLOCKED_REVIEW_CHECK_SKIPPED
    )


def test_self_modifying_skipped_review_check_maps_to_mention_review() -> None:
    decision = decide_review_check(
        {
            FIELD_KIND: RequiredCheckKind.CHECK_RUN,
            FIELD_PRESENT: True,
            FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
            FIELD_CONCLUSION: CheckRunConclusion.SKIPPED,
            FIELD_SKIP_CAUSE: ReviewCheckSkipCause.SELF_MODIFYING_WORKFLOW,
        }
    )

    assert decision.required_action is ReviewCheckAction.MENTION_REVIEW_NEEDED


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


def test_absent_deploy_declaration_maps_to_skip_without_blocking_later_phases() -> None:
    decision = decide_deploy_action(
        declared=False,
        authorization_predicate_satisfied=False,
    )

    assert decision.readiness is DeliveryReadiness.HOLD
    assert decision.delivery_action is DeliveryAction.SKIP
    assert decision.blocks_later_phases is False


def test_unauthorized_deploy_declaration_maps_to_await_authorization() -> None:
    decision = decide_deploy_action(
        declared=True,
        authorization_predicate_satisfied=False,
    )

    assert decision.readiness is DeliveryReadiness.WITHHOLD
    assert decision.delivery_action is DeliveryAction.AWAIT_DEPLOYMENT_AUTHORIZATION
    assert decision.blocks_later_phases is True


def test_authorized_deploy_declaration_maps_to_deploy() -> None:
    decision = decide_deploy_action(
        declared=True,
        authorization_predicate_satisfied=True,
    )

    assert decision.readiness is DeliveryReadiness.HOLD
    assert decision.delivery_action is DeliveryAction.DEPLOY
    assert decision.blocks_later_phases is False


def test_absent_release_declaration_maps_to_skip_without_blocking_close() -> None:
    decision = decide_release_action(
        declared=False,
        authorization_predicate_satisfied=False,
    )

    assert decision.readiness is DeliveryReadiness.HOLD
    assert decision.delivery_action is DeliveryAction.SKIP
    assert decision.blocks_later_phases is False


def test_unauthorized_release_declaration_maps_to_await_authorization() -> None:
    decision = decide_release_action(
        declared=True,
        authorization_predicate_satisfied=False,
    )

    assert decision.readiness is DeliveryReadiness.WITHHOLD
    assert decision.delivery_action is DeliveryAction.AWAIT_RELEASE_AUTHORIZATION
    assert decision.blocks_later_phases is True


def test_authorized_release_declaration_maps_to_release() -> None:
    decision = decide_release_action(
        declared=True,
        authorization_predicate_satisfied=True,
    )

    assert decision.readiness is DeliveryReadiness.HOLD
    assert decision.delivery_action is DeliveryAction.RELEASE
    assert decision.blocks_later_phases is False


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
