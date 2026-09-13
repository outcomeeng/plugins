"""Mapping evidence for deterministic merge-gate decisions."""

from __future__ import annotations

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


def test_required_check_status_and_conclusion_mapping() -> None:
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


def test_review_check_status_and_conclusion_mapping() -> None:
    """Assert current-head review-kind check mapping behavior."""

    assert (
        decide_review_check(
            {
                FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                FIELD_PRESENT: True,
                FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
                FIELD_CONCLUSION: CheckRunConclusion.SUCCESS,
            },
            current_head_review_present=False,
        ).required_action
        is ReviewCheckAction.INSPECT_REVIEW_SURFACES
    )
    assert (
        decide_review_check(
            {FIELD_KIND: RequiredCheckKind.CHECK_RUN, FIELD_PRESENT: False},
            current_head_review_present=False,
        ).required_action
        is ReviewCheckAction.WAIT_FOR_REVIEW
    )

    for status in sorted(CHECK_RUN_NON_TERMINAL_STATUSES):
        assert (
            decide_review_check(
                {
                    FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                    FIELD_PRESENT: True,
                    FIELD_STATUS: status,
                    FIELD_CONCLUSION: None,
                },
                current_head_review_present=False,
            ).required_action
            is ReviewCheckAction.WAIT_FOR_REVIEW
        )

    for conclusion in sorted(
        CHECK_RUN_TERMINAL_NOT_SUCCESS_CONCLUSIONS - {CheckRunConclusion.SKIPPED}
    ):
        assert (
            decide_review_check(
                {
                    FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                    FIELD_PRESENT: True,
                    FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
                    FIELD_CONCLUSION: conclusion,
                },
                current_head_review_present=False,
            ).required_action
            is ReviewCheckAction.MERGE_BLOCKED_REVIEW_CHECK_FAILED
        )

    assert (
        decide_review_check(
            {
                FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                FIELD_PRESENT: True,
                FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
                FIELD_CONCLUSION: CheckRunConclusion.SKIPPED,
                FIELD_STATE_CATEGORY: ReviewCheckStateCategory.SKIPPED_NON_EXCEPTION,
            },
            current_head_review_present=False,
        ).required_action
        is ReviewCheckAction.MERGE_BLOCKED_REVIEW_CHECK_SKIPPED
    )
    assert (
        decide_review_check(
            {
                FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                FIELD_PRESENT: True,
                FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
                FIELD_CONCLUSION: CheckRunConclusion.SKIPPED,
                FIELD_REVIEWER_WORKFLOW_MODIFIED: True,
            },
            current_head_review_present=False,
        ).required_action
        is ReviewCheckAction.MENTION_REVIEW_NEEDED
    )
    assert decide_review_check(
        {
            FIELD_KIND: RequiredCheckKind.CHECK_RUN,
            FIELD_PRESENT: True,
            FIELD_STATUS: CHECK_RUN_TERMINAL_STATUS,
            FIELD_CONCLUSION: CheckRunConclusion.SKIPPED,
            FIELD_REVIEWER_WORKFLOW_MODIFIED: True,
        },
        current_head_review_present=False,
    ).required_action_token == (
        f"{ReviewCheckAction.MENTION_REVIEW_NEEDED.value}"
        f"{MENTION_REVIEW_NEEDED_TOKEN_SEPARATOR}"
        f"{DEFAULT_REVIEW_TRIGGER_PHRASE}"
    )
    assert (
        decide_review_check(
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
        ).required_action
        is ReviewCheckAction.INSPECT_REVIEW_SURFACES
    )
    assert (
        decide_review_check(
            {
                FIELD_KIND: RequiredCheckKind.CHECK_RUN,
                FIELD_STATE_CATEGORY: ReviewCheckStateCategory.MISSING,
            },
            current_head_review_present=False,
        ).required_action
        is ReviewCheckAction.WAIT_FOR_REVIEW
    )


def test_delivery_phase_mapping() -> None:
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


def test_auditor_verdict_mapping() -> None:
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
