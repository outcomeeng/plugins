"""Conformance test for 13-agent-environment.enabler (agent-environment.md conformance).

L1: reads the shipped ``src`` ``hooks.json`` and asserts the product-tree plugin
declares exactly one hook event — ``SessionStart`` — with two entries. The first,
on every source, delegates to ``spx hook run session-start`` and names no
plugin-shipped script path. The second, matched on ``compact``, names the shell's
own read of the reminder resource the foundation-resource manifest names, found
under the plugin root, and names no script. This pins the plugin's integration
with the spx hook runner; what spx writes is spx's own contract, verified by its
suite. The Hook Safety Contract's deterministic shape (timeout, kill switch,
valid-empty floor) is verified by ``spx/15-hook-safety.pdr.md`` and its
validator, not restated here.
"""

from __future__ import annotations

from outcomeeng.validation.hook_contract import (
    PLUGIN_ROOT_TOKEN,
    SESSION_START_COMPACT_MATCHER,
    SESSION_START_EVERY_SOURCE_MATCHER,
)
from outcomeeng_testing.harnesses.hooks import (
    SESSION_START_EVENT,
    compact_entry_command,
    compact_recovery_resource,
    delegating_entry_command,
    session_start_entries,
    session_start_events,
    shipped_plugin_root,
)

# The integration contract: the command invokes the spx hook runner subcommand on
# a binary that defaults to ``spx`` (resolved through an override-then-PATH guard).
_SPX_RUNNER_SUBCOMMAND = "hook run session-start"
_SPX_DEFAULT_BINARY = "${SPX_BIN:-spx}"


def test_only_session_start_hook_is_declared() -> None:
    assert session_start_events() == [SESSION_START_EVENT]


def test_session_start_declares_the_delegating_entry_then_the_compact_entry() -> None:
    matchers = [entry.matcher for entry in session_start_entries()]
    assert matchers == [
        SESSION_START_EVERY_SOURCE_MATCHER,
        SESSION_START_COMPACT_MATCHER,
    ]


def test_delegating_entry_delegates_to_spx() -> None:
    command = delegating_entry_command()
    assert _SPX_RUNNER_SUBCOMMAND in command
    assert _SPX_DEFAULT_BINARY in command


def test_delegating_entry_names_no_plugin_script_path() -> None:
    assert PLUGIN_ROOT_TOKEN not in delegating_entry_command()


def test_compact_entry_names_the_reminder_resource_under_the_plugin_root() -> None:
    plugin_root = shipped_plugin_root()
    resource = compact_recovery_resource(plugin_root).relative_to(plugin_root)
    assert f"{PLUGIN_ROOT_TOKEN}/{resource.as_posix()}" in compact_entry_command()


def test_compact_entry_names_no_plugin_path_beyond_the_reminder_resource() -> None:
    plugin_root = shipped_plugin_root()
    resource = compact_recovery_resource(plugin_root).relative_to(plugin_root)
    remainder = compact_entry_command().replace(
        f"{PLUGIN_ROOT_TOKEN}/{resource.as_posix()}", ""
    )
    assert PLUGIN_ROOT_TOKEN not in remainder
