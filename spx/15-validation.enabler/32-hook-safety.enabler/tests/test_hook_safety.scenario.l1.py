"""Scenario evidence: scanning a dist tree reports trap-prone hooks and stays silent on safe ones.

L1: the scanner walks a real temporary directory tree of ``hooks/hooks.json``
fixtures. No doubles — the filesystem is the real dependency and is cheap,
deterministic, and observable.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from outcomeeng.validation.hook_safety import iter_tree_violations, main

# A command-shape-clean command, so a fixture's only possible violation is its event.
SAFE_COMMAND = "echo '{}'"


def write_hooks(
    root: Path, runtime: str, plugin: str, config: dict[str, object]
) -> Path:
    path = root / runtime / plugin / "hooks" / "hooks.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def blocking_config() -> dict[str, object]:
    return {
        "hooks": {
            "PreToolUse": [
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
    write_hooks(tmp_path, "dist/claude", "spec-tree", blocking_config())

    violations = iter_tree_violations(tmp_path)

    assert violations, (
        "a blocking-capable hook must produce a non-empty report (non-zero exit)"
    )
    report = "\n".join(violations)
    assert "spec-tree" in report  # plugin
    assert "hooks.json" in report  # file
    assert "PreToolUse" in report  # event


def test_clean_tree_reports_nothing(tmp_path: Path) -> None:
    write_hooks(tmp_path, "dist/claude", "spec-tree", safe_config())
    write_hooks(tmp_path, "dist/codex", "spec-tree", safe_config())

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
    write_hooks(tmp_path, "dist/claude", "spec-tree", guarded_substituted_config())

    assert iter_tree_violations(tmp_path) == []


def test_main_reports_location_and_exits_non_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The first scenario assertion couples both halves: reports plugin/file/event AND
    # exits non-zero. Verify them together at the CLI entry point.
    root = tmp_path / "dist/claude"
    write_hooks(tmp_path, "dist/claude", "spec-tree", blocking_config())

    code = main([str(root)])
    err = capsys.readouterr().err

    assert code == 1
    assert "spec-tree" in err and "hooks.json" in err and "PreToolUse" in err


def test_main_exits_zero_for_a_clean_tree(tmp_path: Path) -> None:
    # The assertion frames "the dist trees" (plural): exercise both at the CLI entry.
    write_hooks(tmp_path, "dist/claude", "spec-tree", safe_config())
    write_hooks(tmp_path, "dist/codex", "spec-tree", safe_config())

    assert main([str(tmp_path / "dist/claude"), str(tmp_path / "dist/codex")]) == 0
