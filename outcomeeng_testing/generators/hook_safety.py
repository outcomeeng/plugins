"""Generated and source-owned domains for hook-safety evidence.

Every value traces to a source-owned domain (the hook contract's tokens, tools,
plugin, and commands; the validator's safe-event set) or to a generated space
built beside one. Command shapes compose only contract constants, so no case
repeats a value the validator owns.

Exception case: none.
"""

from __future__ import annotations

from collections.abc import Mapping

from hypothesis import strategies as st

from outcomeeng.validation.hook_contract import (
    CLAUDE_PLUGIN_ROOT_TOKEN,
    PRE_WRITE_ADAPTER_INTERPRETER,
    PRE_WRITE_COMMANDS,
    PRE_WRITE_EMPTY_RESULT,
    PRE_WRITE_MATCHER_SEPARATOR,
    PRE_WRITE_PLUGIN,
    PRE_WRITE_TOOLS,
    SUBSTITUTED_PATH_TOKENS,
)
from outcomeeng.validation.hook_safety import SAFE_EVENTS

SCRIPT_PATH = "scripts/session-start.py"
EXTENSIONLESS_SCRIPT_PATH = "scripts/session-start"
SECOND_SCRIPT_PATH = "scripts/second.py"
EMPTY_RESULT_FLOOR = f"echo '{PRE_WRITE_EMPTY_RESULT}'"
SHORT_CIRCUIT_FLOOR = "true"
PLUGIN_NAME_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789-"
PINNED_CACHE_PREFIX = "/home/user/.claude/plugins/cache/marketplace/plugin"
EXTRA_MATCHER_NAMES = ("Bash", "Read", "MultiEdit", "NotebookEdit")
SEMVER_PART_MAX = 999


def _invocation(token: str, path: str) -> str:
    return f"{PRE_WRITE_ADAPTER_INTERPRETER} {token}/{path}"


def bare_script_commands() -> Mapping[str, str]:
    """Return substituted-path invocations carrying no fallback, keyed by case name."""
    cases: dict[str, str] = {}
    for token in SUBSTITUTED_PATH_TOKENS:
        cases[f"bare {token}"] = _invocation(token, SCRIPT_PATH)
        cases[f"extensionless {token}"] = _invocation(token, EXTENSIONLESS_SCRIPT_PATH)
        cases[f"quoted {token}"] = (
            f'{PRE_WRITE_ADAPTER_INTERPRETER} "{token}"/{SCRIPT_PATH}'
        )
        cases[f"floor before {token}"] = (
            f"{EMPTY_RESULT_FLOOR} && {_invocation(token, SCRIPT_PATH)}"
        )
        cases[f"unguarded second {token}"] = (
            f"{_invocation(token, SCRIPT_PATH)} || {EMPTY_RESULT_FLOOR} ; "
            f"{_invocation(token, SECOND_SCRIPT_PATH)}"
        )
    return cases


def guarded_script_commands() -> Mapping[str, str]:
    """Return substituted-path invocations carrying a trailing fallback, keyed by case name."""
    cases: dict[str, str] = {}
    for token in SUBSTITUTED_PATH_TOKENS:
        guarded = f"{_invocation(token, SCRIPT_PATH)} || {EMPTY_RESULT_FLOOR}"
        cases[f"guarded {token}"] = guarded
        cases[f"short-circuit {token}"] = (
            f"{_invocation(token, SCRIPT_PATH)} || {SHORT_CIRCUIT_FLOOR}"
        )
        cases[f"quoted guarded {token}"] = (
            f'{PRE_WRITE_ADAPTER_INTERPRETER} "{token}"/{SCRIPT_PATH} || {EMPTY_RESULT_FLOOR}'
        )
        cases[f"leading and trailing {token}"] = f"{EMPTY_RESULT_FLOOR} && {guarded}"
    return cases


def guarded_claude_script_command() -> str:
    """Return one guarded substituted-path invocation in the Claude token form."""
    return (
        f"{_invocation(CLAUDE_PLUGIN_ROOT_TOKEN, SCRIPT_PATH)} || {EMPTY_RESULT_FLOOR}"
    )


def bare_claude_script_command() -> str:
    """Return one bare substituted-path invocation in the Claude token form."""
    return _invocation(CLAUDE_PLUGIN_ROOT_TOKEN, SCRIPT_PATH)


def pinned_cache_commands() -> st.SearchStrategy[str]:
    """Generate guarded commands that name a version-pinned plugin cache path."""
    version = st.tuples(
        st.integers(0, SEMVER_PART_MAX),
        st.integers(0, SEMVER_PART_MAX),
        st.integers(0, SEMVER_PART_MAX),
    ).map(lambda parts: ".".join(str(part) for part in parts))
    return version.map(
        lambda pinned: (
            f"{PRE_WRITE_ADAPTER_INTERPRETER} {PINNED_CACHE_PREFIX}/{pinned}/{SCRIPT_PATH}"
            f" || {EMPTY_RESULT_FLOOR}"
        )
    )


def pre_write_matcher() -> str:
    """Return the matcher naming exactly the source-owned Write and Edit tools."""
    return PRE_WRITE_MATCHER_SEPARATOR.join(sorted(PRE_WRITE_TOOLS))


def _is_pre_write_matcher(matcher: str) -> bool:
    names = matcher.split(PRE_WRITE_MATCHER_SEPARATOR)
    return len(names) == len(PRE_WRITE_TOOLS) and set(names) == PRE_WRITE_TOOLS


def matchers_other_than_pre_write() -> st.SearchStrategy[str]:
    """Generate matcher strings other than the exact Write and Edit pair."""
    tool_names = sorted(PRE_WRITE_TOOLS) + list(EXTRA_MATCHER_NAMES)
    composed = st.lists(st.sampled_from(tool_names), max_size=4).map(
        PRE_WRITE_MATCHER_SEPARATOR.join
    )
    return st.one_of(composed, st.text(max_size=24)).filter(
        lambda matcher: not _is_pre_write_matcher(matcher)
    )


def plugin_names_other_than_pre_write() -> st.SearchStrategy[str]:
    """Generate plugin directory names other than the pre-write plugin."""
    return st.text(alphabet=PLUGIN_NAME_ALPHABET, min_size=1, max_size=16).filter(
        lambda name: name != PRE_WRITE_PLUGIN
    )


def commands_other_than_pre_write() -> st.SearchStrategy[str]:
    """Generate commands other than the source-owned pre-write commands."""
    derived = st.builds(
        lambda command, suffix: f"{command}{suffix}",
        st.sampled_from(sorted(PRE_WRITE_COMMANDS)),
        st.text(min_size=1, max_size=8),
    )
    return st.one_of(derived, st.text(max_size=48)).filter(
        lambda command: command not in PRE_WRITE_COMMANDS
    )


def events_outside_safe_events() -> st.SearchStrategy[str]:
    """Generate event names outside the permitted non-blocking set."""
    return st.text(min_size=1, max_size=24).filter(
        lambda event: event not in SAFE_EVENTS
    )


__all__ = [
    "bare_claude_script_command",
    "bare_script_commands",
    "commands_other_than_pre_write",
    "events_outside_safe_events",
    "guarded_claude_script_command",
    "guarded_script_commands",
    "matchers_other_than_pre_write",
    "plugin_names_other_than_pre_write",
    "pinned_cache_commands",
    "pre_write_matcher",
]
