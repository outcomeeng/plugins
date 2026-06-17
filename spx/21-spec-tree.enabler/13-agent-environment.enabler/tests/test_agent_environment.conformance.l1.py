"""Conformance test for 13-agent-environment.enabler (agent-environment.md conformance).

L1: reads the shipped ``src`` ``hooks.json`` and asserts the spec-tree plugin declares
exactly one hook event — ``SessionStart`` wired to ``scripts/session-start.py`` — and no
other hook event.
"""

from __future__ import annotations

import json

from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_root_for_spec_tree_root_test,
)

_HOOKS_JSON = ("src", "plugins", "spec-tree", "hooks", "hooks.json")


def _hooks_config() -> dict[str, object]:
    root = marketplace_root_for_spec_tree_root_test(__file__)
    return json.loads(root.joinpath(*_HOOKS_JSON).read_text(encoding="utf-8"))


def test_only_session_start_hook_is_declared() -> None:
    hooks = _hooks_config()["hooks"]
    assert list(hooks) == ["SessionStart"]


def test_session_start_runs_the_session_start_script() -> None:
    hooks = _hooks_config()["hooks"]
    commands = [
        hook["command"] for entry in hooks["SessionStart"] for hook in entry["hooks"]
    ]
    assert commands == ["python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session-start.py"]
