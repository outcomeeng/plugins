from __future__ import annotations

from outcomeeng.validation.assertion_audit_contract import (
    ASSERTION_AUDIT_CLASS,
    ASSERTION_AUDIT_KIND,
)
from outcomeeng.validation.implementation_audit_contract import ScopeUnitField
from outcomeeng_testing.harnesses.assertion_audit_run import (
    observe_scope_unit_recording,
)


def test_pinned_floor_accepts_the_skill_class_and_kind_for_a_node_spec() -> None:
    recording = observe_scope_unit_recording()

    unit_keys = [recording.root_unit_key, *recording.child_unit_keys]
    assert recording.root_scope_add.exit_status == 0
    assert [add.exit_status for add in recording.child_scope_adds] == [
        0 for _ in recording.child_unit_keys
    ]
    units = {
        unit.get(ScopeUnitField.UNIT_ID): unit
        for unit in recording.rendered_scope_units
    }
    assert [
        (
            units[unit_key].get(ScopeUnitField.AUDIT_CLASS),
            units[unit_key].get(ScopeUnitField.AUDIT_KIND),
        )
        for unit_key in unit_keys
    ] == [(ASSERTION_AUDIT_CLASS, ASSERTION_AUDIT_KIND) for _ in unit_keys]
