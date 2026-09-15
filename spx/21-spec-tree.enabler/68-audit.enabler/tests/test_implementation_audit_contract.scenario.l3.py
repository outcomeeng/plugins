from __future__ import annotations

import json
from itertools import pairwise

from outcomeeng.validation.implementation_audit_contract import (
    ACCOUNTING_RECORD_KIND,
    AuditCoverageRequirement,
    AuditCoverageStatus,
    AuditTerminalStatus,
    PriorContextField,
    ScopeUnitField,
    expected_verification_projection,
)
from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    observe_implementation_audit_lifecycle,
    observe_mismatched_terminal_status_finish,
)
from outcomeeng_testing.harnesses.changeset_scope import CHANGESET_SCOPE


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
    observation = observe_mismatched_terminal_status_finish()

    assert observation.finish_exit_status is not None
    assert observation.finish_exit_status != 0
    assert observation.sealed_after_finish is False


def test_verification_run_seals_an_accounting_record_for_an_unclaimed_path() -> None:
    observation = observe_implementation_audit_lifecycle(record_findings=False)

    rows_by_subject = {
        unit.get(ScopeUnitField.SUBJECT): unit
        for unit in observation.rendered_scope_units
        if unit.get(ScopeUnitField.SUBJECT) in observation.accounting_paths
    }
    assert set(rows_by_subject) == set(observation.accounting_paths)
    for path, row in rows_by_subject.items():
        prior_context = row.get(ScopeUnitField.PRIOR_CONTEXT)
        assert isinstance(prior_context, dict)
        assert row.get(ScopeUnitField.AUDIT_KIND) == ACCOUNTING_RECORD_KIND
        assert (
            row.get(ScopeUnitField.COVERAGE_REQUIREMENT)
            == AuditCoverageRequirement.OPTIONAL.value
        )
        assert (
            row.get(ScopeUnitField.COVERAGE_STATUS) == AuditCoverageStatus.SKIPPED.value
        )
        assert prior_context.get(PriorContextField.CHANGED_FILE_PARTITION) == path
        assert PriorContextField.LANGUAGE_PARTITION not in prior_context
    # No finding was recorded, so an accounting record that forced the rollup
    # would show here as rejected; the findings alone derive the status.
    assert observation.recorded_finding_count == 0
    assert observation.sealed_projection[0] == AuditTerminalStatus.APPROVED.value


def test_verification_run_start_and_input_carry_the_fields_the_skill_reads() -> None:
    observation = observe_implementation_audit_lifecycle()

    assert isinstance(observation.start_resolved_scope, list)
    assert sorted(observation.start_resolved_scope) == sorted(observation.changed_paths)
    assert isinstance(observation.recorded_input_content, str)
    recorded_input = json.loads(observation.recorded_input_content)
    assert recorded_input[CHANGESET_SCOPE.ScopeField.CHANGED_PATHS] == list(
        observation.changed_paths
    )
