"""Compliance evidence for the implementation-audit scope resolver's run-input boundary."""

import json

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    git_commit_oid,
    stale_local_base_repo,
)
from outcomeeng_testing.harnesses.implementation_scope import (
    AUDIT_FIELD,
    ERROR_PREFIX,
    FINAL_COVERAGE_STATUSES,
    RECONCILE_FIELD,
    RECONCILE_PREFIX,
    REQUIRED_COVERAGE,
    SCOPE_IDENTITY_OPTION,
    audit_scope_unit,
    reconcile,
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


def test_a_sealed_path_without_a_recorded_unit_leaves_the_run_unreconciled() -> None:
    covered, omitted = "src/covered.ts", "src/omitted.ts"

    verdict = reconcile(
        (covered, omitted),
        (covered, omitted),
        (
            audit_scope_unit(
                covered,
                requirement=REQUIRED_COVERAGE,
                status=sorted(FINAL_COVERAGE_STATUSES)[0],
            ),
        ),
    )

    assert verdict[RECONCILE_FIELD.UNACCOUNTED] == [omitted]
    assert verdict[RECONCILE_FIELD.EXPECTED] == 2
    assert verdict[RECONCILE_FIELD.RECORDED] == 1
    assert verdict[RECONCILE_FIELD.RECONCILED] is False


def test_a_required_unit_outside_the_final_statuses_leaves_the_run_unreconciled() -> (
    None
):
    pending, accounting = "incomplete", "optional"
    assert pending not in FINAL_COVERAGE_STATUSES
    assert accounting != REQUIRED_COVERAGE
    required_unit = audit_scope_unit(
        "src/pending.ts", requirement=REQUIRED_COVERAGE, status=pending
    )
    accounting_unit = audit_scope_unit(
        "docs/left-to-its-owner.md", requirement=accounting, status=pending
    )

    verdict = reconcile(
        (required_unit[AUDIT_FIELD.SUBJECT], accounting_unit[AUDIT_FIELD.SUBJECT]),
        (required_unit[AUDIT_FIELD.SUBJECT], accounting_unit[AUDIT_FIELD.SUBJECT]),
        (required_unit, accounting_unit),
    )

    assert verdict[RECONCILE_FIELD.NONFINAL] == [required_unit[AUDIT_FIELD.UNIT_ID]]
    assert verdict[RECONCILE_FIELD.UNACCOUNTED] == []
    assert verdict[RECONCILE_FIELD.RECONCILED] is False


def test_a_run_reconciles_only_on_exact_inventory_agreement() -> None:
    sealed = ("src/one.ts", "src/two.ts")
    units = tuple(
        audit_scope_unit(
            subject,
            requirement=REQUIRED_COVERAGE,
            status=sorted(FINAL_COVERAGE_STATUSES)[0],
        )
        for subject in sealed
    )

    agreed = reconcile(sealed, sealed, units)
    drifted_wider = reconcile(sealed, (*sealed, "src/three.ts"), units)
    drifted_narrower = reconcile(sealed, sealed[:1], units)
    widened = reconcile(
        sealed,
        sealed,
        (
            *units,
            audit_scope_unit(
                "src/outside.ts",
                requirement=REQUIRED_COVERAGE,
                status=sorted(FINAL_COVERAGE_STATUSES)[0],
            ),
        ),
    )

    assert agreed[RECONCILE_FIELD.RECONCILED] is True
    assert drifted_wider[RECONCILE_FIELD.DRIFTED] == ["src/three.ts"]
    assert drifted_wider[RECONCILE_FIELD.RECONCILED] is False
    assert drifted_narrower[RECONCILE_FIELD.DRIFTED] == [sealed[1]]
    assert drifted_narrower[RECONCILE_FIELD.RECONCILED] is False
    assert widened[RECONCILE_FIELD.UNEXPECTED] == ["src/outside.ts"]
    assert widened[RECONCILE_FIELD.RECONCILED] is False


def test_an_unreadable_run_yields_a_diagnostic_rather_than_a_verdict() -> None:
    with stale_local_base_repo() as stale:
        completed = run_implementation_scope(
            stale.repo,
            CHANGESET_SCOPE.HEAD_REF,
            reconcile_run="1999-01-01_00-00-00-000-000000000000",
            scope_identity="0000000000000000000000000000000000000000..1111111111111111111111111111111111111111",
        )

        assert completed.returncode
        assert completed.stderr.startswith(RECONCILE_PREFIX)
        assert SCOPE_IDENTITY_OPTION not in completed.stderr
        assert not completed.stdout


def test_a_reconcile_request_without_a_sealed_identity_is_rejected() -> None:
    with stale_local_base_repo() as stale:
        completed = run_implementation_scope(
            stale.repo,
            CHANGESET_SCOPE.HEAD_REF,
            reconcile_run="1999-01-01_00-00-00-000-000000000000",
        )

        assert completed.returncode
        assert completed.stderr.startswith(RECONCILE_PREFIX)
        assert SCOPE_IDENTITY_OPTION in completed.stderr
        assert not completed.stdout
