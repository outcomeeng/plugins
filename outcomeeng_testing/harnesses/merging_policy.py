"""Harness helpers for merge-policy evidence."""

from __future__ import annotations

from collections.abc import Mapping

from outcomeeng.merging_policy import (
    AUDITOR_BLOCKING_FINDING_VERDICTS,
    AUDITOR_BLOCKING_OVERALLS,
    AUDITOR_BLOCKING_ROW_STATUSES,
    CHECK_RUN_NON_TERMINAL_STATUSES,
    CHECK_RUN_SUCCESS_CONCLUSIONS,
    CHECK_RUN_TERMINAL_NOT_SUCCESS_CONCLUSIONS,
    CHECK_RUN_TERMINAL_STATUS,
    DEFAULT_REVIEW_TRIGGER_PHRASE,
    FIELD_CONCLUSION,
    FIELD_FINDINGS,
    FIELD_IN_PR_DIFF,
    FIELD_KIND,
    FIELD_OVERALL,
    FIELD_PRESENT,
    FIELD_REVIEWER_WORKFLOW_MODIFIED,
    FIELD_ROWS,
    FIELD_STATE,
    FIELD_STATE_CATEGORY,
    FIELD_STATUS,
    FIELD_VERDICT,
    MENTION_REVIEW_NEEDED_TOKEN_SEPARATOR,
    STATUS_CONTEXT_NON_TERMINAL_STATES,
    STATUS_CONTEXT_SUCCESS_STATES,
    STATUS_CONTEXT_TERMINAL_NOT_SUCCESS_STATES,
    AuditorFindingVerdict,
    AuditorOverall,
    AuditorRequiredAction,
    AuditorRowStatus,
    CheckRunConclusion,
    DeliveryAction,
    DeliveryReadiness,
    RequiredCheckClassification,
    RequiredCheckKind,
    ReviewCheckAction,
    ReviewCheckStateCategory,
    classify_required_check,
    decide_auditor_verdict,
    decide_deploy_action,
    decide_release_action,
    decide_review_check,
)


def assert_required_check_mapping_contract() -> bool:
    """Assert required-check status/conclusion mapping behavior."""

    for conclusion in sorted(CHECK_RUN_SUCCESS_CONCLUSIONS):
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

    for status in sorted(CHECK_RUN_NON_TERMINAL_STATUSES):
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

    for conclusion in sorted(CHECK_RUN_TERMINAL_NOT_SUCCESS_CONCLUSIONS):
        decision = classify_required_check(
            {
                FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                FIELD_PRESENT: True,
                FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
                FIELD_CONCLUSION: conclusion,
            }
        )
        assert decision.terminal_green is False
        assert (
            decision.classification is RequiredCheckClassification.TERMINAL_NOT_SUCCESS
        )

    decision = classify_required_check(
        {FIELD_KIND: RequiredCheckKind.CHECK_RUN, FIELD_PRESENT: False}
    )
    assert decision.terminal_green is False
    assert decision.classification is RequiredCheckClassification.ABSENT

    for state in sorted(STATUS_CONTEXT_SUCCESS_STATES):
        decision = classify_required_check(
            {
                FIELD_KIND: RequiredCheckKind.STATUS_CONTEXT,
                FIELD_PRESENT: True,
                FIELD_STATE: state,
            }
        )
        assert decision.terminal_green is True
        assert decision.classification is RequiredCheckClassification.TERMINAL_GREEN

    for state in sorted(STATUS_CONTEXT_NON_TERMINAL_STATES):
        decision = classify_required_check(
            {
                FIELD_KIND: RequiredCheckKind.STATUS_CONTEXT,
                FIELD_PRESENT: True,
                FIELD_STATE: state,
            }
        )
        assert decision.terminal_green is False
        assert decision.classification is RequiredCheckClassification.NOT_TERMINAL

    for state in sorted(STATUS_CONTEXT_TERMINAL_NOT_SUCCESS_STATES):
        decision = classify_required_check(
            {
                FIELD_KIND: RequiredCheckKind.STATUS_CONTEXT,
                FIELD_PRESENT: True,
                FIELD_STATE: state,
            }
        )
        assert decision.terminal_green is False
        assert (
            decision.classification is RequiredCheckClassification.TERMINAL_NOT_SUCCESS
        )

    return True


def assert_review_check_mapping_contract() -> bool:
    """Assert current-head review-kind check mapping behavior."""

    assert (
        _review_check_action(
            {
                FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                FIELD_PRESENT: True,
                FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
                FIELD_CONCLUSION: CheckRunConclusion.SUCCESS,
            },
            current_head_review_present=False,
        )
        is ReviewCheckAction.INSPECT_REVIEW_SURFACES
    )
    assert (
        _review_check_action(
            {FIELD_KIND: RequiredCheckKind.CHECK_RUN, FIELD_PRESENT: False},
            current_head_review_present=False,
        )
        is ReviewCheckAction.WAIT_FOR_REVIEW
    )

    for status in sorted(CHECK_RUN_NON_TERMINAL_STATUSES):
        assert (
            _review_check_action(
                {
                    FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                    FIELD_PRESENT: True,
                    FIELD_STATUS: status,
                    FIELD_CONCLUSION: None,
                },
                current_head_review_present=False,
            )
            is ReviewCheckAction.WAIT_FOR_REVIEW
        )

    for conclusion in sorted(
        CHECK_RUN_TERMINAL_NOT_SUCCESS_CONCLUSIONS - {CheckRunConclusion.SKIPPED}
    ):
        assert (
            _review_check_action(
                {
                    FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                    FIELD_PRESENT: True,
                    FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
                    FIELD_CONCLUSION: conclusion,
                },
                current_head_review_present=False,
            )
            is ReviewCheckAction.MERGE_BLOCKED_REVIEW_CHECK_FAILED
        )

    assert (
        _review_check_action(
            {
                FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                FIELD_PRESENT: True,
                FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
                FIELD_CONCLUSION: CheckRunConclusion.SKIPPED,
                FIELD_STATE_CATEGORY: ReviewCheckStateCategory.SKIPPED_NON_EXCEPTION,
            },
            current_head_review_present=False,
        )
        is ReviewCheckAction.MERGE_BLOCKED_REVIEW_CHECK_SKIPPED
    )
    assert (
        _review_check_action(
            {
                FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                FIELD_PRESENT: True,
                FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
                FIELD_CONCLUSION: CheckRunConclusion.SKIPPED,
                FIELD_REVIEWER_WORKFLOW_MODIFIED: True,
            },
            current_head_review_present=False,
        )
        is ReviewCheckAction.MENTION_REVIEW_NEEDED
    )
    assert _review_check_action_token(
        {
            FIELD_KIND: RequiredCheckKind.CHECK_RUN,
            FIELD_PRESENT: True,
            FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
            FIELD_CONCLUSION: CheckRunConclusion.SKIPPED,
            FIELD_REVIEWER_WORKFLOW_MODIFIED: True,
        },
        current_head_review_present=False,
    ) == (
        f"{ReviewCheckAction.MENTION_REVIEW_NEEDED.value}"
        f"{MENTION_REVIEW_NEEDED_TOKEN_SEPARATOR}"
        f"{DEFAULT_REVIEW_TRIGGER_PHRASE}"
    )
    assert (
        _review_check_action(
            {
                FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                FIELD_PRESENT: True,
                FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
                FIELD_CONCLUSION: CheckRunConclusion.SKIPPED,
                FIELD_STATE_CATEGORY: (
                    ReviewCheckStateCategory.SKIPPED_SELF_MODIFYING_WORKFLOW
                ),
            },
            current_head_review_present=True,
        )
        is ReviewCheckAction.INSPECT_REVIEW_SURFACES
    )
    assert (
        _review_check_action(
            {
                FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                FIELD_STATE_CATEGORY: ReviewCheckStateCategory.MISSING,
            },
            current_head_review_present=False,
        )
        is ReviewCheckAction.WAIT_FOR_REVIEW
    )

    return True


def assert_delivery_mapping_contract() -> bool:
    """Assert deploy and release delivery mapping behavior."""

    deploy_decision = decide_deploy_action(
        declared=False,
        authorization_predicate_satisfied=False,
    )
    assert deploy_decision.readiness is DeliveryReadiness.HOLD
    assert deploy_decision.delivery_action is DeliveryAction.SKIP
    assert deploy_decision.blocks_later_phases is False

    deploy_decision = decide_deploy_action(
        declared=True,
        authorization_predicate_satisfied=False,
    )
    assert deploy_decision.readiness is DeliveryReadiness.WITHHOLD
    assert (
        deploy_decision.delivery_action is DeliveryAction.AWAIT_DEPLOYMENT_AUTHORIZATION
    )
    assert deploy_decision.blocks_later_phases is True

    deploy_decision = decide_deploy_action(
        declared=True,
        authorization_predicate_satisfied=True,
    )
    assert deploy_decision.readiness is DeliveryReadiness.HOLD
    assert deploy_decision.delivery_action is DeliveryAction.DEPLOY
    assert deploy_decision.blocks_later_phases is False

    release_decision = decide_release_action(
        declared=False,
        authorization_predicate_satisfied=False,
    )
    assert release_decision.readiness is DeliveryReadiness.HOLD
    assert release_decision.delivery_action is DeliveryAction.SKIP
    assert release_decision.blocks_later_phases is False

    release_decision = decide_release_action(
        declared=True,
        authorization_predicate_satisfied=False,
    )
    assert release_decision.readiness is DeliveryReadiness.WITHHOLD
    assert (
        release_decision.delivery_action is DeliveryAction.AWAIT_RELEASE_AUTHORIZATION
    )
    assert release_decision.blocks_later_phases is True

    release_decision = decide_release_action(
        declared=True,
        authorization_predicate_satisfied=True,
    )
    assert release_decision.readiness is DeliveryReadiness.HOLD
    assert release_decision.delivery_action is DeliveryAction.RELEASE
    assert release_decision.blocks_later_phases is False

    return True


def assert_auditor_verdict_mapping_contract() -> bool:
    """Assert auditor verdict mapping behavior."""

    for overall in sorted(AUDITOR_BLOCKING_OVERALLS):
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

    for status in sorted(AUDITOR_BLOCKING_ROW_STATUSES):
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

    for verdict in sorted(AUDITOR_BLOCKING_FINDING_VERDICTS):
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

    return True


def _review_check_action(
    check: Mapping[str, object],
    *,
    current_head_review_present: bool,
) -> ReviewCheckAction:
    return decide_review_check(
        check,
        current_head_review_present=current_head_review_present,
    ).required_action


def _review_check_action_token(
    check: Mapping[str, object],
    *,
    current_head_review_present: bool,
) -> str:
    return decide_review_check(
        check,
        current_head_review_present=current_head_review_present,
    ).required_action_token
