"""Conformance tests for the eval-evidence audit surface."""

from __future__ import annotations

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[5]
SKILL = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "audit-eval-evidence"
    / "SKILL.md"
)
REFERENCE = SKILL.parent / "references" / "evidence-model.md"
AGENT = (
    REPO_ROOT / "src" / "plugins" / "spec-tree" / "agents" / "eval-evidence-auditor.md"
)


def _frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match is not None
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def test_audit_eval_evidence_skill_is_agent_preloaded_read_only_audit() -> None:
    text = SKILL.read_text(encoding="utf-8")
    fields = _frontmatter(text)

    assert fields["name"] == "audit-eval-evidence"
    assert "preloaded by the eval-evidence-auditor agent" in text
    assert set(fields["allowed-tools"].split(", ")) == {
        "Read",
        "Grep",
        "Glob",
        "Bash",
        "Skill",
    }
    assert "<dispatch_gate>" in text
    assert "references/evidence-model.md" in text
    assert REFERENCE.exists()


def test_eval_evidence_auditor_is_thin_wrapper_for_skill() -> None:
    text = AGENT.read_text(encoding="utf-8")
    fields = _frontmatter(text)

    assert fields["name"] == "eval-evidence-auditor"
    assert fields["model"] == "sonnet"
    assert "  - spec-tree:audit-eval-evidence" in text
    assert "Follow the injected audit methodology exactly." in text
    assert "NEVER edit files" in text
