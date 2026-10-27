from __future__ import annotations

from outcomeeng.validation.assertion_audit_contract import PARENT_UNIT_FIELD
from outcomeeng.validation.implementation_audit_contract import (
    RUN_SEALED_FIELD,
    RUN_TERMINAL_STATUS_FIELD,
    AuditTerminalStatus,
    ScopeUnitField,
)
from outcomeeng_testing.harnesses.assertion_audit_run import (
    observe_sealed_run_with_finding,
)


def test_pinned_cli_seals_a_run_recording_the_unit_tree_and_finding() -> None:
    observation = observe_sealed_run_with_finding()

    assert len(observation.child_unit_keys) > 1
    assert observation.root_scope_add.exit_status == 0
    assert [add.exit_status for add in observation.child_scope_adds] == [
        0 for _ in observation.child_unit_keys
    ]
    assert observation.finding_add.exit_status == 0
    assert observation.finish.exit_status == 0
    finish_report = observation.finish.report
    assert finish_report is not None
    assert finish_report.get(RUN_SEALED_FIELD) is True
    assert (
        finish_report.get(RUN_TERMINAL_STATUS_FIELD)
        == AuditTerminalStatus.REJECTED.value
    )
    units = {
        unit.get(ScopeUnitField.UNIT_ID): unit
        for unit in observation.rendered_scope_units
    }
    assert sorted(str(unit_key) for unit_key in units) == sorted(
        [observation.root_unit_key, *observation.child_unit_keys]
    )
    assert not units[observation.root_unit_key].get(PARENT_UNIT_FIELD)
    assert [
        units[unit_key].get(PARENT_UNIT_FIELD)
        for unit_key in observation.child_unit_keys
    ] == [observation.root_unit_key for _ in observation.child_unit_keys]
