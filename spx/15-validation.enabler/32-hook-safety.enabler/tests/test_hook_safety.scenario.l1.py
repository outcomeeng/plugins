"""Scenario evidence: scanning a dist tree reports trap-prone hooks and stays silent on safe ones.

L1: the validator walks a real temporary directory tree whose ``hooks/hooks.json``
payloads the hook-tree harness copies in by path from the hook-safety fixtures. No
doubles — the filesystem is the real dependency and is cheap, deterministic, and
observable. The default-root scan runs ``main`` with no roots from a tree holding a
payload in each runtime tree, so the default roots themselves are exercised.
"""

from __future__ import annotations

import pytest

from outcomeeng.validation.hook_contract import (
    CLAUDE_RUNTIME_TREE,
    HOOKS_CONFIG_FILE,
    POST_TOOL_USE_EVENT,
    RUNTIME_TREES,
)
from outcomeeng.validation.hook_safety import iter_tree_violations
from outcomeeng_testing.harnesses.hook_safety_tree import (
    FixtureCase,
    FixtureGroup,
    case_id,
    fixture_cases,
    hook_tree,
)


@pytest.mark.parametrize("case", fixture_cases(FixtureGroup.SESSION_START), ids=case_id)
def test_blocking_hook_is_reported_with_plugin_file_and_event(
    case: FixtureCase,
) -> None:
    with hook_tree() as tree:
        tree.install_rekeyed(CLAUDE_RUNTIME_TREE, case, POST_TOOL_USE_EVENT)

        violations = iter_tree_violations(tree.root)

    report = "\n".join(violations)
    assert violations
    for plugin in case.plugins:
        assert plugin in report
    assert HOOKS_CONFIG_FILE in report
    assert POST_TOOL_USE_EVENT in report


@pytest.mark.parametrize("case", fixture_cases(FixtureGroup.SESSION_START), ids=case_id)
def test_blocking_hook_makes_the_scan_exit_non_zero_and_name_its_location(
    case: FixtureCase,
) -> None:
    with hook_tree() as tree:
        tree.install_rekeyed(CLAUDE_RUNTIME_TREE, case, POST_TOOL_USE_EVENT)

        scan = tree.scan_default_roots([str(tree.runtime_root(CLAUDE_RUNTIME_TREE))])

    assert scan.exit_code != 0
    for plugin in case.plugins:
        assert plugin in scan.stderr
    assert HOOKS_CONFIG_FILE in scan.stderr
    assert POST_TOOL_USE_EVENT in scan.stderr


@pytest.mark.parametrize("case", fixture_cases(FixtureGroup.SESSION_START), ids=case_id)
def test_safe_hooks_in_every_runtime_tree_report_nothing(case: FixtureCase) -> None:
    with hook_tree() as tree:
        for runtime in RUNTIME_TREES:
            tree.install(runtime, case)

        violations = iter_tree_violations(tree.root)

    assert violations == []


@pytest.mark.parametrize("case", fixture_cases(FixtureGroup.SESSION_START), ids=case_id)
def test_safe_hooks_in_every_runtime_tree_exit_zero(case: FixtureCase) -> None:
    with hook_tree() as tree:
        for runtime in RUNTIME_TREES:
            tree.install(runtime, case)

        scan = tree.scan_default_roots()

    assert scan.exit_code == 0
    assert scan.stderr == ""


@pytest.mark.parametrize("case", fixture_cases(FixtureGroup.SESSION_START), ids=case_id)
def test_default_scan_reports_a_blocking_hook_in_each_runtime_tree(
    case: FixtureCase,
) -> None:
    with hook_tree() as tree:
        for runtime in RUNTIME_TREES:
            tree.install_rekeyed(runtime, case, POST_TOOL_USE_EVENT)

        scan = tree.scan_default_roots()

    assert scan.exit_code != 0
    for runtime in RUNTIME_TREES:
        assert runtime in scan.stderr
