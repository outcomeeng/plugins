"""Conformance test for 13-agent-environment.enabler (agent-environment.md conformance).

L1: reads the shipped ``hooks.json`` of each generated runtime tree by path and
asserts the spec-tree plugin declares exactly two hook events. ``SessionStart``
delegates to ``spx hook run session-start`` and names no plugin-shipped script
path. ``PreToolUse`` carries a matcher naming exactly the Write and Edit tools and
a command that runs the write-boundary adapter inside the inline guard. The event
names, matcher tools and separator, and pre-write command forms come from
``outcomeeng.validation.hook_contract``; the harness owns the layout and the file
read. What spx writes is spx's own contract, verified by its suite.
"""

from __future__ import annotations

import pytest

from outcomeeng.validation.hook_contract import (
    CLAUDE_RUNTIME_TREE,
    CODEX_RUNTIME_TREE,
    MATCHER_KEY,
    PRE_TOOL_USE_EVENT,
    PRE_WRITE_COMMAND_CLAUDE,
    PRE_WRITE_COMMAND_CODEX,
    PRE_WRITE_MATCHER_SEPARATOR,
    PRE_WRITE_TOOLS,
    RUNTIME_TREES,
    SESSION_START_EVENT,
    SUBSTITUTED_PATH_TOKENS,
)
from outcomeeng_testing.harnesses.hooks import event_commands, shipped_hook_events


@pytest.mark.parametrize("runtime", RUNTIME_TREES)
def test_exactly_two_hook_events_are_declared(runtime: str) -> None:
    events = shipped_hook_events(runtime, __file__)
    assert sorted(events) == sorted([SESSION_START_EVENT, PRE_TOOL_USE_EVENT])


@pytest.mark.parametrize("runtime", RUNTIME_TREES)
def test_session_start_delegates_to_spx_and_names_no_plugin_script_path(
    runtime: str,
) -> None:
    events = shipped_hook_events(runtime, __file__)
    (command,) = event_commands(events[SESSION_START_EVENT])
    assert "hook run session-start" in command
    for token in SUBSTITUTED_PATH_TOKENS:
        assert token not in command


@pytest.mark.parametrize("runtime", RUNTIME_TREES)
def test_pre_tool_use_matcher_names_exactly_write_and_edit(runtime: str) -> None:
    events = shipped_hook_events(runtime, __file__)
    (block,) = events[PRE_TOOL_USE_EVENT]
    named = block[MATCHER_KEY].split(PRE_WRITE_MATCHER_SEPARATOR)
    assert sorted(named) == sorted(PRE_WRITE_TOOLS)


@pytest.mark.parametrize(
    ("runtime", "expected_command"),
    [
        (CLAUDE_RUNTIME_TREE, PRE_WRITE_COMMAND_CLAUDE),
        (CODEX_RUNTIME_TREE, PRE_WRITE_COMMAND_CODEX),
    ],
)
def test_pre_tool_use_runs_the_write_boundary_adapter_inside_the_inline_guard(
    runtime: str, expected_command: str
) -> None:
    events = shipped_hook_events(runtime, __file__)
    (command,) = event_commands(events[PRE_TOOL_USE_EVENT])
    assert command == expected_command
