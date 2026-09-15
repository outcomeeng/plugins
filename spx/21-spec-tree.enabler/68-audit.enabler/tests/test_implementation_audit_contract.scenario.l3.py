from __future__ import annotations

from itertools import pairwise

from outcomeeng.validation.implementation_audit_contract import (
    ACCOUNTING_RECORD_KIND,
    AuditCoverageRequirement,
    AuditCoverageStatus,
    expected_verification_projection,
)
from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    observe_implementation_audit_lifecycle,
    observe_mismatched_terminal_status_finish,
)


def test_verification_run_evidence_sequences_are_monotonic() -> None:
    observation = observe_implementation_audit_lifecycle()

    sequences = observation.scope_sequences
    assert sequences
    assert all(isinstance(sequence, int) for sequence in sequences)
    assert all(current == previous + 1 for previous, current in pairwise(sequences))
    assert observation.finding_sequences == (sequences[-1] + 1,)


def test_verification_run_seals_the_authoritative_finding_count() -> None:
    observation = observe_implementation_audit_lifecycle()

    assert observation.sealed_projection == expected_verification_projection(
        observation.run_token,
        finding_count=observation.recorded_finding_count,
        terminal_status=observation.terminal_status,
    )


def test_verification_run_counts_one_rule_across_subjects() -> None:
    observation = observe_implementation_audit_lifecycle(findings_per_subject=True)

    distinct_subjects = set(observation.subject_paths)
    assert len(distinct_subjects) > 1
    assert observation.sealed_projection == expected_verification_projection(
        observation.run_token,
        finding_count=len(distinct_subjects),
        terminal_status=observation.terminal_status,
    )


def test_verification_run_rejects_approval_after_a_blocking_finding() -> None:
    exit_status = observe_mismatched_terminal_status_finish()

    assert exit_status is not None
    assert exit_status != 0


def test_verification_run_seals_an_accounting_record_for_an_unclaimed_path() -> None:
    observation = observe_implementation_audit_lifecycle()

    accounting_rows = [
        unit
        for unit in observation.rendered_scope_units
        if unit.get("subject") == observation.accounting_path
    ]
    assert len(accounting_rows) == 1
    row = accounting_rows[0]
    prior_context = row.get("priorContext")
    assert isinstance(prior_context, dict)
    assert row.get("auditKind") == ACCOUNTING_RECORD_KIND
    assert row.get("coverageRequirement") == AuditCoverageRequirement.OPTIONAL.value
    assert row.get("coverageStatus") == AuditCoverageStatus.SKIPPED.value
    assert prior_context.get("changedFilePartition") == observation.accounting_path
    assert "languagePartition" not in prior_context
    assert observation.sealed_projection[0] == observation.terminal_status.value
