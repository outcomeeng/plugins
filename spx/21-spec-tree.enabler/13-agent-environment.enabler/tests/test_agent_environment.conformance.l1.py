"""Conformance test for 13-agent-environment.enabler (agent-environment.md conformance).

L1: reads the shipped ``src`` ``hooks.json`` and asserts the spec-tree plugin
declares exactly one hook event — ``SessionStart`` — whose command delegates to
``spx hook run session-start`` and names no plugin-shipped script path. This pins
the plugin's integration with the spx hook runner; what spx writes is spx's own
contract, verified by its suite. The Hook Safety Contract's deterministic shape
(timeout, kill switch, valid-empty floor) is verified by ``spx/15-hook-safety.pdr.md``
and its validator, not restated here.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.hooks import (
    SESSION_START_EVENT,
    session_start_command,
    session_start_events,
)

# The integration contract: the command invokes the spx hook runner subcommand on
# a binary that defaults to ``spx`` (resolved through an override-then-PATH guard).
_SPX_RUNNER_SUBCOMMAND = "hook run session-start"
_SPX_DEFAULT_BINARY = "${SPX_BIN:-spx}"
# A plugin-shipped script would be invoked through a substituted plugin path token.
_PLUGIN_SCRIPT_PATH_TOKENS = ("${CLAUDE_PLUGIN_ROOT}", "${CLAUDE_SKILL_DIR}")


def test_only_session_start_hook_is_declared() -> None:
    assert session_start_events() == [SESSION_START_EVENT]


def test_session_start_delegates_to_spx() -> None:
    command = session_start_command()
    assert _SPX_RUNNER_SUBCOMMAND in command
    assert _SPX_DEFAULT_BINARY in command


def test_session_start_names_no_plugin_script_path() -> None:
    command = session_start_command()
    for token in _PLUGIN_SCRIPT_PATH_TOKENS:
        assert token not in command
