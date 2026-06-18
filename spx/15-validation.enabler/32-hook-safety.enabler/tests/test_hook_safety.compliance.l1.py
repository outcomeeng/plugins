"""Compliance evidence: the hook-safety validator rejects every trap-prone hook config.

Each rule is exercised against a violating parsed hook config and a clean one, so
enforcement is neither trivially always-failing nor blind to a real trap. The
blocking-event rule parametrizes over the source-owned ``BLOCKING_EVENTS`` set
rather than a hand-picked subset, so the evidence covers the complete domain the
module owns. The detection logic lives in the source module under test.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import pytest

from outcomeeng.validation.hook_safety import (
    BLOCKING_EVENTS,
    hook_config_violations,
    iter_tree_violations,
)


def config(
    event: str, *, command: str = "echo '{}'", timeout: int | None = 5
) -> Mapping[str, object]:
    """Build a one-hook hooks.json config for ``event`` with an overridable command/timeout."""
    handler: dict[str, object] = {"type": "command", "command": command}
    if timeout is not None:
        handler["timeout"] = timeout
    return {"hooks": {event: [{"matcher": "", "hooks": [handler]}]}}


@pytest.mark.parametrize("event", sorted(BLOCKING_EVENTS))
def test_blocking_event_is_flagged(event: str) -> None:
    # NEVER: pass a hook registered on a blocking-capable event. The default
    # ``echo '{}'`` command is command-shape-clean, so the only violation is the event.
    assert hook_config_violations(config(event)), (
        f"a hook on blocking-capable event {event!r} must be flagged"
    )


def test_non_blocking_event_with_safe_command_passes() -> None:
    assert hook_config_violations(config("SessionStart")) == []


def test_missing_timeout_is_flagged() -> None:
    # NEVER: pass a hook entry that declares no explicit timeout.
    assert hook_config_violations(config("SessionStart", timeout=None))


def test_bare_script_invocation_without_fallback_is_flagged() -> None:
    # NEVER: pass a bare script-file invocation at a substituted path with no inline fallback.
    bare = "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session-start.py"
    assert hook_config_violations(config("SessionStart", command=bare))


def test_script_invocation_with_inline_fallback_passes() -> None:
    guarded = "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session-start.py 2>/dev/null || echo '{}'"
    assert hook_config_violations(config("SessionStart", command=guarded)) == []


def test_bare_skill_dir_invocation_is_flagged() -> None:
    # The substituted-path check covers ${CLAUDE_SKILL_DIR}, not only ${CLAUDE_PLUGIN_ROOT}.
    bare = "python3 ${CLAUDE_SKILL_DIR}/scripts/run.py"
    assert hook_config_violations(config("SessionStart", command=bare))


def test_skill_dir_invocation_with_inline_fallback_passes() -> None:
    guarded = "python3 ${CLAUDE_SKILL_DIR}/scripts/run.py || echo '{}'"
    assert hook_config_violations(config("SessionStart", command=guarded)) == []


def test_codex_skill_dir_token_invocation_is_flagged() -> None:
    # The build rewrites ${CLAUDE_SKILL_DIR} to ${SKILL_DIR} in dist/codex; a bare
    # invocation via the Codex token must be caught when that tree is scanned.
    bare = "python3 ${SKILL_DIR}/scripts/run.py"
    assert hook_config_violations(config("SessionStart", command=bare))


def test_codex_plugin_root_token_invocation_is_flagged() -> None:
    # Codex exposes its native ${PLUGIN_ROOT} alongside the ${CLAUDE_PLUGIN_ROOT} alias.
    bare = "python3 ${PLUGIN_ROOT}/scripts/run.py"
    assert hook_config_violations(config("SessionStart", command=bare))


def test_short_circuit_fallback_satisfies_the_presence_check() -> None:
    # The deterministic check verifies a ``||`` fallback exists. Whether that fallback's
    # floor emits a valid empty result (``|| true`` does not) is the audited inline-guard
    # property of the contract, not this check — so a short-circuit fallback passes here.
    short_circuit = "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session-start.py || true"
    assert hook_config_violations(config("SessionStart", command=short_circuit)) == []


def test_extensionless_substituted_script_without_fallback_is_flagged() -> None:
    # A substituted-path invocation with no file extension drifts the same way; the check
    # does not depend on a ``.py`` / ``.sh`` suffix.
    bare = "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session-start"
    assert hook_config_violations(config("SessionStart", command=bare))


def test_unrecognized_event_is_flagged() -> None:
    # Fail closed: an event in neither the safe nor the known-blocking set is flagged.
    assert hook_config_violations(config("SomeFutureEvent"))


def test_event_blocking_on_one_runtime_only_is_flagged() -> None:
    # PostToolUse is non-blocking on Claude Code but can block continuation on Codex.
    # The same hooks.json ships to both, so it is outside the cross-runtime safe set.
    assert hook_config_violations(config("PostToolUse"))


def test_omitted_matcher_block_is_handled() -> None:
    # Codex allows a matcher-less block (as the live ~/.codex/hooks.json uses); a bare
    # hook in that form is still flagged on timeout and command shape.
    omitted: Mapping[str, object] = {
        "hooks": {
            "SessionStart": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/x.py",
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
        "hooks": {
            "SessionStart": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/x.py || echo '{}'",
                            "timeout": 5,
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
    leading = "echo '{}' && python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session-start.py"
    assert hook_config_violations(config("SessionStart", command=leading))


def test_leading_and_trailing_fallback_passes() -> None:
    # Only the trailing fallback (after the script) guards the invocation; a redundant
    # leading floor does not change the outcome.
    both = "echo '{}' && python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session-start.py || echo '{}'"
    assert hook_config_violations(config("SessionStart", command=both)) == []


def test_second_substituted_invocation_without_fallback_is_flagged() -> None:
    # Each substituted-path invocation needs its own guard — a guarded first script does
    # not cover a bare second one in a multi-statement command.
    cmd = "python3 ${CLAUDE_PLUGIN_ROOT}/a.py || echo '{}' ; python3 ${CLAUDE_PLUGIN_ROOT}/b.py"
    assert hook_config_violations(config("SessionStart", command=cmd))


def test_quoted_substituted_path_invocation_is_flagged() -> None:
    # A shell-safe quoted variable ("${CLAUDE_PLUGIN_ROOT}"/...) is the same substituted
    # path; the quote between the brace and the slash must not defeat detection.
    bare = 'python3 "${CLAUDE_PLUGIN_ROOT}"/scripts/session-start.py'
    assert hook_config_violations(config("SessionStart", command=bare))


def test_quoted_substituted_path_with_fallback_passes() -> None:
    guarded = 'python3 "${CLAUDE_PLUGIN_ROOT}"/scripts/session-start.py || echo "{}"'
    assert hook_config_violations(config("SessionStart", command=guarded)) == []


def test_blocking_event_violation_reported_once_per_event() -> None:
    # Two handlers on one blocking event produce exactly one event-level violation.
    cfg: Mapping[str, object] = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "",
                    "hooks": [
                        {"type": "command", "command": "echo '{}'", "timeout": 5},
                        {"type": "command", "command": "echo '{}'", "timeout": 5},
                    ],
                }
            ]
        }
    }
    blocking = [v for v in hook_config_violations(cfg) if "blocking-capable event" in v]
    assert len(blocking) == 1


def test_version_pinned_cache_path_is_flagged() -> None:
    # NEVER: pass a hook command naming a version-pinned plugin cache path.
    pinned = "python3 /Users/dev/.claude/plugins/cache/outcomeeng/spec-tree/0.57.33/scripts/x.py || echo '{}'"
    assert hook_config_violations(config("SessionStart", command=pinned))


def _write_config(root: Path, runtime: str, cfg: Mapping[str, object]) -> None:
    path = root / runtime / "spec-tree" / "hooks" / "hooks.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg), encoding="utf-8")


def _rule_messages(violations: list[str]) -> list[str]:
    # Drop the leading ``<relative-path>: `` so two trees compare on rule text alone.
    return [violation.split(": ", 1)[1] for violation in violations]


def test_rules_apply_identically_across_both_runtime_trees(tmp_path: Path) -> None:
    # ALWAYS: each runtime tree, scanned in isolation, yields the same rule violation —
    # so a bug that skipped one subtree would make the two lists differ.
    blocking = config("PreToolUse")
    claude_root = tmp_path / "claude"
    codex_root = tmp_path / "codex"
    _write_config(claude_root, "dist/claude", blocking)
    _write_config(codex_root, "dist/codex", blocking)

    claude_rules = _rule_messages(iter_tree_violations(claude_root))
    codex_rules = _rule_messages(iter_tree_violations(codex_root))

    assert claude_rules, "the blocking event must be flagged in each runtime tree"
    assert claude_rules == codex_rules
