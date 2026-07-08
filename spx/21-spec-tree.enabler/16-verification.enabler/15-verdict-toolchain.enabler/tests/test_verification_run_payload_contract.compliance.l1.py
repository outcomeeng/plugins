from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    audit_skill_ships_no_verdict_toolchain_scripts,
    spx_floor_provides_verification_run_lifecycle,
)


def test_spx_floor_provides_verification_run_lifecycle() -> None:
    assert spx_floor_provides_verification_run_lifecycle()


def test_audit_skill_ships_no_verdict_toolchain_scripts() -> None:
    assert audit_skill_ships_no_verdict_toolchain_scripts()
