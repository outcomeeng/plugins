"""Scenario evidence for the /merge changeset classifier's environment failures."""

from __future__ import annotations

from outcomeeng_testing.harnesses.changeset_scope import (
    MERGE_CLASSIFIER,
    classifier_tree_without_scope_module,
    directory_outside_git_worktree,
    git_failure_stderr,
    repo_with_git_absent_from_path,
    run_merge_classifier,
)


def test_missing_scope_module_names_the_path_the_skills_and_the_reinstall_fix() -> None:
    with classifier_tree_without_scope_module() as tree:
        completed = run_merge_classifier(tree.repo, script=tree.classifier)
        assert completed.returncode == 1
        assert completed.stderr.startswith(MERGE_CLASSIFIER.BASE_REF_ERROR_PREFIX)
        assert "Traceback (most recent call last):" not in completed.stderr
        assert str(tree.missing_module) in completed.stderr
        assert str(tree.skills_dir) in completed.stderr
        for entry in tree.skills_entries:
            assert entry in completed.stderr
        assert "reinstall the product-tree plugin" in completed.stderr.lower()
        assert "scope-changeset skill" in completed.stderr
        assert "beside the merge skill" in completed.stderr


def test_git_absent_from_path_is_named_with_the_install_fix() -> None:
    with repo_with_git_absent_from_path() as gitless:
        completed = run_merge_classifier(gitless.repo, env=gitless.env)
        assert completed.returncode == 1
        assert completed.stderr.startswith(MERGE_CLASSIFIER.BASE_REF_ERROR_PREFIX)
        assert "Traceback (most recent call last):" not in completed.stderr
        assert "git is not on PATH" in completed.stderr
        assert "install git or add it to path" in completed.stderr.lower()


def test_directory_outside_a_git_worktree_reports_the_status_failure_and_fix() -> None:
    with directory_outside_git_worktree() as directory:
        completed = run_merge_classifier(directory)
        assert completed.returncode == 1
        assert completed.stderr.startswith(MERGE_CLASSIFIER.BASE_REF_ERROR_PREFIX)
        assert "Traceback (most recent call last):" not in completed.stderr
        assert "git status" in completed.stderr
        assert git_failure_stderr(directory, "status") in completed.stderr
        assert "inside a git working tree" in completed.stderr
