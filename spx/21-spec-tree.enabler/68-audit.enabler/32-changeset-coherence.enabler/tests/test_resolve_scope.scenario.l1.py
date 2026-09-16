"""Scenario evidence for the coherence audit's committed-scope resolver."""

from __future__ import annotations

import json

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    COHERENCE_SCOPE,
    checkout_branch,
    git_commit_oid,
    remote_base_oid,
    repo_without_origin,
    run_coherence_scope,
    stale_local_base_repo,
    temporary_changeset_scope,
)


def test_branch_scope_excludes_commits_already_merged_to_the_base() -> None:
    """A stale local base ref never widens the resolved scope.

    The fixture's feature branch carries a commit already present on
    ``origin/<base>``. Composing against the lagging local ref would re-admit
    that merged file; composing against the remote-tracking ref keeps the merge
    base at the true branch point, so only the feature's own change resolves.
    """
    with stale_local_base_repo() as stale:
        completed = run_coherence_scope(stale.repo, CHANGESET_SCOPE.HEAD_REF)

        assert not completed.returncode
        resolved = json.loads(completed.stdout)
        assert frozenset(
            resolved[CHANGESET_SCOPE.ScopeField.CHANGED_PATHS]
        ) == frozenset((stale.feature_file,))
        assert (
            stale.merged_file not in resolved[CHANGESET_SCOPE.ScopeField.CHANGED_PATHS]
        )


def test_resolved_identities_are_full_commit_object_ids() -> None:
    with stale_local_base_repo() as stale:
        resolved = json.loads(
            run_coherence_scope(stale.repo, CHANGESET_SCOPE.HEAD_REF).stdout
        )

        assert resolved[CHANGESET_SCOPE.ScopeField.BASE] == remote_base_oid(
            stale.repo, stale.base_ref
        )
        assert resolved[CHANGESET_SCOPE.ScopeField.HEAD] == git_commit_oid(
            stale.repo, stale.feature_branch
        )
        assert (
            resolved[CHANGESET_SCOPE.ScopeField.BASE]
            != resolved[CHANGESET_SCOPE.ScopeField.HEAD]
        )


def test_explicit_commit_range_resolves_both_endpoints() -> None:
    with stale_local_base_repo() as stale:
        branch_form = json.loads(
            run_coherence_scope(stale.repo, CHANGESET_SCOPE.HEAD_REF).stdout
        )
        range_form = json.loads(
            run_coherence_scope(
                stale.repo,
                f"{CHANGESET_SCOPE.remote_tracking_ref(stale.base_ref)}"
                f"{CHANGESET_SCOPE.RANGE_SEPARATOR}{CHANGESET_SCOPE.HEAD_REF}",
            ).stdout
        )

        assert range_form == branch_form


def test_branch_not_checked_out_resolves_its_own_paths() -> None:
    """A named branch resolves its own scope, not the checked-out branch's.

    The canonical branch-scope range fixes its far end at ``HEAD``, so an audit
    invoked on a branch other than the checked-out one would pair that branch's
    head identity with the checked-out branch's paths and classify the wrong
    changeset.
    """
    with stale_local_base_repo() as stale:
        checkout_branch(stale.repo, stale.base_ref)

        resolved = json.loads(
            run_coherence_scope(stale.repo, stale.feature_branch).stdout
        )

        assert frozenset(
            resolved[CHANGESET_SCOPE.ScopeField.CHANGED_PATHS]
        ) == frozenset((stale.feature_file,))
        assert resolved[CHANGESET_SCOPE.ScopeField.HEAD] == git_commit_oid(
            stale.repo, stale.feature_branch
        )


def test_unconfigured_remote_base_is_reported_without_traceback() -> None:
    with repo_without_origin() as repo:
        completed = run_coherence_scope(repo, CHANGESET_SCOPE.HEAD_REF)

        assert completed.returncode
        assert completed.stderr.startswith(COHERENCE_SCOPE.ERROR_PREFIX)
        assert "Traceback (most recent call last):" not in completed.stderr


def test_malformed_commit_range_is_rejected_without_traceback() -> None:
    with stale_local_base_repo() as stale:
        completed = run_coherence_scope(
            stale.repo,
            f"{CHANGESET_SCOPE.remote_tracking_ref(stale.base_ref)}"
            f"{CHANGESET_SCOPE.RANGE_SEPARATOR}",
        )

        assert completed.returncode
        assert completed.stderr.startswith(COHERENCE_SCOPE.ERROR_PREFIX)
        assert "Traceback (most recent call last):" not in completed.stderr


def test_nonexistent_repository_path_is_reported_without_traceback() -> None:
    with temporary_changeset_scope() as paths:
        completed = run_coherence_scope(
            paths.repo,
            CHANGESET_SCOPE.HEAD_REF,
            repo_override=paths.empty_state_dir,
        )

        assert completed.returncode
        assert completed.stderr.startswith(COHERENCE_SCOPE.ERROR_PREFIX)
        assert "Traceback (most recent call last):" not in completed.stderr
        assert str(paths.empty_state_dir) in completed.stderr
        assert not completed.stdout
