"""Deterministic merge-gate policy helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


FIELD_CONCLUSION = "conclusion"
FIELD_FINDINGS = "findings"
FIELD_IN_PR_DIFF = "in_pr_diff"
FIELD_KIND = "kind"
FIELD_OVERALL = "overall"
FIELD_PRESENT = "present"
FIELD_ROWS = "rows"
FIELD_SKIPPED_BY_DESIGN = "skipped_by_design"
FIELD_STATE = "state"
FIELD_STATUS = "status"
FIELD_VERDICT = "verdict"


class RequiredCheckKind(StrEnum):
    """Required-check source kind."""

    CHECK_RUN = "check_run"
    STATUS_CONTEXT = "status_context"


class CheckRunStatus(StrEnum):
    """Check-run status values read from a status check rollup."""

    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    QUEUED = "QUEUED"


class CheckRunConclusion(StrEnum):
    """Check-run conclusion values that affect merge readiness."""

    ACTION_REQUIRED = "ACTION_REQUIRED"
    CANCELLED = "CANCELLED"
    FAILURE = "FAILURE"
    NEUTRAL = "NEUTRAL"
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    TIMED_OUT = "TIMED_OUT"


class StatusContextState(StrEnum):
    """Status-context states read from a status check rollup."""

    ERROR = "ERROR"
    EXPECTED = "EXPECTED"
    FAILURE = "FAILURE"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"


class RequiredCheckClassification(StrEnum):
    """Merge-readiness classification for one required check."""

    ABSENT = "absent"
    NOT_TERMINAL = "not-terminal"
    TERMINAL_GREEN = "terminal-green"
    TERMINAL_NOT_SUCCESS = "terminal-not-success"


class ProductionReadiness(StrEnum):
    """Production-readiness gate result."""

    HOLD = "HOLD"
    WITHHOLD = "WITHHOLD"


class MergeAction(StrEnum):
    """Action allowed by production readiness."""

    AWAIT_APPROVAL = "AWAIT_APPROVAL"
    MERGE = "MERGE"


class DeliveryReadiness(StrEnum):
    """Delivery-phase readiness gate result."""

    HOLD = "HOLD"
    WITHHOLD = "WITHHOLD"


class DeliveryAction(StrEnum):
    """Action selected for a delivery lifecycle phase."""

    AWAIT_DEPLOYMENT_AUTHORIZATION = "AWAIT_DEPLOYMENT_AUTHORIZATION"
    AWAIT_RELEASE_AUTHORIZATION = "AWAIT_RELEASE_AUTHORIZATION"
    DEPLOY = "DEPLOY"
    RELEASE = "RELEASE"
    SKIP = "SKIP"


class AuditorRequiredAction(StrEnum):
    """Required handling for an auditor verdict surfaced during merge work."""

    FIX_BEFORE_MERGE = "FIX_BEFORE_MERGE"
    NO_REPAIR = "NO_REPAIR"
    TRACK_OUT_OF_PR = "TRACK_OUT_OF_PR"


class ReviewCheckAction(StrEnum):
    """Required handling for the current-head review-kind check."""

    INSPECT_REVIEW_SURFACES = "INSPECT_REVIEW_SURFACES"
    MENTION_REVIEW_NEEDED = "MENTION_REVIEW_NEEDED"
    MERGE_BLOCKED_REVIEW_CHECK_FAILED = "MERGE_BLOCKED:review-check-failed"
    MERGE_BLOCKED_REVIEW_CHECK_SKIPPED = "MERGE_BLOCKED:review-check-skipped"
    WAIT_FOR_REVIEW = "WAIT_FOR_REVIEW"


class AuditorOverall(StrEnum):
    """Auditor overall statuses the merge policy reads."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class AuditorRowStatus(StrEnum):
    """Auditor row statuses the merge policy reads."""

    FAIL = "FAIL"
    PASS = "PASS"
    UNKNOWN = "UNKNOWN"


class AuditorFindingVerdict(StrEnum):
    """Auditor finding verdicts the merge policy reads."""

    INFO = "INFO"
    REJECT = "REJECT"
    WARNING = "WARNING"


@dataclass(frozen=True)
class RequiredCheckDecision:
    """Decision for one required check."""

    terminal_green: bool
    classification: RequiredCheckClassification


@dataclass(frozen=True)
class ProductionDecision:
    """Decision for the production-readiness gate."""

    production_readiness: ProductionReadiness
    merge_action: MergeAction


@dataclass(frozen=True)
class AuditorVerdictDecision:
    """Decision for auditor-verdict handling."""

    required_action: AuditorRequiredAction
    merge_blocked: bool


@dataclass(frozen=True)
class DeliveryDecision:
    """Decision for one post-merge delivery phase."""

    readiness: DeliveryReadiness
    delivery_action: DeliveryAction
    blocks_later_phases: bool


@dataclass(frozen=True)
class ReviewCheckDecision:
    """Decision for the current-head review-kind check."""

    required_action: ReviewCheckAction


CHECK_RUN_NON_TERMINAL_STATUSES = frozenset(
    {CheckRunStatus.QUEUED, CheckRunStatus.IN_PROGRESS}
)
CHECK_RUN_TERMINAL_STATUS = CheckRunStatus.COMPLETED
CHECK_RUN_SUCCESS_CONCLUSIONS = frozenset({CheckRunConclusion.SUCCESS})
CHECK_RUN_TERMINAL_NOT_SUCCESS_CONCLUSIONS = frozenset(
    {
        CheckRunConclusion.ACTION_REQUIRED,
        CheckRunConclusion.CANCELLED,
        CheckRunConclusion.FAILURE,
        CheckRunConclusion.NEUTRAL,
        CheckRunConclusion.SKIPPED,
        CheckRunConclusion.TIMED_OUT,
    }
)
STATUS_CONTEXT_NON_TERMINAL_STATES = frozenset(
    {StatusContextState.EXPECTED, StatusContextState.PENDING}
)
STATUS_CONTEXT_SUCCESS_STATES = frozenset({StatusContextState.SUCCESS})
STATUS_CONTEXT_TERMINAL_NOT_SUCCESS_STATES = frozenset(
    {StatusContextState.ERROR, StatusContextState.FAILURE}
)
AUDITOR_BLOCKING_OVERALLS = frozenset({AuditorOverall.REJECTED, AuditorOverall.UNKNOWN})
AUDITOR_BLOCKING_ROW_STATUSES = frozenset(
    {AuditorRowStatus.FAIL, AuditorRowStatus.UNKNOWN}
)
AUDITOR_BLOCKING_FINDING_VERDICTS = frozenset({AuditorFindingVerdict.REJECT})


def classify_required_check(
    check: Mapping[str, object],
) -> RequiredCheckDecision:
    """Classify one required check for merge readiness."""
    if check.get(FIELD_PRESENT) is False:
        return _required_check_decision(RequiredCheckClassification.ABSENT)
    if check.get(FIELD_KIND) == RequiredCheckKind.STATUS_CONTEXT:
        return _classify_status_context(check.get(FIELD_STATE))
    return _classify_check_run(
        status=check.get(FIELD_STATUS),
        conclusion=check.get(FIELD_CONCLUSION),
    )


def decide_production_readiness(
    *,
    recognition_mechanism_declared: bool,
    production_relevant: bool | None,
    operator_approved: bool,
) -> ProductionDecision:
    """Decide whether production readiness permits merge execution."""
    if (
        not recognition_mechanism_declared
        or not production_relevant
        or operator_approved
    ):
        return ProductionDecision(
            production_readiness=ProductionReadiness.HOLD,
            merge_action=MergeAction.MERGE,
        )
    return ProductionDecision(
        production_readiness=ProductionReadiness.WITHHOLD,
        merge_action=MergeAction.AWAIT_APPROVAL,
    )


def decide_deploy_action(
    *,
    declared: bool,
    authorization_predicate_satisfied: bool,
) -> DeliveryDecision:
    """Decide whether the DEPLOY phase runs, waits, or no-ops."""
    if not declared:
        return DeliveryDecision(
            readiness=DeliveryReadiness.HOLD,
            delivery_action=DeliveryAction.SKIP,
            blocks_later_phases=False,
        )
    if authorization_predicate_satisfied:
        return DeliveryDecision(
            readiness=DeliveryReadiness.HOLD,
            delivery_action=DeliveryAction.DEPLOY,
            blocks_later_phases=False,
        )
    return DeliveryDecision(
        readiness=DeliveryReadiness.WITHHOLD,
        delivery_action=DeliveryAction.AWAIT_DEPLOYMENT_AUTHORIZATION,
        blocks_later_phases=True,
    )


def decide_release_action(
    *,
    declared: bool,
    authorization_predicate_satisfied: bool,
) -> DeliveryDecision:
    """Decide whether the RELEASE phase runs, waits, or no-ops."""
    if not declared:
        return DeliveryDecision(
            readiness=DeliveryReadiness.HOLD,
            delivery_action=DeliveryAction.SKIP,
            blocks_later_phases=False,
        )
    if authorization_predicate_satisfied:
        return DeliveryDecision(
            readiness=DeliveryReadiness.HOLD,
            delivery_action=DeliveryAction.RELEASE,
            blocks_later_phases=False,
        )
    return DeliveryDecision(
        readiness=DeliveryReadiness.WITHHOLD,
        delivery_action=DeliveryAction.AWAIT_RELEASE_AUTHORIZATION,
        blocks_later_phases=True,
    )


def decide_auditor_verdict(verdict: Mapping[str, Any]) -> AuditorVerdictDecision:
    """Decide how a merge flow handles a surfaced auditor verdict."""
    if verdict.get(FIELD_IN_PR_DIFF) is False:
        return AuditorVerdictDecision(
            required_action=AuditorRequiredAction.TRACK_OUT_OF_PR,
            merge_blocked=False,
        )
    if _auditor_verdict_blocks_merge(verdict):
        return AuditorVerdictDecision(
            required_action=AuditorRequiredAction.FIX_BEFORE_MERGE,
            merge_blocked=True,
        )
    return AuditorVerdictDecision(
        required_action=AuditorRequiredAction.NO_REPAIR,
        merge_blocked=False,
    )


def decide_review_check(check: Mapping[str, object]) -> ReviewCheckDecision:
    """Decide how merge readiness handles the current-head review-kind check."""
    required_check = classify_required_check(check)
    if required_check.classification in {
        RequiredCheckClassification.ABSENT,
        RequiredCheckClassification.NOT_TERMINAL,
    }:
        return ReviewCheckDecision(required_action=ReviewCheckAction.WAIT_FOR_REVIEW)
    if required_check.classification is RequiredCheckClassification.TERMINAL_GREEN:
        return ReviewCheckDecision(
            required_action=ReviewCheckAction.INSPECT_REVIEW_SURFACES,
        )
    if check.get(FIELD_CONCLUSION) == CheckRunConclusion.SKIPPED:
        if check.get(FIELD_SKIPPED_BY_DESIGN) is True:
            return ReviewCheckDecision(
                required_action=ReviewCheckAction.MENTION_REVIEW_NEEDED,
            )
        return ReviewCheckDecision(
            required_action=ReviewCheckAction.MERGE_BLOCKED_REVIEW_CHECK_SKIPPED,
        )
    return ReviewCheckDecision(
        required_action=ReviewCheckAction.MERGE_BLOCKED_REVIEW_CHECK_FAILED,
    )


def _classify_check_run(
    *,
    status: object,
    conclusion: object,
) -> RequiredCheckDecision:
    if status in CHECK_RUN_NON_TERMINAL_STATUSES:
        return _required_check_decision(RequiredCheckClassification.NOT_TERMINAL)
    if (
        status == CHECK_RUN_TERMINAL_STATUS
        and conclusion in CHECK_RUN_SUCCESS_CONCLUSIONS
    ):
        return _required_check_decision(RequiredCheckClassification.TERMINAL_GREEN)
    return _required_check_decision(RequiredCheckClassification.TERMINAL_NOT_SUCCESS)


def _classify_status_context(state: object) -> RequiredCheckDecision:
    if state in STATUS_CONTEXT_NON_TERMINAL_STATES:
        return _required_check_decision(RequiredCheckClassification.NOT_TERMINAL)
    if state in STATUS_CONTEXT_SUCCESS_STATES:
        return _required_check_decision(RequiredCheckClassification.TERMINAL_GREEN)
    return _required_check_decision(RequiredCheckClassification.TERMINAL_NOT_SUCCESS)


def _required_check_decision(
    classification: RequiredCheckClassification,
) -> RequiredCheckDecision:
    return RequiredCheckDecision(
        terminal_green=classification is RequiredCheckClassification.TERMINAL_GREEN,
        classification=classification,
    )


def _auditor_verdict_blocks_merge(verdict: Mapping[str, Any]) -> bool:
    if verdict.get(FIELD_OVERALL) in AUDITOR_BLOCKING_OVERALLS:
        return True
    return _contains_blocking_row(verdict.get(FIELD_ROWS, ())) or (
        _contains_blocking_finding(verdict.get(FIELD_FINDINGS, ()))
    )


def _contains_blocking_row(rows: object) -> bool:
    if not isinstance(rows, Sequence) or isinstance(rows, str):
        return False
    return any(
        isinstance(row, Mapping)
        and row.get(FIELD_STATUS) in AUDITOR_BLOCKING_ROW_STATUSES
        for row in rows
    )


def _contains_blocking_finding(findings: object) -> bool:
    if not isinstance(findings, Sequence) or isinstance(findings, str):
        return False
    return any(
        isinstance(finding, Mapping)
        and finding.get(FIELD_VERDICT) in AUDITOR_BLOCKING_FINDING_VERDICTS
        for finding in findings
    )
