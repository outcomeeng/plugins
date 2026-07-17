"""Scenario evidence for the /merge changeset classifier."""

from __future__ import annotations

from outcomeeng_testing.harnesses.changeset_scope import (
    canonical_merge_changeset,
    contains_python_traceback,
    load_changeset_scope_module,
    load_merge_classifier_module,
    modified_spaced_note_repo,
    repo_without_origin,
    run_merge_classifier,
)


def test_changed_paths_use_the_canonical_changeset_scope() -> None:
    with canonical_merge_changeset() as stale:
        paths = set(load_merge_classifier_module().changed_paths(stale.repo))
        assert stale.feature_file in paths
        assert stale.merged_file not in paths
        assert stale.working_file in paths


def test_spaced_coordination_note_path_is_preserved() -> None:
    with modified_spaced_note_repo() as spaced:
        classifier = load_merge_classifier_module()
        working = classifier._working_tree_paths(spaced.repo)
        assert spaced.note_path in working
        assert classifier.is_coordination_note(spaced.note_path)


def test_unconfigured_remote_base_is_reported_without_traceback() -> None:
    with repo_without_origin() as repo:
        completed = run_merge_classifier(repo)
        classifier = load_merge_classifier_module()
        changeset_scope = load_changeset_scope_module()
        assert completed.returncode != 0
        assert classifier.BASE_REF_ERROR_PREFIX in completed.stderr
        assert changeset_scope.ORIGIN_HEAD_REF in completed.stderr
        assert not contains_python_traceback(completed.stderr)
