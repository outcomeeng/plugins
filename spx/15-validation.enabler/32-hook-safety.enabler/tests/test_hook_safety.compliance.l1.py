"""Compliance evidence: the hook-safety validator rejects every trap-prone hook payload.

Each violating case is a whole ``hooks.json`` payload the hook-tree harness builds
from the validator's source-owned values, varying the one value its clause names,
writes into a runtime tree, and hands the test by path through the scan. Conforming
payloads sit beside the violating ones so enforcement is neither blind nor
always-failing. Every case domain comes from the harness's case builders; this file
chooses no case, value, or setup policy.
"""

from __future__ import annotations

import pytest

from outcomeeng.validation.hook_contract import (
    BLOCKING_EVENT_VIOLATION_MARKER,
    CLAUDE_RUNTIME_TREE,
    RUNTIME_TREES,
)
from outcomeeng.validation.hook_safety import iter_tree_violations
from outcomeeng_testing.harnesses.hook_safety_tree import (
    HookCase,
    allowlist_violation_cases,
    bare_script_cases,
    conforming_cases,
    guarded_script_cases,
    hook_tree,
    missing_timeout_cases,
    pinned_cache_cases,
    pre_write_violation_cases,
)

VIOLATING_CASES = (
    *allowlist_violation_cases(),
    *missing_timeout_cases(),
    *bare_script_cases(),
    *pinned_cache_cases(),
    *pre_write_violation_cases(),
)
CONFORMING_CASES = (*conforming_cases(), *guarded_script_cases())


def case_id(case: HookCase) -> str:
    return case.name


# --- NEVER: a hook on an event outside the permitted non-blocking set --------------


@pytest.mark.parametrize("case", allowlist_violation_cases(), ids=case_id)
def test_event_outside_the_allowlist_is_flagged(case: HookCase) -> None:
    with hook_tree() as tree:
        tree.write_case(CLAUDE_RUNTIME_TREE, case)

        violations = iter_tree_violations(tree.root)

    assert violations, case.name


@pytest.mark.parametrize("case", conforming_cases(), ids=case_id)
@pytest.mark.parametrize("runtime", RUNTIME_TREES)
def test_permitted_hook_passes(runtime: str, case: HookCase) -> None:
    with hook_tree() as tree:
        tree.write_case(runtime, case)

        violations = iter_tree_violations(tree.root)

    assert violations == [], case.name


# --- NEVER: a hook entry without an explicit timeout -------------------------------


@pytest.mark.parametrize("case", missing_timeout_cases(), ids=case_id)
def test_handler_without_a_timeout_is_flagged(case: HookCase) -> None:
    with hook_tree() as tree:
        tree.write_case(CLAUDE_RUNTIME_TREE, case)

        violations = iter_tree_violations(tree.root)

    assert violations, case.name


# --- NEVER: a bare substituted-path invocation with no inline fallback -------------


@pytest.mark.parametrize("case", bare_script_cases(), ids=case_id)
def test_substituted_path_invocation_without_a_fallback_is_flagged(
    case: HookCase,
) -> None:
    with hook_tree() as tree:
        tree.write_case(CLAUDE_RUNTIME_TREE, case)

        violations = iter_tree_violations(tree.root)

    assert violations, case.name


@pytest.mark.parametrize("case", guarded_script_cases(), ids=case_id)
def test_substituted_path_invocation_with_a_fallback_passes(case: HookCase) -> None:
    with hook_tree() as tree:
        tree.write_case(CLAUDE_RUNTIME_TREE, case)

        violations = iter_tree_violations(tree.root)

    assert violations == [], case.name


# --- NEVER: a command naming a version-pinned plugin cache path --------------------


@pytest.mark.parametrize("case", pinned_cache_cases(), ids=case_id)
def test_command_naming_a_version_pinned_cache_path_is_flagged(case: HookCase) -> None:
    with hook_tree() as tree:
        tree.write_case(CLAUDE_RUNTIME_TREE, case)

        violations = iter_tree_violations(tree.root)

    assert violations, case.name


# --- ALWAYS: the rules apply identically across the runtime trees ------------------


@pytest.mark.parametrize("case", VIOLATING_CASES, ids=case_id)
def test_violating_case_report_is_identical_across_runtime_trees(
    case: HookCase,
) -> None:
    with hook_tree() as tree:
        for runtime in RUNTIME_TREES:
            tree.write_case(runtime, case)

        reports = [
            iter_tree_violations(tree.runtime_root(runtime))
            for runtime in RUNTIME_TREES
        ]

    assert reports[0], case.name
    assert all(report == reports[0] for report in reports), case.name


@pytest.mark.parametrize("case", CONFORMING_CASES, ids=case_id)
def test_conforming_case_passes_in_every_runtime_tree(case: HookCase) -> None:
    with hook_tree() as tree:
        for runtime in RUNTIME_TREES:
            tree.write_case(runtime, case)

        reports = [
            iter_tree_violations(tree.runtime_root(runtime))
            for runtime in RUNTIME_TREES
        ]

    assert all(report == [] for report in reports), case.name


# --- NEVER: a PreToolUse entry differing from the pre-write exception --------------


@pytest.mark.parametrize("case", pre_write_violation_cases(), ids=case_id)
@pytest.mark.parametrize("runtime", RUNTIME_TREES)
def test_entry_differing_from_the_pre_write_exception_is_flagged(
    runtime: str, case: HookCase
) -> None:
    with hook_tree() as tree:
        tree.write_case(runtime, case)

        violations = iter_tree_violations(tree.root)

    assert any(
        BLOCKING_EVENT_VIOLATION_MARKER in violation for violation in violations
    ), case.name
