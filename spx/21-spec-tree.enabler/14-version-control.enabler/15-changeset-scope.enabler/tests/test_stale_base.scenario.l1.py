"""Scenario tests for the committed-scope resolver's stale-base refusal.

Covers the Scenario assertions in ``../changeset-scope.md`` on a head behind
the fetched base, a lagging local remote-tracking ref, and a current head.

``l1``: the shipped resolver runs as a subprocess against a synthetic
repository whose origin is a real bare repository beside it.
"""

from __future__ import annotations

import json

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    CHANGESET_SCOPE_CONTRACT,
    base_advanced_after_branch_repo,
    generated_changeset_scope_cases,
    git_commit_oid,
    git_commits_between,
    git_merge_base,
    lagging_remote_tracking_repo,
    remote_base_oid,
    run_changeset_scope,
    stale_local_base_repo,
)


def test_a_head_behind_the_fetched_base_is_refused_without_a_scope() -> None:
    for scenario in generated_changeset_scope_cases():
        with base_advanced_after_branch_repo(scenario) as advanced:
            tip = remote_base_oid(advanced.repo, advanced.base_ref)
            merge_base = git_merge_base(
                advanced.repo, CHANGESET_SCOPE_CONTRACT.HEAD_REF, tip
            )

            result = run_changeset_scope(
                advanced.repo, CHANGESET_SCOPE_CONTRACT.HEAD_REF
            )

            assert result.returncode == CHANGESET_SCOPE.EXIT_STALE_BASE
            assert result.stdout == ""
            diagnostic = json.loads(result.stderr.strip().splitlines()[-1])
            assert diagnostic[CHANGESET_SCOPE.StaleBaseField.STATUS] == (
                CHANGESET_SCOPE.STALE_BASE_STATUS
            )
            assert diagnostic[CHANGESET_SCOPE.StaleBaseField.TIP] == tip
            assert diagnostic[CHANGESET_SCOPE.StaleBaseField.MERGE_BASE] == merge_base
            assert diagnostic[CHANGESET_SCOPE.StaleBaseField.BEHIND] == (
                git_commits_between(advanced.repo, merge_base, tip)
            )


def test_a_lagging_remote_tracking_ref_is_fetched_before_comparing() -> None:
    for scenario in generated_changeset_scope_cases():
        with lagging_remote_tracking_repo(scenario) as lagging:
            local_ref = CHANGESET_SCOPE.remote_tracking_ref(lagging.base_ref)
            remote_tip = remote_base_oid(lagging.repo, lagging.base_ref)
            assert git_commit_oid(lagging.repo, local_ref) != remote_tip

            result = run_changeset_scope(
                lagging.repo, CHANGESET_SCOPE_CONTRACT.HEAD_REF
            )

            assert result.returncode == CHANGESET_SCOPE.EXIT_STALE_BASE
            diagnostic = json.loads(result.stderr.strip().splitlines()[-1])
            assert diagnostic[CHANGESET_SCOPE.StaleBaseField.TIP] == remote_tip
            assert git_commit_oid(lagging.repo, local_ref) == remote_tip


def test_a_head_descending_from_the_fetched_tip_resolves_with_that_base() -> None:
    for scenario in generated_changeset_scope_cases():
        with stale_local_base_repo(scenario) as stale:
            tip = remote_base_oid(stale.repo, stale.base_ref)

            result = run_changeset_scope(stale.repo, CHANGESET_SCOPE_CONTRACT.HEAD_REF)

            assert result.returncode == 0
            resolved = json.loads(result.stdout)
            assert resolved[CHANGESET_SCOPE.ScopeField.BASE] == tip
            assert resolved[CHANGESET_SCOPE.ScopeField.HEAD] == git_commit_oid(
                stale.repo, CHANGESET_SCOPE_CONTRACT.HEAD_REF
            )


def test_a_symbolic_origin_head_base_is_fetched_as_its_branch() -> None:
    for scenario in generated_changeset_scope_cases():
        with lagging_remote_tracking_repo(scenario) as lagging:
            remote_tip = remote_base_oid(lagging.repo, lagging.base_ref)
            selector = (
                f"{CHANGESET_SCOPE.remote_tracking_ref(CHANGESET_SCOPE_CONTRACT.HEAD_REF)}"
                f"{CHANGESET_SCOPE.RANGE_SEPARATOR}{CHANGESET_SCOPE_CONTRACT.HEAD_REF}"
            )

            result = run_changeset_scope(lagging.repo, selector)

            assert result.returncode == CHANGESET_SCOPE.EXIT_STALE_BASE
            diagnostic = json.loads(result.stderr.strip().splitlines()[-1])
            assert diagnostic[CHANGESET_SCOPE.StaleBaseField.TIP] == remote_tip


def test_an_explicit_local_ref_base_is_compared_as_given() -> None:
    for scenario in generated_changeset_scope_cases():
        with stale_local_base_repo(scenario) as stale:
            local_base = git_commit_oid(stale.repo, stale.base_ref)
            assert local_base != remote_base_oid(stale.repo, stale.base_ref)
            selector = (
                f"{stale.base_ref}{CHANGESET_SCOPE.RANGE_SEPARATOR}"
                f"{CHANGESET_SCOPE_CONTRACT.HEAD_REF}"
            )

            result = run_changeset_scope(stale.repo, selector)

            assert result.returncode == 0
            resolved = json.loads(result.stdout)
            assert resolved[CHANGESET_SCOPE.ScopeField.BASE] == local_base
            assert git_commit_oid(stale.repo, stale.base_ref) == local_base
