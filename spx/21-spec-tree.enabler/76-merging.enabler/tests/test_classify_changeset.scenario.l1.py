"""Scenario evidence for the /merge changeset classifier."""

from __future__ import annotations

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE_CONTRACT,
    MERGE_CLASSIFIER,
    canonical_merge_changeset,
    contains_python_traceback,
    modified_spaced_note_repo,
    repo_without_origin,
    run_merge_classifier,
)


def test_changed_paths_use_the_canonical_changeset_scope() -> None:
    with canonical_merge_changeset() as stale:
        assert frozenset(MERGE_CLASSIFIER.changed_paths(stale.repo)) == frozenset(
            (stale.feature_file, stale.working_file)
        )


def test_spaced_coordination_note_path_is_preserved() -> None:
    with modified_spaced_note_repo() as spaced:
        assert tuple(MERGE_CLASSIFIER._working_tree_paths(spaced.repo)) == (
            spaced.note_path,
        )
        assert MERGE_CLASSIFIER.is_coordination_note(spaced.note_path)


def test_unconfigured_remote_base_is_reported_without_traceback() -> None:
    with repo_without_origin() as repo:
        completed = run_merge_classifier(repo)
        assert completed.returncode
        assert MERGE_CLASSIFIER.BASE_REF_ERROR_PREFIX in completed.stderr
        assert CHANGESET_SCOPE_CONTRACT.ORIGIN_HEAD_REF in completed.stderr
        assert not contains_python_traceback(completed.stderr)
