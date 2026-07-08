from __future__ import annotations

from pathlib import Path

from outcomeeng.validation.spx_version import REQUIRED_SPX_VERSION, is_satisfied


def test_spx_floor_provides_verification_run_lifecycle() -> None:
    assert is_satisfied(REQUIRED_SPX_VERSION, "0.6.13")

    workflow = Path(".github/workflows/check.yml").read_text(encoding="utf-8")
    assert 'SPX_VERSION: "0.6.13"' in workflow


def test_audit_skill_uses_spx_verification_run_payload_contract() -> None:
    source = Path("src/plugins/spec-tree/skills/audit/SKILL.md").read_text(
        encoding="utf-8"
    )

    for command in (
        "spx verification run start",
        "spx verification run scope add",
        "spx verification run finding add",
        "spx verification run finish",
        "spx verification run render",
    ):
        assert command in source

    assert 'python3 "${CLAUDE_SKILL_DIR}/scripts/' not in source


def test_audit_skill_ships_no_verdict_toolchain_scripts() -> None:
    for retired_name in (
        "verdict.py",
        "aggregate_verdicts.py",
        "pass_results.py",
        "journal_emit.py",
        "audit_orchestrator.py",
    ):
        assert not Path(
            "src/plugins/spec-tree/skills/audit/scripts", retired_name
        ).exists()
