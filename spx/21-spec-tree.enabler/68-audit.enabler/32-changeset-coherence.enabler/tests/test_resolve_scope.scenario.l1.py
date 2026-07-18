"""Scenario evidence for the coherence audit's committed-scope resolver."""

from __future__ import annotations

import json

from outcomeeng_testing.harnesses.changeset_scope import (
    COHERENCE_SCOPE,
    contains_python_traceback,
    repo_without_origin,
    run_coherence_scope,
    stale_local_base_repo,
)


def test_branch_scope_excludes_commits_already_merged_to_the_base() -> None:
    """A stale local base ref never widens the resolved scope.

    The fixture's feature branch carries a commit already present on
    ``origin/<base>``. Composing against the lagging local ref would re-admit
    that merged file; composing against the remote-tracking ref keeps the merge
    base at the true branch point, so only the feature's own change resolves.
    """
    with stale_local_base_repo() as stale:
        completed = run_coherence_scope(stale.repo, "HEAD")

        assert not completed.returncode
        resolved = json.loads(completed.stdout)
        assert frozenset(resolved["changed_paths"]) == frozenset((stale.feature_file,))
        assert stale.merged_file not in resolved["changed_paths"]


def test_resolved_identities_are_full_commit_object_ids() -> None:
    with stale_local_base_repo() as stale:
        resolved = json.loads(run_coherence_scope(stale.repo, "HEAD").stdout)

        assert len(resolved["base"]) == 40
        assert len(resolved["head"]) == 40
        assert resolved["base"] != resolved["head"]


def test_explicit_commit_range_resolves_both_endpoints() -> None:
    with stale_local_base_repo() as stale:
        branch_form = json.loads(run_coherence_scope(stale.repo, "HEAD").stdout)
        range_form = json.loads(
            run_coherence_scope(stale.repo, f"origin/{stale.base_ref}...HEAD").stdout
        )

        assert range_form == branch_form


def test_unconfigured_remote_base_is_reported_without_traceback() -> None:
    with repo_without_origin() as repo:
        completed = run_coherence_scope(repo, "HEAD")

        assert completed.returncode
        assert COHERENCE_SCOPE.ERROR_PREFIX in completed.stderr
        assert not contains_python_traceback(completed.stderr)


def test_malformed_commit_range_is_rejected_without_traceback() -> None:
    with stale_local_base_repo() as stale:
        completed = run_coherence_scope(stale.repo, "origin/main...")

        assert completed.returncode
        assert COHERENCE_SCOPE.ERROR_PREFIX in completed.stderr
        assert not contains_python_traceback(completed.stderr)
