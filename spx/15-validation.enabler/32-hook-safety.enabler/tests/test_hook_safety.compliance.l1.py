"""Compliance evidence: the hook-safety validator rejects every trap-prone hook payload.

Each violating case is a whole ``hooks.json`` fixture tree under
``outcomeeng_testing/fixtures/hook_safety/``, copied by path into a runtime tree by
the hook-tree harness; its directory name states the one clause instance it
violates. The blocking-events clause places one fixture's handler list under each
event the source-owned ``BLOCKING_EVENTS`` supplies. Conforming fixtures sit beside
the violating ones so enforcement is neither blind nor always-failing. Every
expected value is imported from the ``outcomeeng.validation`` hook modules; this file
chooses no case, value, or setup policy.
"""

from __future__ import annotations

import pytest

from outcomeeng.validation.hook_contract import (
    BLOCKING_EVENT_VIOLATION_MARKER,
    CLAUDE_RUNTIME_TREE,
    PRE_TOOL_USE_EVENT,
    RUNTIME_TREES,
)
from outcomeeng.validation.hook_safety import BLOCKING_EVENTS, iter_tree_violations
from outcomeeng_testing.harnesses.hook_safety_tree import (
    FixtureCase,
    FixtureGroup,
    case_id,
    fixture_cases,
    hook_tree,
)


# --- NEVER: a hook on an event outside the permitted non-blocking set --------------


@pytest.mark.parametrize("event", sorted(BLOCKING_EVENTS))
@pytest.mark.parametrize("case", fixture_cases(FixtureGroup.SESSION_START), ids=case_id)
def test_handlers_on_a_blocking_event_are_flagged(
    case: FixtureCase, event: str
) -> None:
    with hook_tree() as tree:
        tree.install_rekeyed(CLAUDE_RUNTIME_TREE, case, event)

        violations = iter_tree_violations(tree.root)

    assert any(
        BLOCKING_EVENT_VIOLATION_MARKER in violation for violation in violations
    ), event


@pytest.mark.parametrize(
    "case", fixture_cases(FixtureGroup.UNRECOGNIZED_EVENT), ids=case_id
)
def test_unrecognized_event_is_flagged(case: FixtureCase) -> None:
    with hook_tree() as tree:
        tree.install(CLAUDE_RUNTIME_TREE, case)

        violations = iter_tree_violations(tree.root)

    assert violations, case.name


@pytest.mark.parametrize(
    "case",
    fixture_cases(FixtureGroup.SESSION_START, FixtureGroup.PRE_WRITE_EXCEPTION),
    ids=case_id,
)
@pytest.mark.parametrize("runtime", RUNTIME_TREES)
def test_permitted_hook_passes(runtime: str, case: FixtureCase) -> None:
    with hook_tree() as tree:
        tree.install(runtime, case)

        violations = iter_tree_violations(tree.root)

    assert violations == [], case.name


@pytest.mark.parametrize("runtime", RUNTIME_TREES)
def test_shipped_hook_config_passes(runtime: str) -> None:
    with hook_tree() as tree:
        tree.install_shipped(runtime)

        violations = iter_tree_violations(tree.root)

    assert violations == [], runtime


# --- NEVER: a hook entry without an explicit timeout -------------------------------


@pytest.mark.parametrize(
    "case", fixture_cases(FixtureGroup.MISSING_TIMEOUT), ids=case_id
)
def test_handler_without_a_timeout_is_flagged(case: FixtureCase) -> None:
    with hook_tree() as tree:
        tree.install(CLAUDE_RUNTIME_TREE, case)

        violations = iter_tree_violations(tree.root)

    assert violations, case.name


# --- NEVER: a bare substituted-path invocation with no inline fallback -------------


@pytest.mark.parametrize("case", fixture_cases(FixtureGroup.BARE_SCRIPT), ids=case_id)
def test_substituted_path_invocation_without_a_fallback_is_flagged(
    case: FixtureCase,
) -> None:
    with hook_tree() as tree:
        tree.install(CLAUDE_RUNTIME_TREE, case)

        violations = iter_tree_violations(tree.root)

    assert violations, case.name


@pytest.mark.parametrize(
    "case", fixture_cases(FixtureGroup.GUARDED_SCRIPT), ids=case_id
)
def test_substituted_path_invocation_with_a_fallback_passes(case: FixtureCase) -> None:
    with hook_tree() as tree:
        tree.install(CLAUDE_RUNTIME_TREE, case)

        violations = iter_tree_violations(tree.root)

    assert violations == [], case.name


# --- NEVER: a command naming a version-pinned plugin cache path --------------------


@pytest.mark.parametrize("case", fixture_cases(FixtureGroup.PINNED_CACHE), ids=case_id)
def test_command_naming_a_version_pinned_cache_path_is_flagged(
    case: FixtureCase,
) -> None:
    with hook_tree() as tree:
        tree.install(CLAUDE_RUNTIME_TREE, case)

        violations = iter_tree_violations(tree.root)

    assert violations, case.name


# --- ALWAYS: the rules apply identically across the runtime trees ------------------


@pytest.mark.parametrize(
    "case",
    fixture_cases(
        FixtureGroup.UNRECOGNIZED_EVENT,
        FixtureGroup.MISSING_TIMEOUT,
        FixtureGroup.BARE_SCRIPT,
        FixtureGroup.PINNED_CACHE,
        FixtureGroup.PRE_WRITE_DEVIATION,
    ),
    ids=case_id,
)
def test_violating_case_report_is_identical_across_runtime_trees(
    case: FixtureCase,
) -> None:
    with hook_tree() as tree:
        for runtime in RUNTIME_TREES:
            tree.install(runtime, case)

        reports = [
            iter_tree_violations(tree.runtime_root(runtime))
            for runtime in RUNTIME_TREES
        ]

    assert reports[0], case.name
    assert all(report == reports[0] for report in reports), case.name


@pytest.mark.parametrize("event", sorted(BLOCKING_EVENTS))
@pytest.mark.parametrize("case", fixture_cases(FixtureGroup.SESSION_START), ids=case_id)
def test_blocking_event_report_is_identical_across_runtime_trees(
    case: FixtureCase, event: str
) -> None:
    with hook_tree() as tree:
        for runtime in RUNTIME_TREES:
            tree.install_rekeyed(runtime, case, event)

        reports = [
            iter_tree_violations(tree.runtime_root(runtime))
            for runtime in RUNTIME_TREES
        ]

    assert reports[0], event
    assert all(report == reports[0] for report in reports), event


@pytest.mark.parametrize(
    "case",
    fixture_cases(
        FixtureGroup.SESSION_START,
        FixtureGroup.GUARDED_SCRIPT,
        FixtureGroup.PRE_WRITE_EXCEPTION,
    ),
    ids=case_id,
)
def test_conforming_case_passes_in_every_runtime_tree(case: FixtureCase) -> None:
    with hook_tree() as tree:
        for runtime in RUNTIME_TREES:
            tree.install(runtime, case)

        reports = [
            iter_tree_violations(tree.runtime_root(runtime))
            for runtime in RUNTIME_TREES
        ]

    assert all(report == [] for report in reports), case.name


# --- NEVER: a PreToolUse entry differing from the pre-write exception --------------


@pytest.mark.parametrize(
    "case", fixture_cases(FixtureGroup.PRE_WRITE_DEVIATION), ids=case_id
)
@pytest.mark.parametrize("runtime", RUNTIME_TREES)
def test_entry_differing_from_the_pre_write_exception_is_flagged(
    runtime: str, case: FixtureCase
) -> None:
    with hook_tree() as tree:
        tree.install(runtime, case)

        violations = iter_tree_violations(tree.root)

    assert any(
        BLOCKING_EVENT_VIOLATION_MARKER in violation for violation in violations
    ), case.name


@pytest.mark.parametrize("event", sorted(BLOCKING_EVENTS - {PRE_TOOL_USE_EVENT}))
@pytest.mark.parametrize(
    "case", fixture_cases(FixtureGroup.PRE_WRITE_EXCEPTION), ids=case_id
)
def test_pre_write_exception_block_on_another_blocking_event_is_flagged(
    case: FixtureCase, event: str
) -> None:
    with hook_tree() as tree:
        tree.install_rekeyed(CLAUDE_RUNTIME_TREE, case, event)

        violations = iter_tree_violations(tree.root)

    assert any(
        BLOCKING_EVENT_VIOLATION_MARKER in violation for violation in violations
    ), event
