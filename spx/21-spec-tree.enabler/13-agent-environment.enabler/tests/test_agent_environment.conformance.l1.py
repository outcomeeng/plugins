"""Conformance test for 13-agent-environment.enabler (agent-environment.md conformance).

L1: reads the shipped ``hooks.json`` of each generated runtime tree by path and
asserts the spec-tree plugin declares exactly two hook events. ``SessionStart``
delegates to ``spx hook run session-start`` and names no plugin-shipped script
path. ``PreToolUse`` carries a matcher naming exactly the Write and Edit tools and
a command that runs the write-boundary adapter inside the inline guard. The event
names, matcher tools and separator, layout names, and pre-write command forms come
from ``outcomeeng.validation.hook_contract``; what spx writes is spx's own
contract, verified by its suite.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from outcomeeng.validation.hook_contract import (
    CLAUDE_RUNTIME_TREE,
    CODEX_RUNTIME_TREE,
    COMMAND_KEY,
    HOOKS_CONFIG_ENCODING,
    HOOKS_CONFIG_FILE,
    HOOKS_DIRECTORY,
    HOOKS_KEY,
    MATCHER_KEY,
    PRE_TOOL_USE_EVENT,
    PRE_WRITE_COMMAND_CLAUDE,
    PRE_WRITE_COMMAND_CODEX,
    PRE_WRITE_MATCHER_SEPARATOR,
    PRE_WRITE_PLUGIN,
    PRE_WRITE_TOOLS,
    RUNTIME_TREES,
    SESSION_START_EVENT,
    SUBSTITUTED_PATH_TOKENS,
)
from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_root_for_spec_tree_root_test,
)

_PRE_WRITE_COMMAND_BY_TREE = {
    CLAUDE_RUNTIME_TREE: PRE_WRITE_COMMAND_CLAUDE,
    CODEX_RUNTIME_TREE: PRE_WRITE_COMMAND_CODEX,
}


def _shipped_events(runtime: str) -> dict[str, Any]:
    """Return the event map of the spec-tree plugin's shipped hooks.json."""
    path = (
        marketplace_root_for_spec_tree_root_test(__file__)
        / runtime
        / PRE_WRITE_PLUGIN
        / HOOKS_DIRECTORY
        / HOOKS_CONFIG_FILE
    )
    config: dict[str, Any] = json.loads(path.read_text(encoding=HOOKS_CONFIG_ENCODING))
    events: dict[str, Any] = config[HOOKS_KEY]
    return events


def _commands(blocks: list[dict[str, Any]]) -> list[str]:
    return [handler[COMMAND_KEY] for block in blocks for handler in block[HOOKS_KEY]]


@pytest.mark.parametrize("runtime", RUNTIME_TREES)
def test_exactly_two_hook_events_are_declared(runtime: str) -> None:
    events = _shipped_events(runtime)
    assert sorted(events) == sorted([SESSION_START_EVENT, PRE_TOOL_USE_EVENT])


@pytest.mark.parametrize("runtime", RUNTIME_TREES)
def test_session_start_delegates_to_spx_and_names_no_plugin_script_path(
    runtime: str,
) -> None:
    (command,) = _commands(_shipped_events(runtime)[SESSION_START_EVENT])
    assert "hook run session-start" in command
    for token in SUBSTITUTED_PATH_TOKENS:
        assert token not in command


@pytest.mark.parametrize("runtime", RUNTIME_TREES)
def test_pre_tool_use_matcher_names_exactly_write_and_edit(runtime: str) -> None:
    (block,) = _shipped_events(runtime)[PRE_TOOL_USE_EVENT]
    named = block[MATCHER_KEY].split(PRE_WRITE_MATCHER_SEPARATOR)
    assert sorted(named) == sorted(PRE_WRITE_TOOLS)


@pytest.mark.parametrize("runtime", RUNTIME_TREES)
def test_pre_tool_use_runs_the_write_boundary_adapter_inside_the_inline_guard(
    runtime: str,
) -> None:
    (command,) = _commands(_shipped_events(runtime)[PRE_TOOL_USE_EVENT])
    assert command == _PRE_WRITE_COMMAND_BY_TREE[runtime]
