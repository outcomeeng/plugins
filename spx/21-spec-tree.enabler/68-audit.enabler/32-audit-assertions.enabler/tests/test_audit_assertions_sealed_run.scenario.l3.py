from __future__ import annotations

from outcomeeng.validation.implementation_audit_contract import (
    RUN_SEALED_FIELD,
    RUN_TERMINAL_STATUS_FIELD,
    AuditTerminalStatus,
    ScopeUnitField,
)
from outcomeeng_testing.harnesses.assertion_audit_run import (
    observe_sealed_run_with_finding,
)


def test_pinned_cli_seals_a_run_recording_the_skill_unit_and_finding() -> None:
    observation = observe_sealed_run_with_finding()

    assert observation.scope_add.exit_status == 0
    assert observation.finding_add.exit_status == 0
    assert observation.finish.exit_status == 0
    finish_report = observation.finish.report
    assert finish_report is not None
    assert finish_report.get(RUN_SEALED_FIELD) is True
    assert (
        finish_report.get(RUN_TERMINAL_STATUS_FIELD)
        == AuditTerminalStatus.REJECTED.value
    )
    unit_keys = [
        unit.get(ScopeUnitField.UNIT_ID) for unit in observation.rendered_scope_units
    ]
    assert unit_keys == [observation.unit_key]
