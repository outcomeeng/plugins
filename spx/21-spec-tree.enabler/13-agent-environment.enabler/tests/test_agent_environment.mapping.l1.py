"""Mapping test for 13-agent-environment.enabler (agent-environment.md mapping).

L1: reads the shipped ``src`` ``hooks.json`` wiring file and asserts each converted
hook event maps to its ``spx hooks <event>`` command and that the converted hooks'
scripts are absent. This is the marketplace's hook contribution; the hook behavior
itself is owned by ``spx hooks <event>`` and verified in ``@outcomeeng/spx``.
"""

from __future__ import annotations

import json

from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_root_for_spec_tree_root_test,
)

CONVERTED_EVENT_COMMANDS = {
    "SessionStart": "spx hooks session-start",
    "PreToolUse": "spx hooks pre-tool-use",
}
REMOVED_HOOK_SCRIPTS = ("session-start.py", "load-gate.py")

_HOOKS_JSON = ("src", "plugins", "spec-tree", "hooks", "hooks.json")
_SCRIPTS_DIR = ("src", "plugins", "spec-tree", "scripts")


def _hooks_config() -> dict[str, object]:
    root = marketplace_root_for_spec_tree_root_test(__file__)
    payload = root.joinpath(*_HOOKS_JSON).read_text(encoding="utf-8")
    return json.loads(payload)


def test_converted_events_wire_to_spx_hooks() -> None:
    hooks = _hooks_config()["hooks"]
    for event, command in CONVERTED_EVENT_COMMANDS.items():
        commands = [
            hook["command"] for entry in hooks[event] for hook in entry["hooks"]
        ]
        assert commands == [command]


def test_converted_hook_scripts_are_absent() -> None:
    root = marketplace_root_for_spec_tree_root_test(__file__)
    scripts = root.joinpath(*_SCRIPTS_DIR)
    present = {path.name for path in scripts.iterdir()} if scripts.is_dir() else set()
    assert not present & set(REMOVED_HOOK_SCRIPTS)
