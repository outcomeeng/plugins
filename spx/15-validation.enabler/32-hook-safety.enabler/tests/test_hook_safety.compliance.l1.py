"""Compliance evidence: the hook-safety validator rejects every trap-prone hook payload.

Finite violating cases are whole ``hooks.json`` payloads the hook-tree harness
writes and hands back by path; the validator scans the tree that holds them. Open
violating spaces (events, version-pinned commands, plugins, matchers, and commands
other than the pre-write exception) draw from the spec-governed generators, and
each generated payload is a whole payload built by the harness. Conforming
payloads sit beside the violating ones so enforcement is neither blind nor
always-failing. Every case domain comes from the validator's source owners, the
generators, or the governing spec sentence; this file chooses none.
"""

from __future__ import annotations

import pytest
from hypothesis import given

from outcomeeng.validation.hook_contract import (
    BLOCKING_EVENT_VIOLATION_MARKER,
    CLAUDE_RUNTIME_TREE,
    PRE_TOOL_USE_EVENT,
    PRE_WRITE_COMMAND_CLAUDE,
    PRE_WRITE_PLUGIN,
    RUNTIME_TREES,
    SESSION_START_EVENT,
)
from outcomeeng.validation.hook_safety import (
    BLOCKING_EVENTS,
    SAFE_EVENTS,
    hook_config_violations,
    iter_tree_violations,
)
from outcomeeng_testing.generators.hook_safety import (
    bare_script_commands,
    commands_other_than_pre_write,
    events_outside_safe_events,
    guarded_script_commands,
    matchers_other_than_pre_write,
    pinned_cache_commands,
    plugin_names_other_than_pre_write,
    pre_write_matcher,
)
from outcomeeng_testing.harnesses.hook_safety_tree import (
    DEFAULT_MATCHER,
    hook_config,
    hook_tree,
)


def pre_write_exception_payload(
    *, matcher: str | None = None, command: str | None = None
) -> dict[str, object]:
    """Whole in-memory payload shaped as the pre-write exception, with overridable parts."""
    return dict(
        hook_config(
            PRE_TOOL_USE_EVENT,
            command=PRE_WRITE_COMMAND_CLAUDE if command is None else command,
            matcher=pre_write_matcher() if matcher is None else matcher,
        )
    )


# --- events outside the permitted non-blocking set -------------------------------


@pytest.mark.parametrize("event", sorted(BLOCKING_EVENTS))
def test_blocking_event_is_flagged(event: str) -> None:
    with hook_tree() as tree:
        tree.write_event_hook(CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, event)

        violations = iter_tree_violations(tree.root)

    assert any(
        BLOCKING_EVENT_VIOLATION_MARKER in violation and event in violation
        for violation in violations
    )


@pytest.mark.parametrize("event", sorted(SAFE_EVENTS))
def test_safe_event_with_a_safe_handler_passes(event: str) -> None:
    with hook_tree() as tree:
        tree.write_event_hook(CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, event)

        violations = iter_tree_violations(tree.root)

    assert violations == []


@given(event=events_outside_safe_events())
def test_every_event_outside_the_safe_set_is_flagged(event: str) -> None:
    assert hook_config_violations(hook_config(event))


# --- explicit timeout --------------------------------------------------------------


@pytest.mark.parametrize("matcher", [DEFAULT_MATCHER, None])
@pytest.mark.parametrize("event", sorted(SAFE_EVENTS))
def test_handler_without_a_timeout_is_flagged(event: str, matcher: str | None) -> None:
    with hook_tree() as tree:
        tree.write_event_hook(
            CLAUDE_RUNTIME_TREE,
            PRE_WRITE_PLUGIN,
            event,
            timeout=None,
            matcher=matcher,
        )

        violations = iter_tree_violations(tree.root)

    assert violations


# --- substituted-path invocations --------------------------------------------------


@pytest.mark.parametrize(("case", "command"), sorted(bare_script_commands().items()))
def test_substituted_path_invocation_without_a_fallback_is_flagged(
    case: str, command: str
) -> None:
    with hook_tree() as tree:
        tree.write_session_start_hook(
            CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, command=command
        )

        violations = iter_tree_violations(tree.root)

    assert violations, case


@pytest.mark.parametrize(("case", "command"), sorted(guarded_script_commands().items()))
def test_substituted_path_invocation_with_a_fallback_passes(
    case: str, command: str
) -> None:
    with hook_tree() as tree:
        tree.write_session_start_hook(
            CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, command=command
        )

        violations = iter_tree_violations(tree.root)

    assert violations == [], case


# --- version-pinned cache paths ----------------------------------------------------


@given(command=pinned_cache_commands())
def test_command_naming_a_version_pinned_cache_path_is_flagged(command: str) -> None:
    assert hook_config_violations(hook_config(SESSION_START_EVENT, command=command))


# --- identical rules across the runtime trees --------------------------------------


@pytest.mark.parametrize("event", sorted(BLOCKING_EVENTS))
def test_blocking_event_report_is_identical_across_runtime_trees(event: str) -> None:
    with hook_tree() as tree:
        for runtime in RUNTIME_TREES:
            tree.write_event_hook(runtime, PRE_WRITE_PLUGIN, event)

        reports = [
            iter_tree_violations(tree.runtime_root(runtime))
            for runtime in RUNTIME_TREES
        ]

    assert reports[0]
    assert all(report == reports[0] for report in reports)


@pytest.mark.parametrize(("case", "command"), sorted(bare_script_commands().items()))
def test_command_report_is_identical_across_runtime_trees(
    case: str, command: str
) -> None:
    with hook_tree() as tree:
        for runtime in RUNTIME_TREES:
            tree.write_session_start_hook(runtime, PRE_WRITE_PLUGIN, command=command)

        reports = [
            iter_tree_violations(tree.runtime_root(runtime))
            for runtime in RUNTIME_TREES
        ]

    assert reports[0], case
    assert all(report == reports[0] for report in reports)


@pytest.mark.parametrize("runtime", RUNTIME_TREES)
def test_pre_write_exception_passes_in_its_runtime_tree(runtime: str) -> None:
    with hook_tree() as tree:
        tree.write_pre_write_hook(runtime, PRE_WRITE_PLUGIN)

        violations = iter_tree_violations(tree.root)

    assert violations == []


# --- the pre-write exception admits nothing beyond itself --------------------------


@pytest.mark.parametrize("event", sorted(BLOCKING_EVENTS - {PRE_TOOL_USE_EVENT}))
def test_pre_write_exception_is_flagged_on_another_blocking_event(event: str) -> None:
    with hook_tree() as tree:
        tree.write_pre_write_hook(CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, event=event)

        violations = iter_tree_violations(tree.root)

    assert any(BLOCKING_EVENT_VIOLATION_MARKER in violation for violation in violations)


def test_pre_write_exception_without_a_matcher_key_is_flagged() -> None:
    with hook_tree() as tree:
        tree.write_matcherless_pre_write_hook(CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN)

        violations = iter_tree_violations(tree.root)

    assert any(BLOCKING_EVENT_VIOLATION_MARKER in violation for violation in violations)


def test_second_pre_tool_use_entry_beside_the_exception_is_flagged() -> None:
    # The governing sentence names "a second PreToolUse entry beside it".
    with hook_tree() as tree:
        tree.write_pre_write_hook(CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, entries=2)

        violations = iter_tree_violations(tree.root)

    assert any(BLOCKING_EVENT_VIOLATION_MARKER in violation for violation in violations)


def test_second_handler_inside_the_exception_block_is_flagged() -> None:
    # A second handler makes the block differ from the single-handler exception.
    with hook_tree() as tree:
        tree.write_pre_write_hook(CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, handlers=2)

        violations = iter_tree_violations(tree.root)

    assert any(BLOCKING_EVENT_VIOLATION_MARKER in violation for violation in violations)


def test_pre_write_exception_without_a_plugin_is_flagged() -> None:
    assert hook_config_violations(pre_write_exception_payload())


@given(plugin=plugin_names_other_than_pre_write())
def test_pre_write_exception_is_flagged_for_any_other_plugin(plugin: str) -> None:
    assert hook_config_violations(pre_write_exception_payload(), plugin)


@given(matcher=matchers_other_than_pre_write())
def test_pre_write_exception_is_flagged_for_any_other_matcher(matcher: str) -> None:
    assert hook_config_violations(
        pre_write_exception_payload(matcher=matcher), PRE_WRITE_PLUGIN
    )


@given(command=commands_other_than_pre_write())
def test_pre_write_exception_is_flagged_for_any_other_command(command: str) -> None:
    assert hook_config_violations(
        pre_write_exception_payload(command=command), PRE_WRITE_PLUGIN
    )
