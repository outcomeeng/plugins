"""Compliance evidence: the hook-safety validator rejects every trap-prone hook config.

Each rule is exercised against real violating whole-payload ``hooks.json`` fixtures
and conforming ones beside them, so enforcement is neither trivially always-failing
nor blind to a real trap. The blocking-event rule parametrizes over the source-owned
``BLOCKING_EVENTS`` set rather than a hand-picked subset, so the evidence covers the
complete domain the module owns. The detection logic lives in the source module
under test, and each rule's message text is imported from it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.validation.hook_contract import SESSION_START_EVENT
from outcomeeng.validation.hook_safety import (
    BARE_SUBSTITUTED_PATH_MESSAGE,
    BLOCKING_EVENT_MESSAGE,
    BLOCKING_EVENTS,
    CODEX_ONLY_BLOCKING_EVENTS,
    DEFAULT_ROOTS,
    MISSING_TIMEOUT_MESSAGE,
    PINNED_CACHE_MESSAGE,
    UNKNOWN_EVENT_MESSAGE,
    hook_config_violations,
    iter_tree_violations,
)
from outcomeeng_testing.harnesses.hook_safety import (
    bare_substituted_path_hooks_paths,
    guarded_substituted_path_hooks_paths,
    hook_config,
    missing_timeout_hooks_path,
    read_hooks_config,
    unknown_event_hooks_path,
    version_pinned_cache_hooks_path,
    write_plugin_hooks,
)


def _rule_messages(violations: list[str]) -> list[str]:
    # Drop the leading ``<event>: `` or ``<relative-path>: <event>: `` prefix so a
    # violation compares on its rule text alone.
    return [violation.rsplit(": ", 1)[1] for violation in violations]


@pytest.mark.parametrize("event", sorted(BLOCKING_EVENTS))
def test_blocking_event_is_flagged(event: str) -> None:
    # NEVER: pass a hook registered on a blocking-capable event. The default
    # ``echo '{}'`` command is command-shape-clean, so the only violation is the event.
    assert _rule_messages(hook_config_violations(hook_config(event))) == [
        BLOCKING_EVENT_MESSAGE
    ]


@pytest.mark.parametrize("event", sorted(CODEX_ONLY_BLOCKING_EVENTS))
def test_event_blocking_on_one_runtime_only_is_flagged(event: str) -> None:
    # An event non-blocking on Claude Code but able to block continuation on Codex is
    # outside the cross-runtime safe set, because the same hooks.json ships to both.
    assert BLOCKING_EVENT_MESSAGE in _rule_messages(
        hook_config_violations(hook_config(event))
    )


def test_unrecognized_event_is_flagged() -> None:
    # Fail closed: an event in neither the safe nor the known-blocking set is flagged.
    violations = hook_config_violations(read_hooks_config(unknown_event_hooks_path()))
    assert _rule_messages(violations) == [UNKNOWN_EVENT_MESSAGE]


def test_non_blocking_event_with_safe_command_passes() -> None:
    assert hook_config_violations(hook_config(SESSION_START_EVENT)) == []


def test_missing_timeout_is_flagged() -> None:
    # NEVER: pass a hook entry that declares no explicit timeout.
    violations = hook_config_violations(read_hooks_config(missing_timeout_hooks_path()))
    assert _rule_messages(violations) == [MISSING_TIMEOUT_MESSAGE]


@pytest.mark.parametrize(
    "fixture", bare_substituted_path_hooks_paths(), ids=lambda path: path.stem
)
def test_bare_substituted_path_invocation_is_flagged(fixture: Path) -> None:
    # NEVER: pass a bare script-file invocation at a substituted path with no inline
    # fallback — on either tree's token, with or without an extension, quoted or not,
    # behind a leading floor, or as the second invocation of a multi-statement command.
    violations = hook_config_violations(read_hooks_config(fixture))
    assert BARE_SUBSTITUTED_PATH_MESSAGE in _rule_messages(violations)


@pytest.mark.parametrize(
    "fixture", guarded_substituted_path_hooks_paths(), ids=lambda path: path.stem
)
def test_guarded_substituted_path_invocation_passes(fixture: Path) -> None:
    # The deterministic check verifies a short-circuit fallback follows the invocation.
    # Whether that fallback's floor emits a valid empty result (``|| true`` does not) is
    # the audited inline-guard property of the contract, not this check — so every
    # guarded form passes here, a leading floor beside the trailing one included.
    assert hook_config_violations(read_hooks_config(fixture)) == []


def test_bare_and_guarded_fixture_families_are_both_present() -> None:
    # A compliance claim rests on at least one real violating case beside a conforming
    # one; an emptied fixture directory would otherwise vacuously pass both families.
    assert bare_substituted_path_hooks_paths()
    assert guarded_substituted_path_hooks_paths()


def test_blocking_event_violation_reported_once_per_event() -> None:
    # Two handlers on one blocking event produce exactly one event-level violation.
    cfg = hook_config(min(BLOCKING_EVENTS), handler_count=2)
    messages = _rule_messages(hook_config_violations(cfg))
    assert messages.count(BLOCKING_EVENT_MESSAGE) == 1


def test_version_pinned_cache_path_is_flagged() -> None:
    # NEVER: pass a hook command naming a version-pinned plugin cache path.
    violations = hook_config_violations(
        read_hooks_config(version_pinned_cache_hooks_path())
    )
    assert _rule_messages(violations) == [PINNED_CACHE_MESSAGE]


def test_rules_apply_identically_across_both_runtime_trees(tmp_path: Path) -> None:
    # ALWAYS: each runtime tree, scanned in isolation, yields the same rule violation —
    # so a bug that skipped one subtree would make the two lists differ.
    blocking = hook_config(min(BLOCKING_EVENTS))
    claude_root = tmp_path / "claude"
    codex_root = tmp_path / "codex"
    claude_runtime, codex_runtime = DEFAULT_ROOTS
    write_plugin_hooks(claude_root, claude_runtime, blocking)
    write_plugin_hooks(codex_root, codex_runtime, blocking)

    claude_rules = _rule_messages(iter_tree_violations(claude_root))
    codex_rules = _rule_messages(iter_tree_violations(codex_root))

    assert claude_rules == [BLOCKING_EVENT_MESSAGE]
    assert claude_rules == codex_rules
