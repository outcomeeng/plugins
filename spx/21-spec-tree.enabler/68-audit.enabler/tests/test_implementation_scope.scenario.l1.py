"""Scenario evidence for implementation-audit scope discovery."""

import json

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    git_commit_oid,
    stale_local_base_repo,
    temporary_changeset_scope,
)
from outcomeeng_testing.harnesses.implementation_scope import (
    ERROR_PREFIX,
    run_implementation_scope,
)


def test_scope_discovery_preserves_remote_base_and_feature_identity() -> None:
    with stale_local_base_repo() as stale:
        completed = run_implementation_scope(stale.repo, CHANGESET_SCOPE.HEAD_REF)

        assert not completed.returncode
        resolved = json.loads(completed.stdout)
        assert resolved[CHANGESET_SCOPE.ScopeField.BASE] == git_commit_oid(
            stale.repo, CHANGESET_SCOPE.remote_tracking_ref(stale.base_ref)
        )
        assert resolved[CHANGESET_SCOPE.ScopeField.HEAD] == git_commit_oid(
            stale.repo, stale.feature_branch
        )
        assert resolved[CHANGESET_SCOPE.ScopeField.CHANGED_PATHS] == [
            stale.feature_file
        ]


def test_scope_discovery_reports_a_nonexistent_repository() -> None:
    with temporary_changeset_scope() as paths:
        completed = run_implementation_scope(
            paths.repo, CHANGESET_SCOPE.HEAD_REF, repo_override=paths.empty_state_dir
        )

        assert completed.returncode
        assert completed.stderr.startswith(ERROR_PREFIX)
        assert str(paths.empty_state_dir) in completed.stderr
        assert "Traceback (most recent call last):" not in completed.stderr
        assert not completed.stdout
