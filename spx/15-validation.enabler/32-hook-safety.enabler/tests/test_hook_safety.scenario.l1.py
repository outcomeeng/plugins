"""Scenario evidence: scanning a dist tree reports trap-prone hooks and stays silent on safe ones.

L1: the validator walks a real temporary directory tree whose ``hooks/hooks.json``
payloads the hook-tree harness writes and hands back by path. No doubles — the
filesystem is the real dependency and is cheap, deterministic, and observable.
The default-root scan runs ``main`` with no roots from a tree holding a payload in
each runtime tree, so the default roots themselves are exercised.
"""

from __future__ import annotations

from outcomeeng.validation.hook_contract import (
    CLAUDE_RUNTIME_TREE,
    HOOKS_CONFIG_FILE,
    POST_TOOL_USE_EVENT,
    RUNTIME_TREES,
)
from outcomeeng.validation.hook_safety import iter_tree_violations
from outcomeeng_testing.harnesses.hook_safety_tree import (
    FOREIGN_PLUGIN,
    guarded_script_command,
    hook_tree,
)


def test_blocking_hook_is_reported_with_plugin_file_and_event() -> None:
    with hook_tree() as tree:
        tree.write_event_hook(CLAUDE_RUNTIME_TREE, FOREIGN_PLUGIN, POST_TOOL_USE_EVENT)

        violations = iter_tree_violations(tree.root)

    report = "\n".join(violations)
    assert violations
    assert FOREIGN_PLUGIN in report
    assert HOOKS_CONFIG_FILE in report
    assert POST_TOOL_USE_EVENT in report


def test_blocking_hook_makes_the_scan_exit_non_zero_and_name_its_location() -> None:
    with hook_tree() as tree:
        tree.write_event_hook(CLAUDE_RUNTIME_TREE, FOREIGN_PLUGIN, POST_TOOL_USE_EVENT)

        scan = tree.scan_default_roots([str(tree.runtime_root(CLAUDE_RUNTIME_TREE))])

    assert scan.exit_code != 0
    assert FOREIGN_PLUGIN in scan.stderr
    assert HOOKS_CONFIG_FILE in scan.stderr
    assert POST_TOOL_USE_EVENT in scan.stderr


def test_safe_hooks_in_every_runtime_tree_report_nothing() -> None:
    with hook_tree() as tree:
        for runtime in RUNTIME_TREES:
            tree.write_session_start_hook(
                runtime, FOREIGN_PLUGIN, command=guarded_script_command()
            )

        violations = iter_tree_violations(tree.root)

    assert violations == []


def test_safe_hooks_in_every_runtime_tree_exit_zero() -> None:
    with hook_tree() as tree:
        for runtime in RUNTIME_TREES:
            tree.write_session_start_hook(
                runtime, FOREIGN_PLUGIN, command=guarded_script_command()
            )

        scan = tree.scan_default_roots()

    assert scan.exit_code == 0
    assert scan.stderr == ""


def test_default_scan_reports_a_blocking_hook_in_each_runtime_tree() -> None:
    with hook_tree() as tree:
        for runtime in RUNTIME_TREES:
            tree.write_event_hook(runtime, FOREIGN_PLUGIN, POST_TOOL_USE_EVENT)

        scan = tree.scan_default_roots()

    assert scan.exit_code != 0
    for runtime in RUNTIME_TREES:
        assert runtime in scan.stderr
