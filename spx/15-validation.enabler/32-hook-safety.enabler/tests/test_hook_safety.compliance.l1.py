"""Compliance evidence: the hook-safety validator rejects every trap-prone hook config.

Each rule is exercised against a violating parsed hook config and a clean one, so
enforcement is neither trivially always-failing nor blind to a real trap. The
blocking-event rule parametrizes over the source-owned ``BLOCKING_EVENTS`` set
rather than a hand-picked subset, so the evidence covers the complete domain the
module owns. The detection logic lives in the source module under test.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from outcomeeng.validation.hook_contract import (
    BLOCKING_EVENT_VIOLATION_MARKER,
    CLAUDE_PLUGIN_ROOT_TOKEN,
    CLAUDE_RUNTIME_TREE,
    CLAUDE_SKILL_DIR_TOKEN,
    CODEX_PLUGIN_ROOT_TOKEN,
    CODEX_RUNTIME_TREE,
    CODEX_SKILL_DIR_TOKEN,
    COMMAND_KEY,
    HOOKS_KEY,
    MATCHER_KEY,
    POST_TOOL_USE_EVENT,
    PRE_TOOL_USE_EVENT,
    PRE_WRITE_ADAPTER_INTERPRETER,
    PRE_WRITE_COMMAND_CLAUDE,
    PRE_WRITE_COMMAND_CODEX,
    PRE_WRITE_EMPTY_RESULT,
    PRE_WRITE_KILL_SWITCH,
    PRE_WRITE_MATCHER_SEPARATOR,
    PRE_WRITE_PLUGIN,
    PRE_WRITE_TOOLS,
    REPORT_LOCATION_SEPARATOR,
    SESSION_START_EVENT,
    TIMEOUT_KEY,
)
from outcomeeng.validation.hook_safety import (
    BLOCKING_EVENTS,
    hook_config_violations,
    iter_tree_violations,
)
from outcomeeng_testing.harnesses.hook_safety_tree import hook_tree


def config(
    event: str,
    *,
    command: str = f"echo '{PRE_WRITE_EMPTY_RESULT}'",
    timeout: int | None = 5,
) -> Mapping[str, object]:
    """Build a one-hook hooks.json config for ``event`` with an overridable command/timeout."""
    handler: dict[str, object] = {COMMAND_KEY: command}
    if timeout is not None:
        handler[TIMEOUT_KEY] = timeout
    return {HOOKS_KEY: {event: [{MATCHER_KEY: "", HOOKS_KEY: [handler]}]}}


@pytest.mark.parametrize("event", sorted(BLOCKING_EVENTS))
def test_blocking_event_is_flagged(event: str) -> None:
    # NEVER: pass a hook registered on a blocking-capable event. The default
    # ``echo '{}'`` command is command-shape-clean, so the only violation is the event.
    assert hook_config_violations(config(event)), (
        f"a {BLOCKING_EVENT_VIOLATION_MARKER} {event!r} must be flagged"
    )


def test_non_blocking_event_with_safe_command_passes() -> None:
    assert hook_config_violations(config(SESSION_START_EVENT)) == []


def test_missing_timeout_is_flagged() -> None:
    # NEVER: pass a hook entry that declares no explicit timeout.
    assert hook_config_violations(config(SESSION_START_EVENT, timeout=None))


def test_bare_script_invocation_without_fallback_is_flagged() -> None:
    # NEVER: pass a bare script-file invocation at a substituted path with no inline fallback.
    bare = f"{PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_PLUGIN_ROOT_TOKEN}/scripts/session-start.py"
    assert hook_config_violations(config(SESSION_START_EVENT, command=bare))


def test_script_invocation_with_inline_fallback_passes() -> None:
    guarded = f"{PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_PLUGIN_ROOT_TOKEN}/scripts/session-start.py 2>/dev/null || echo '{PRE_WRITE_EMPTY_RESULT}'"
    assert hook_config_violations(config(SESSION_START_EVENT, command=guarded)) == []


def test_bare_skill_dir_invocation_is_flagged() -> None:
    # The substituted-path check covers ${CLAUDE_SKILL_DIR}, not only ${CLAUDE_PLUGIN_ROOT}.
    bare = f"{PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_SKILL_DIR_TOKEN}/scripts/run.py"
    assert hook_config_violations(config(SESSION_START_EVENT, command=bare))


def test_skill_dir_invocation_with_inline_fallback_passes() -> None:
    guarded = (
        f"{PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_SKILL_DIR_TOKEN}/scripts/run.py"
        f" || echo '{PRE_WRITE_EMPTY_RESULT}'"
    )
    assert hook_config_violations(config(SESSION_START_EVENT, command=guarded)) == []


def test_codex_skill_dir_token_invocation_is_flagged() -> None:
    # The build rewrites ${CLAUDE_SKILL_DIR} to ${SKILL_DIR} in dist/codex; a bare
    # invocation via the Codex token must be caught when that tree is scanned.
    bare = f"{PRE_WRITE_ADAPTER_INTERPRETER} {CODEX_SKILL_DIR_TOKEN}/scripts/run.py"
    assert hook_config_violations(config(SESSION_START_EVENT, command=bare))


def test_codex_plugin_root_token_invocation_is_flagged() -> None:
    # Codex exposes its native ${PLUGIN_ROOT} alongside the ${CLAUDE_PLUGIN_ROOT} alias.
    bare = f"{PRE_WRITE_ADAPTER_INTERPRETER} {CODEX_PLUGIN_ROOT_TOKEN}/scripts/run.py"
    assert hook_config_violations(config(SESSION_START_EVENT, command=bare))


def test_short_circuit_fallback_satisfies_the_presence_check() -> None:
    # The deterministic check verifies a ``||`` fallback exists. Whether that fallback's
    # floor emits a valid empty result (``|| true`` does not) is the audited inline-guard
    # property of the contract, not this check — so a short-circuit fallback passes here.
    short_circuit = f"{PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_PLUGIN_ROOT_TOKEN}/scripts/session-start.py || true"
    assert (
        hook_config_violations(config(SESSION_START_EVENT, command=short_circuit)) == []
    )


def test_extensionless_substituted_script_without_fallback_is_flagged() -> None:
    # A substituted-path invocation with no file extension drifts the same way; the check
    # does not depend on a ``.py`` / ``.sh`` suffix.
    bare = f"{PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_PLUGIN_ROOT_TOKEN}/scripts/session-start"
    assert hook_config_violations(config(SESSION_START_EVENT, command=bare))


def test_unrecognized_event_is_flagged() -> None:
    # Fail closed: an event in neither the safe nor the known-blocking set is flagged.
    assert hook_config_violations(config("SomeFutureEvent"))


def test_event_blocking_on_one_runtime_only_is_flagged() -> None:
    # PostToolUse is non-blocking on Claude Code but can block continuation on Codex.
    # The same hooks.json ships to both, so it is outside the cross-runtime safe set.
    assert hook_config_violations(config(POST_TOOL_USE_EVENT))


def test_omitted_matcher_block_is_handled() -> None:
    # Codex allows a matcher-less block (as the live ~/.codex/hooks.json uses); a bare
    # hook in that form is still flagged on timeout and command shape.
    omitted: Mapping[str, object] = {
        HOOKS_KEY: {
            SESSION_START_EVENT: [
                {
                    HOOKS_KEY: [
                        {
                            COMMAND_KEY: f"{PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_PLUGIN_ROOT_TOKEN}/x.py",
                        }
                    ]
                }
            ]
        }
    }
    assert hook_config_violations(omitted)


def test_omitted_matcher_safe_form_passes() -> None:
    # The same matcher-less shape, guarded and timed, is clean.
    safe: Mapping[str, object] = {
        HOOKS_KEY: {
            SESSION_START_EVENT: [
                {
                    HOOKS_KEY: [
                        {
                            COMMAND_KEY: f"{PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_PLUGIN_ROOT_TOKEN}/x.py || echo '{PRE_WRITE_EMPTY_RESULT}'",
                            TIMEOUT_KEY: 5,
                        }
                    ]
                }
            ]
        }
    }
    assert hook_config_violations(safe) == []


def test_floor_preceding_the_script_is_flagged() -> None:
    # A floor that precedes the script (``echo '{}' && script``) does not guard the
    # invocation — the fallback must follow the script.
    leading = f"echo '{PRE_WRITE_EMPTY_RESULT}' && {PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_PLUGIN_ROOT_TOKEN}/scripts/session-start.py"
    assert hook_config_violations(config(SESSION_START_EVENT, command=leading))


def test_leading_and_trailing_fallback_passes() -> None:
    # Only the trailing fallback (after the script) guards the invocation; a redundant
    # leading floor does not change the outcome.
    both = f"echo '{PRE_WRITE_EMPTY_RESULT}' && {PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_PLUGIN_ROOT_TOKEN}/scripts/session-start.py || echo '{PRE_WRITE_EMPTY_RESULT}'"
    assert hook_config_violations(config(SESSION_START_EVENT, command=both)) == []


def test_second_substituted_invocation_without_fallback_is_flagged() -> None:
    # Each substituted-path invocation needs its own guard — a guarded first script does
    # not cover a bare second one in a multi-statement command.
    cmd = f"{PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_PLUGIN_ROOT_TOKEN}/a.py || echo '{PRE_WRITE_EMPTY_RESULT}' ; {PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_PLUGIN_ROOT_TOKEN}/b.py"
    assert hook_config_violations(config(SESSION_START_EVENT, command=cmd))


def test_quoted_substituted_path_invocation_is_flagged() -> None:
    # A shell-safe quoted variable ("${CLAUDE_PLUGIN_ROOT}"/...) is the same substituted
    # path; the quote between the brace and the slash must not defeat detection.
    bare = f'{PRE_WRITE_ADAPTER_INTERPRETER} "{CLAUDE_PLUGIN_ROOT_TOKEN}"/scripts/session-start.py'
    assert hook_config_violations(config(SESSION_START_EVENT, command=bare))


def test_quoted_substituted_path_with_fallback_passes() -> None:
    guarded = f'{PRE_WRITE_ADAPTER_INTERPRETER} "{CLAUDE_PLUGIN_ROOT_TOKEN}"/scripts/session-start.py || echo "{PRE_WRITE_EMPTY_RESULT}"'
    assert hook_config_violations(config(SESSION_START_EVENT, command=guarded)) == []


def test_blocking_event_violation_reported_once_per_event() -> None:
    # Two handlers on one blocking event produce exactly one event-level violation.
    cfg: Mapping[str, object] = {
        HOOKS_KEY: {
            PRE_TOOL_USE_EVENT: [
                {
                    MATCHER_KEY: "",
                    HOOKS_KEY: [
                        {
                            COMMAND_KEY: f"echo '{PRE_WRITE_EMPTY_RESULT}'",
                            TIMEOUT_KEY: 5,
                        },
                        {
                            COMMAND_KEY: f"echo '{PRE_WRITE_EMPTY_RESULT}'",
                            TIMEOUT_KEY: 5,
                        },
                    ],
                }
            ]
        }
    }
    blocking = [
        v for v in hook_config_violations(cfg) if BLOCKING_EVENT_VIOLATION_MARKER in v
    ]
    assert len(blocking) == 1


def test_version_pinned_cache_path_is_flagged() -> None:
    # NEVER: pass a hook command naming a version-pinned plugin cache path.
    pinned = f"{PRE_WRITE_ADAPTER_INTERPRETER} /Users/dev/.claude/plugins/cache/outcomeeng/spec-tree/0.57.33/scripts/x.py || echo '{PRE_WRITE_EMPTY_RESULT}'"
    assert hook_config_violations(config(SESSION_START_EVENT, command=pinned))


def _rule_messages(violations: list[str]) -> list[str]:
    # Drop the leading ``<relative-path>: `` so two trees compare on rule text alone.
    return [
        violation.split(REPORT_LOCATION_SEPARATOR, 1)[1] for violation in violations
    ]


def test_rules_apply_identically_across_both_runtime_trees() -> None:
    # ALWAYS: each runtime tree, scanned in isolation, yields the same rule violation —
    # so a bug that skipped one subtree would make the two lists differ.
    blocking = config(PRE_TOOL_USE_EVENT)
    with hook_tree() as tree:
        claude_tree = tree.subtree(CLAUDE_RUNTIME_TREE)
        codex_tree = tree.subtree(CODEX_RUNTIME_TREE)
        claude_tree.write_hooks(CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, blocking)
        codex_tree.write_hooks(CODEX_RUNTIME_TREE, PRE_WRITE_PLUGIN, blocking)

        claude_rules = _rule_messages(iter_tree_violations(claude_tree.root))
        codex_rules = _rule_messages(iter_tree_violations(codex_tree.root))

    assert claude_rules, "the blocking event must be flagged in each runtime tree"
    assert claude_rules == codex_rules


PRE_WRITE_MATCHER = PRE_WRITE_MATCHER_SEPARATOR.join(sorted(PRE_WRITE_TOOLS))


def pre_write_config(
    *,
    matcher: str = PRE_WRITE_MATCHER,
    command: str = PRE_WRITE_COMMAND_CLAUDE,
    extra_entries: int = 0,
    extra_handlers: int = 0,
) -> Mapping[str, object]:
    handler: dict[str, object] = {
        COMMAND_KEY: command,
        TIMEOUT_KEY: 5,
    }
    entries = [
        {MATCHER_KEY: matcher, HOOKS_KEY: [handler] * (1 + extra_handlers)}
        for _ in range(1 + extra_entries)
    ]
    return {HOOKS_KEY: {PRE_TOOL_USE_EVENT: entries}}


@pytest.mark.parametrize(
    ("runtime", "command"),
    [
        (CLAUDE_RUNTIME_TREE, PRE_WRITE_COMMAND_CLAUDE),
        (CODEX_RUNTIME_TREE, PRE_WRITE_COMMAND_CODEX),
    ],
)
def test_pre_write_exception_passes_in_its_runtime_tree(
    runtime: str, command: str
) -> None:
    with hook_tree() as tree:
        tree.write_hooks(runtime, PRE_WRITE_PLUGIN, pre_write_config(command=command))

        assert iter_tree_violations(tree.root) == []


def test_pre_write_exception_is_flagged_for_another_plugin() -> None:
    assert hook_config_violations(pre_write_config(), "other-plugin")
    assert hook_config_violations(pre_write_config())


EDIT_TOOL, WRITE_TOOL = sorted(PRE_WRITE_TOOLS)
SEPARATOR = PRE_WRITE_MATCHER_SEPARATOR


@pytest.mark.parametrize(
    "matcher",
    [
        "",
        WRITE_TOOL,
        EDIT_TOOL,
        f"{WRITE_TOOL}{SEPARATOR}{EDIT_TOOL}{SEPARATOR}Bash",
        f"{WRITE_TOOL}{SEPARATOR}Read",
        f"{EDIT_TOOL}{SEPARATOR}{WRITE_TOOL}{SEPARATOR}{WRITE_TOOL}",
        "Bash",
        ".*",
    ],
)
def test_pre_write_exception_is_flagged_for_a_different_matcher(matcher: str) -> None:
    assert hook_config_violations(pre_write_config(matcher=matcher), PRE_WRITE_PLUGIN)


@pytest.mark.parametrize("event", sorted(BLOCKING_EVENTS - {PRE_TOOL_USE_EVENT}))
def test_pre_write_exception_is_flagged_on_another_blocking_event(event: str) -> None:
    # NEVER: pass a hook on a blocking-capable event other than PreToolUse, even when
    # the block is the exact pre-write exception registered by its plugin.
    handler: dict[str, object] = {
        COMMAND_KEY: PRE_WRITE_COMMAND_CLAUDE,
        TIMEOUT_KEY: 5,
    }
    on_event: Mapping[str, object] = {
        HOOKS_KEY: {event: [{MATCHER_KEY: PRE_WRITE_MATCHER, HOOKS_KEY: [handler]}]}
    }
    assert hook_config_violations(on_event, PRE_WRITE_PLUGIN)


def test_pre_write_exception_without_a_matcher_key_is_flagged() -> None:
    handler: dict[str, object] = {
        COMMAND_KEY: PRE_WRITE_COMMAND_CLAUDE,
        TIMEOUT_KEY: 5,
    }
    matcherless: Mapping[str, object] = {
        HOOKS_KEY: {PRE_TOOL_USE_EVENT: [{HOOKS_KEY: [handler]}]}
    }
    assert hook_config_violations(matcherless, PRE_WRITE_PLUGIN)


def test_pre_write_exception_is_flagged_for_a_different_command() -> None:
    other = (
        f"{PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_PLUGIN_ROOT_TOKEN}/scripts/other.py"
        f" || echo '{PRE_WRITE_EMPTY_RESULT}'"
    )
    assert hook_config_violations(pre_write_config(command=other), PRE_WRITE_PLUGIN)


def test_second_pre_tool_use_entry_beside_the_exception_is_flagged() -> None:
    assert hook_config_violations(pre_write_config(extra_entries=1), PRE_WRITE_PLUGIN)


def test_second_handler_inside_the_exception_block_is_flagged() -> None:
    assert hook_config_violations(pre_write_config(extra_handlers=1), PRE_WRITE_PLUGIN)


@pytest.mark.parametrize(
    "command",
    [
        PRE_WRITE_COMMAND_CLAUDE.replace(
            PRE_WRITE_KILL_SWITCH, f"{PRE_WRITE_KILL_SWITCH}_OTHER"
        ),
        PRE_WRITE_COMMAND_CLAUDE.replace(PRE_WRITE_EMPTY_RESULT, ""),
    ],
)
def test_pre_write_exception_is_flagged_for_a_command_with_a_changed_guard(
    command: str,
) -> None:
    # The changed command still reaches the adapter through ${CLAUDE_PLUGIN_ROOT} with
    # an inline fallback, so only equality with the source-owned command flags it.
    assert hook_config_violations(pre_write_config(command=command), PRE_WRITE_PLUGIN)
