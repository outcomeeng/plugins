from __future__ import annotations

from pathlib import Path


def test_implementation_audit_uses_spx_verification_run() -> None:
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

    assert "--verification-type audit" in source
    assert "--scope-type changeset" in source
    assert "stable producer identity" in source
    assert "producer provenance" in source


def test_implementation_audit_dispatches_named_concern_skills() -> None:
    source = Path("src/plugins/spec-tree/skills/audit/SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "audit-{lang}-code" in source
    assert "audit-{lang}-tests" in source
    assert "audit-{lang}-architecture" in source
    assert "audit-{lang}*" not in source
    assert "Dispatch: `audit-{lang}`" not in source


def test_implementation_audit_removes_plugin_side_verdict_scripts() -> None:
    source = Path("src/plugins/spec-tree/skills/audit/SKILL.md").read_text(
        encoding="utf-8"
    )

    for retired_name in (
        "verdict.py",
        "aggregate_verdicts.py",
        "pass_results.py",
        "journal_emit.py",
        "audit_orchestrator.py",
        "spx journal",
    ):
        assert retired_name not in source

    assert not list(Path("src/plugins/spec-tree/skills/audit/scripts").glob("*.py"))


def test_implementation_auditor_is_the_only_implementation_wrapper() -> None:
    implementation_auditor = Path(
        "src/plugins/spec-tree/agents/implementation-auditor.md"
    )

    assert implementation_auditor.is_file()
    assert "name: implementation-auditor" in implementation_auditor.read_text(
        encoding="utf-8"
    )
    assert not Path("src/plugins/spec-tree/agents/auditor.md").exists()
    assert not Path("src/plugins/spec-tree/agents/audit-orchestrator.md").exists()


def test_language_code_audit_skills_use_explicit_code_names() -> None:
    for plugin_name, skill_name in (
        ("python", "audit-python-code"),
        ("typescript", "audit-typescript-code"),
        ("rust", "audit-rust-code"),
    ):
        skill_path = Path("src/plugins") / plugin_name / "skills" / skill_name
        source = (skill_path / "SKILL.md").read_text(encoding="utf-8")

        assert skill_path.is_dir()
        assert f"name: {skill_name}" in source
        assert f'"skill": "{skill_name}"' in source
        old_skill_path = (
            Path("src/plugins")
            / plugin_name
            / "skills"
            / skill_name.removesuffix("-code")
        )
        assert not old_skill_path.exists()
