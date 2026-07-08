from __future__ import annotations

from pathlib import Path


def test_instruction_block_routes_audits_to_implementation_auditor() -> None:
    template = Path(
        "src/plugins/spec-tree/skills/understand/templates/instruction-block.md"
    ).read_text(encoding="utf-8")

    assert '"agent_type": "implementation-auditor"' in template
    assert "spx verification run" in template
    assert '"agent_type": "auditor"' not in template
    assert '"agent_type": "audit-orchestrator"' not in template


def test_apply_surfaces_reference_code_audit_skill_names() -> None:
    for path in (
        Path("src/plugins/spec-tree/skills/apply/SKILL.md"),
        Path("src/plugins/spec-tree/agents/applier.md"),
    ):
        source = path.read_text(encoding="utf-8")

        assert "audit-python-code" in source
        assert "audit-typescript-code" in source
        assert 'Skill("audit-python")' not in source
        assert 'Skill("audit-typescript")' not in source


def test_methodology_uses_generic_code_audit_skill_name() -> None:
    source = Path("methodology/skills/skill-structure.md").read_text(encoding="utf-8")

    assert "/audit-[language]-code" in source
    assert "/audit-[language]`" not in source
