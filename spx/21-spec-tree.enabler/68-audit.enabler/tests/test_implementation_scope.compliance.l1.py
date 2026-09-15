"""Compliance evidence for the implementation-audit scope resolver's run-input boundary."""

import json

from outcomeeng.validation.implementation_audit_contract import (
    ImplementationAuditConcern,
)
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
    run_implementation_scope_against_recorded_run,
    run_implementation_scope_with_unlaunchable_spx,
)

LANGUAGE = "typescript"
CONCERN = ImplementationAuditConcern.CODE


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
                language=LANGUAGE,
                concern=CONCERN,
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
    subjects = ("src/pending.ts", "docs/left-to-its-owner.md")
    required_unit = audit_scope_unit(
        subjects[0],
        language=LANGUAGE,
        concern=CONCERN,
        requirement=REQUIRED_COVERAGE,
        status=pending,
    )
    accounting_unit = audit_scope_unit(
        subjects[1],
        language=LANGUAGE,
        concern=CONCERN,
        requirement=accounting,
        status=pending,
    )

    verdict = reconcile(subjects, subjects, (required_unit, accounting_unit))

    assert verdict[RECONCILE_FIELD.NONFINAL] == [required_unit[AUDIT_FIELD.UNIT_ID]]
    assert verdict[RECONCILE_FIELD.UNACCOUNTED] == []
    assert verdict[RECONCILE_FIELD.RECONCILED] is False


def test_a_run_reconciles_only_on_exact_inventory_agreement() -> None:
    sealed = ("src/one.ts", "src/two.ts")
    units = tuple(
        audit_scope_unit(
            subject,
            language=LANGUAGE,
            concern=CONCERN,
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
                language=LANGUAGE,
                concern=CONCERN,
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


def test_an_unlaunchable_cli_yields_a_diagnostic_rather_than_an_unreconciled_verdict() -> (
    None
):
    with stale_local_base_repo() as stale:
        completed = run_implementation_scope_with_unlaunchable_spx(
            stale.repo,
            CHANGESET_SCOPE.HEAD_REF,
            reconcile_run="1999-01-01_00-00-00-000-000000000000",
            scope_identity="0000000000000000000000000000000000000000..1111111111111111111111111111111111111111",
        )

        assert completed.returncode == 2
        assert completed.stderr.startswith(RECONCILE_PREFIX)
        assert not completed.stdout


def test_a_recorded_run_reconciles_against_a_fresh_resolution_of_its_selector() -> None:
    with stale_local_base_repo() as stale:
        identity = f"{stale.base_ref}..{stale.feature_branch}"
        final = sorted(FINAL_COVERAGE_STATUSES)[0]
        unit = audit_scope_unit(
            stale.feature_file,
            language=LANGUAGE,
            concern=CONCERN,
            requirement=REQUIRED_COVERAGE,
            status=final,
        )
        phantom = "src/never-changed.ts"
        phantom_unit = audit_scope_unit(
            phantom,
            language=LANGUAGE,
            concern=CONCERN,
            requirement=REQUIRED_COVERAGE,
            status=final,
        )

        agreed = run_implementation_scope_against_recorded_run(
            stale.repo,
            CHANGESET_SCOPE.HEAD_REF,
            reconcile_run="1999-01-01_00-00-00-000-000000000000",
            scope_identity=identity,
            recorded_changed_paths=[stale.feature_file],
            scope_units=[unit],
        )
        drifted = run_implementation_scope_against_recorded_run(
            stale.repo,
            CHANGESET_SCOPE.HEAD_REF,
            reconcile_run="1999-01-01_00-00-00-000-000000000000",
            scope_identity=identity,
            recorded_changed_paths=[stale.feature_file, phantom],
            scope_units=[unit, phantom_unit],
        )

        assert agreed.returncode == 0
        assert json.loads(agreed.stdout)[RECONCILE_FIELD.RECONCILED] is True
        assert drifted.returncode == 1
        verdict = json.loads(drifted.stdout)
        assert verdict[RECONCILE_FIELD.DRIFTED] == [phantom]
        assert verdict[RECONCILE_FIELD.UNACCOUNTED] == []
        assert verdict[RECONCILE_FIELD.RECONCILED] is False
