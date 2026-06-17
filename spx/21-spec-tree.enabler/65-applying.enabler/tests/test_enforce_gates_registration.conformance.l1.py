"""Conformance: the applying gate hook is registered plugin-level, not skill-scoped.

The gate-enforcement hook must fire on every Skill invocation while the spec-tree
plugin is enabled — not only after the applying skill happens to be invoked in a
session. So it is declared in the plugin's ``hooks/hooks.json`` as a
``PostToolUse`` hook matched on the ``Skill`` tool, and the applying skill's
frontmatter carries no ``hooks:`` block (which would scope it to that skill).
"""

from __future__ import annotations

import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
HOOKS_JSON = REPO_ROOT / "src" / "plugins" / "spec-tree" / "hooks" / "hooks.json"
APPLYING_SKILL = (
    REPO_ROOT / "src" / "plugins" / "spec-tree" / "skills" / "apply" / "SKILL.md"
)
HOOK_COMMAND_FRAGMENT = "scripts/enforce-gates.py"


def _skill_matched_post_tool_use_commands() -> list[str]:
    config = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
    entries = config.get("hooks", {}).get("PostToolUse", [])
    return [
        hook.get("command", "")
        for entry in entries
        if entry.get("matcher") == "Skill"
        for hook in entry.get("hooks", [])
    ]


def _frontmatter(text: str) -> str:
    parts = text.split("---", 2)
    return parts[1] if len(parts) >= 3 else ""


def test_enforce_gates_registered_as_plugin_level_post_tool_use_hook() -> None:
    commands = _skill_matched_post_tool_use_commands()
    assert any(HOOK_COMMAND_FRAGMENT in command for command in commands), (
        f"hooks.json must register a PostToolUse hook matched on Skill that invokes "
        f"{HOOK_COMMAND_FRAGMENT}; found commands: {commands!r}"
    )


def test_applying_frontmatter_declares_no_skill_scoped_hook() -> None:
    frontmatter = _frontmatter(APPLYING_SKILL.read_text(encoding="utf-8"))
    assert "hooks:" not in frontmatter, (
        "applying SKILL.md frontmatter must not declare a skill-scoped hooks: block — "
        "the gate hook is registered plugin-level in hooks/hooks.json"
    )
