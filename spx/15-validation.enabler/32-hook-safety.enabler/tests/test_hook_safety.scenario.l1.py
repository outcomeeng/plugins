"""Scenario evidence: scanning a dist tree reports trap-prone hooks and stays silent on safe ones.

L1: the scanner walks a real temporary directory tree of ``hooks/hooks.json``
fixtures. No doubles — the filesystem is the real dependency and is cheap,
deterministic, and observable.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from outcomeeng.validation.hook_contract import (
    CLAUDE_PLUGIN_ROOT_TOKEN,
    CLAUDE_RUNTIME_TREE,
    CODEX_RUNTIME_TREE,
    COMMAND_KEY,
    HOOKS_CONFIG_ENCODING,
    HOOKS_CONFIG_FILE,
    HOOKS_DIRECTORY,
    HOOKS_KEY,
    MATCHER_KEY,
    PRE_TOOL_USE_EVENT,
    PRE_WRITE_ADAPTER_INTERPRETER,
    PRE_WRITE_COMMAND_CLAUDE,
    PRE_WRITE_EMPTY_RESULT,
    PRE_WRITE_MATCHER_SEPARATOR,
    PRE_WRITE_PLUGIN,
    PRE_WRITE_TOOLS,
    SESSION_START_EVENT,
    TIMEOUT_KEY,
)
from outcomeeng.validation.hook_safety import iter_tree_violations, main

# A command-shape-clean command, so a fixture's only possible violation is its event.
SAFE_COMMAND = f"echo '{PRE_WRITE_EMPTY_RESULT}'"


def write_hooks(
    root: Path, runtime: str, plugin: str, config: dict[str, object]
) -> Path:
    path = root / runtime / plugin / HOOKS_DIRECTORY / HOOKS_CONFIG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config), encoding=HOOKS_CONFIG_ENCODING)
    return path


def blocking_config() -> dict[str, object]:
    return {
        HOOKS_KEY: {
            PRE_TOOL_USE_EVENT: [
                {
                    MATCHER_KEY: "",
                    HOOKS_KEY: [{COMMAND_KEY: SAFE_COMMAND, TIMEOUT_KEY: 5}],
                }
            ]
        }
    }


def safe_config() -> dict[str, object]:
    return {
        HOOKS_KEY: {
            SESSION_START_EVENT: [
                {
                    MATCHER_KEY: "",
                    HOOKS_KEY: [{COMMAND_KEY: SAFE_COMMAND, TIMEOUT_KEY: 5}],
                }
            ]
        }
    }


def test_blocking_hook_is_reported_with_location(tmp_path: Path) -> None:
    write_hooks(tmp_path, CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, blocking_config())

    violations = iter_tree_violations(tmp_path)

    assert violations, (
        "a blocking-capable hook must produce a non-empty report (non-zero exit)"
    )
    report = "\n".join(violations)
    assert PRE_WRITE_PLUGIN in report  # plugin
    assert HOOKS_CONFIG_FILE in report  # file
    assert PRE_TOOL_USE_EVENT in report  # event


def test_clean_tree_reports_nothing(tmp_path: Path) -> None:
    write_hooks(tmp_path, CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, safe_config())
    write_hooks(tmp_path, CODEX_RUNTIME_TREE, PRE_WRITE_PLUGIN, safe_config())

    assert iter_tree_violations(tmp_path) == []


def guarded_substituted_config() -> dict[str, object]:
    # A non-blocking hook whose command IS a substituted-path invocation, guarded.
    command = f"{PRE_WRITE_ADAPTER_INTERPRETER} {CLAUDE_PLUGIN_ROOT_TOKEN}/scripts/session-start.py || echo '{PRE_WRITE_EMPTY_RESULT}'"
    return {
        HOOKS_KEY: {
            SESSION_START_EVENT: [
                {
                    MATCHER_KEY: "",
                    HOOKS_KEY: [{COMMAND_KEY: command, TIMEOUT_KEY: 5}],
                }
            ]
        }
    }


def test_guarded_substituted_path_hook_reports_nothing(tmp_path: Path) -> None:
    # Scenario witness for the assertion's "uses a guarded command" clause: a guarded
    # substituted-path invocation in an otherwise clean tree produces no violations.
    write_hooks(
        tmp_path, CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, guarded_substituted_config()
    )

    assert iter_tree_violations(tmp_path) == []


def test_main_reports_location_and_exits_non_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The first scenario assertion couples both halves: reports plugin/file/event AND
    # exits non-zero. Verify them together at the CLI entry point.
    root = tmp_path / CLAUDE_RUNTIME_TREE
    write_hooks(tmp_path, CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, blocking_config())

    code = main([str(root)])
    err = capsys.readouterr().err

    assert code == 1
    assert (
        PRE_WRITE_PLUGIN in err
        and HOOKS_CONFIG_FILE in err
        and PRE_TOOL_USE_EVENT in err
    )


def test_main_exits_zero_for_a_clean_tree(tmp_path: Path) -> None:
    # The assertion frames "the dist trees" (plural): exercise both at the CLI entry.
    write_hooks(tmp_path, CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, safe_config())
    write_hooks(tmp_path, CODEX_RUNTIME_TREE, PRE_WRITE_PLUGIN, safe_config())

    assert (
        main([str(tmp_path / CLAUDE_RUNTIME_TREE), str(tmp_path / CODEX_RUNTIME_TREE)])
        == 0
    )


def test_spec_tree_pre_write_hook_scans_clean_and_other_plugin_is_reported(
    tmp_path: Path,
) -> None:
    matcher = PRE_WRITE_MATCHER_SEPARATOR.join(sorted(PRE_WRITE_TOOLS))
    config = {
        HOOKS_KEY: {
            PRE_TOOL_USE_EVENT: [
                {
                    MATCHER_KEY: matcher,
                    HOOKS_KEY: [
                        {
                            COMMAND_KEY: PRE_WRITE_COMMAND_CLAUDE,
                            TIMEOUT_KEY: 5,
                        }
                    ],
                }
            ]
        }
    }
    write_hooks(tmp_path, CLAUDE_RUNTIME_TREE, PRE_WRITE_PLUGIN, config)
    assert iter_tree_violations(tmp_path) == []

    write_hooks(tmp_path, CLAUDE_RUNTIME_TREE, "other-plugin", config)
    violations = iter_tree_violations(tmp_path)
    assert violations
    assert all("other-plugin" in v for v in violations)
