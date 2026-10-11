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

    assert recording.scope_add.exit_status == 0
    recorded = [
        unit
        for unit in recording.rendered_scope_units
        if unit.get(ScopeUnitField.UNIT_ID) == recording.unit_key
    ]
    assert len(recorded) == 1
    assert recorded[0].get(ScopeUnitField.AUDIT_CLASS) == ASSERTION_AUDIT_CLASS
    assert recorded[0].get(ScopeUnitField.AUDIT_KIND) == ASSERTION_AUDIT_KIND
