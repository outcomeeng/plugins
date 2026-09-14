"""Compliance evidence for the implementation-audit scope resolver's run-input boundary."""

import json

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    git_commit_oid,
    stale_local_base_repo,
)
from outcomeeng_testing.harnesses.implementation_scope import (
    ERROR_PREFIX,
    run_implementation_scope,
)


def test_supplied_keys_never_displace_the_resolved_scope() -> None:
    with stale_local_base_repo() as stale:
        forged = json.dumps(
            {
                CHANGESET_SCOPE.ScopeField.BASE: "forged-base",
                CHANGESET_SCOPE.ScopeField.HEAD: "forged-head",
                CHANGESET_SCOPE.ScopeField.CHANGED_PATHS: ["forged/path"],
                "selector": "HEAD",
            }
        )

        completed = run_implementation_scope(
            stale.repo, CHANGESET_SCOPE.HEAD_REF, audit_input=forged
        )

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
        assert resolved["selector"] == "HEAD"


def test_a_non_object_run_input_is_rejected_rather_than_ignored() -> None:
    with stale_local_base_repo() as stale:
        completed = run_implementation_scope(
            stale.repo, CHANGESET_SCOPE.HEAD_REF, audit_input='["not", "an", "object"]'
        )

        assert completed.returncode
        assert completed.stderr.startswith(ERROR_PREFIX)
        assert not completed.stdout


def test_malformed_run_input_json_is_rejected_rather_than_ignored() -> None:
    with stale_local_base_repo() as stale:
        completed = run_implementation_scope(
            stale.repo, CHANGESET_SCOPE.HEAD_REF, audit_input='{"selector": '
        )

        assert completed.returncode
        assert completed.stderr.startswith(ERROR_PREFIX)
        assert not completed.stdout
