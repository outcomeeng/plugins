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


def test_audit_eval_evidence_skill_frontmatter_grants_context_loading() -> None:
    text = SKILL.read_text(encoding="utf-8")
    fields = _frontmatter(text)

    assert fields["name"] == "audit-eval-evidence"
    assert set(fields["allowed-tools"].split(", ")) == {
        "Read",
        "Grep",
        "Glob",
        "Bash",
        "Skill",
    }
    assert REFERENCE.exists()


def test_eval_evidence_auditor_frontmatter_preloads_skill() -> None:
    text = AGENT.read_text(encoding="utf-8")
    fields = _frontmatter(text)

    assert fields["name"] == "eval-evidence-auditor"
    assert fields["model"] == "sonnet"
    assert set(fields["tools"].split(", ")) == {
        "Bash",
        "Read",
        "Skill",
    }
    assert "skills:\n  - spec-tree:audit-eval-evidence" in text
