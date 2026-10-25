"""Scenario evidence: scanning a dist tree reports trap-prone hooks and stays silent on safe ones.

L1: the scanner walks a real temporary directory tree of ``hooks/hooks.json``
fixtures. No doubles — the filesystem is the real dependency and is cheap,
deterministic, and observable.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.validation.hook_safety import (
    BLOCKING_EVENTS,
    DEFAULT_ROOTS,
    iter_tree_violations,
    main,
)
from outcomeeng_testing.harnesses.hook_safety import (
    HOOK_PLUGIN_NAME,
    write_plugin_hooks,
)

# A command-shape-clean command, so a fixture's only possible violation is its event.
claude_root, codex_root = DEFAULT_ROOTS
event = min(BLOCKING_EVENTS)

SAFE_COMMAND = "echo '{}'"


def blocking_config(event: str) -> dict[str, object]:
    return {
        "hooks": {
            event: [
                {
                    "matcher": "",
                    "hooks": [
                        {"type": "command", "command": SAFE_COMMAND, "timeout": 5}
                    ],
                }
            ]
        }
    }


def safe_config() -> dict[str, object]:
    return {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "",
                    "hooks": [
                        {"type": "command", "command": SAFE_COMMAND, "timeout": 5}
                    ],
                }
            ]
        }
    }


def test_blocking_hook_is_reported_with_location(tmp_path: Path) -> None:
    write_plugin_hooks(tmp_path, claude_root, blocking_config(event))

    violations = iter_tree_violations(tmp_path)

    assert violations, (
        "a blocking-capable hook must produce a non-empty report (non-zero exit)"
    )
    report = "\n".join(violations)
    assert HOOK_PLUGIN_NAME in report  # plugin
    assert "hooks.json" in report  # file
    assert event in report  # event


def test_clean_tree_reports_nothing(tmp_path: Path) -> None:
    write_plugin_hooks(tmp_path, claude_root, safe_config())
    write_plugin_hooks(tmp_path, codex_root, safe_config())

    assert iter_tree_violations(tmp_path) == []


def guarded_substituted_config() -> dict[str, object]:
    # A non-blocking hook whose command IS a substituted-path invocation, guarded.
    command = "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session-start.py || echo '{}'"
    return {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": command, "timeout": 5}],
                }
            ]
        }
    }


def test_guarded_substituted_path_hook_reports_nothing(tmp_path: Path) -> None:
    # Scenario witness for the assertion's "uses a guarded command" clause: a guarded
    # substituted-path invocation in an otherwise clean tree produces no violations.
    write_plugin_hooks(tmp_path, claude_root, guarded_substituted_config())

    assert iter_tree_violations(tmp_path) == []


def test_main_reports_location_and_exits_non_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The first scenario assertion couples both halves: reports plugin/file/event AND
    # exits non-zero. Verify them together at the CLI entry point.
    root = tmp_path / claude_root
    write_plugin_hooks(tmp_path, claude_root, blocking_config(event))

    code = main([str(root)])
    err = capsys.readouterr().err

    assert code == 1
    assert HOOK_PLUGIN_NAME in err  # plugin
    assert "hooks.json" in err  # file
    assert event in err  # event


def test_main_exits_zero_for_a_clean_tree(tmp_path: Path) -> None:
    # The assertion frames "the dist trees" (plural): exercise both at the CLI entry.
    write_plugin_hooks(tmp_path, claude_root, safe_config())
    write_plugin_hooks(tmp_path, codex_root, safe_config())

    assert main([str(tmp_path / claude_root), str(tmp_path / codex_root)]) == 0
