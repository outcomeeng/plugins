"""Compliance evidence for the implementation-audit scope resolver's run-input boundary."""

import json

from outcomeeng.validation.implementation_audit_contract import (
    AuditCoverageRequirement,
    AuditCoverageStatus,
    ImplementationAuditConcern,
    implementation_audit_concern_skill_name,
)
from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    source_language,
)
from outcomeeng_testing.harnesses.changeset_scope import (
    ORIGIN_HEAD_REF,
    CHANGESET_SCOPE,
    git_commit_oid,
    stale_local_base_repo,
)
from outcomeeng_testing.generators.changeset_scope import distinct_subject_paths
from outcomeeng_testing.harnesses.implementation_scope import (
    ABSENT_RUN_TOKEN,
    AUDIT_FIELD,
    ERROR_PREFIX,
    EXIT_COMMAND_FAILURE,
    EXIT_UNRECONCILED,
    FINAL_COVERAGE_STATUSES,
    INPUT_COMMAND,
    LIVE_PATHS_KEY,
    MISSING_SKILL_STATUS,
    RECONCILE_FIELD,
    RECONCILE_PREFIX,
    RENDER_COMMAND,
    REQUIRED_COVERAGE,
    SCOPE_IDENTITY_OPTION,
    SENTINEL_SCOPE_IDENTITY,
    audit_scope_unit,
    reconcile,
    run_implementation_scope,
    run_implementation_scope_against_recorded_run,
    run_implementation_scope_recording_every_command,
    run_implementation_scope_with_unlaunchable_spx,
    spx_scope_arguments,
    spx_subcommands,
)

LANGUAGE = source_language()
CONCERN = ImplementationAuditConcern.CODE
FINAL = AuditCoverageStatus.AUDITED.value


def test_supplied_keys_never_displace_the_resolved_scope() -> None:
    with stale_local_base_repo() as stale:
        forged_base, forged_head, forged_path = distinct_subject_paths(3)
        forged = json.dumps(
            {
                CHANGESET_SCOPE.ScopeField.BASE: forged_base,
                CHANGESET_SCOPE.ScopeField.HEAD: forged_head,
                CHANGESET_SCOPE.ScopeField.CHANGED_PATHS: [forged_path],
            }
        )

        completed = run_implementation_scope(
            stale.repo, CHANGESET_SCOPE.HEAD_REF, audit_input=forged
        )

        assert not completed.returncode
        resolved = json.loads(completed.stdout)
        assert resolved[CHANGESET_SCOPE.ScopeField.BASE] == git_commit_oid(
            stale.repo, ORIGIN_HEAD_REF
        )
        assert resolved[CHANGESET_SCOPE.ScopeField.HEAD] == git_commit_oid(
            stale.repo, stale.feature_branch
        )
        assert resolved[CHANGESET_SCOPE.ScopeField.CHANGED_PATHS] == [
            stale.feature_file
        ]


def test_a_non_object_run_input_is_rejected_rather_than_ignored() -> None:
    with stale_local_base_repo() as stale:
        completed = run_implementation_scope(
            stale.repo, CHANGESET_SCOPE.HEAD_REF, audit_input='["not", "an", "object"]'
        )

        assert completed.returncode == EXIT_COMMAND_FAILURE
        assert completed.stderr.startswith(ERROR_PREFIX)
        assert not completed.stdout


def test_malformed_run_input_json_is_rejected_rather_than_ignored() -> None:
    with stale_local_base_repo() as stale:
        completed = run_implementation_scope(
            stale.repo, CHANGESET_SCOPE.HEAD_REF, audit_input='{"selector": '
        )

        assert completed.returncode == EXIT_COMMAND_FAILURE
        assert completed.stderr.startswith(ERROR_PREFIX)
        assert not completed.stdout


def test_a_sealed_path_without_a_recorded_unit_leaves_the_run_unreconciled() -> None:
    covered, omitted = distinct_subject_paths(2)

    verdict = reconcile(
        (covered, omitted),
        (covered, omitted),
        (
            audit_scope_unit(
                covered,
                language=LANGUAGE,
                concern=CONCERN,
                requirement=REQUIRED_COVERAGE,
                status=FINAL,
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
    pending = AuditCoverageStatus.SKIPPED.value
    accounting = AuditCoverageRequirement.OPTIONAL.value
    assert pending not in FINAL_COVERAGE_STATUSES
    assert accounting != REQUIRED_COVERAGE
    subjects = distinct_subject_paths(2)
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
    paths = distinct_subject_paths(4)
    sealed, (outside, extra) = paths[:2], paths[2:]
    units = tuple(
        audit_scope_unit(
            subject,
            language=LANGUAGE,
            concern=CONCERN,
            requirement=REQUIRED_COVERAGE,
            status=FINAL,
        )
        for subject in sealed
    )

    agreed = reconcile(sealed, sealed, units)
    drifted_wider = reconcile(sealed, (*sealed, extra), units)
    drifted_narrower = reconcile(sealed, sealed[:1], units)
    widened = reconcile(
        sealed,
        sealed,
        (
            *units,
            audit_scope_unit(
                outside,
                language=LANGUAGE,
                concern=CONCERN,
                requirement=REQUIRED_COVERAGE,
                status=FINAL,
            ),
        ),
    )

    assert agreed[RECONCILE_FIELD.RECONCILED] is True
    assert drifted_wider[RECONCILE_FIELD.DRIFTED] == [extra]
    assert drifted_wider[RECONCILE_FIELD.RECONCILED] is False
    assert drifted_narrower[RECONCILE_FIELD.DRIFTED] == [sealed[1]]
    assert drifted_narrower[RECONCILE_FIELD.RECONCILED] is False
    assert widened[RECONCILE_FIELD.UNEXPECTED] == [outside]
    assert widened[RECONCILE_FIELD.RECONCILED] is False


def test_an_unreadable_run_yields_a_diagnostic_rather_than_a_verdict() -> None:
    with stale_local_base_repo() as stale:
        completed = run_implementation_scope(
            stale.repo,
            CHANGESET_SCOPE.HEAD_REF,
            reconcile_run=ABSENT_RUN_TOKEN,
            scope_identity=SENTINEL_SCOPE_IDENTITY,
        )

        assert completed.returncode == EXIT_COMMAND_FAILURE
        assert completed.stderr.startswith(RECONCILE_PREFIX)
        assert ABSENT_RUN_TOKEN in completed.stderr
        assert SCOPE_IDENTITY_OPTION not in completed.stderr
        assert not completed.stdout


def test_a_reconcile_request_without_a_sealed_identity_is_rejected() -> None:
    with stale_local_base_repo() as stale:
        completed = run_implementation_scope_recording_every_command(
            stale.repo,
            CHANGESET_SCOPE.HEAD_REF,
            reconcile_run=ABSENT_RUN_TOKEN,
        )

        assert completed.returncode == EXIT_COMMAND_FAILURE
        assert completed.stderr.startswith(RECONCILE_PREFIX)
        assert SCOPE_IDENTITY_OPTION in completed.stderr
        assert not completed.stdout
        # The request fails before any command runs: git resolution included.
        assert completed.recorded_launches == ()


def test_an_unlaunchable_cli_yields_a_diagnostic_rather_than_an_unreconciled_verdict() -> (
    None
):
    with stale_local_base_repo() as stale:
        completed = run_implementation_scope_with_unlaunchable_spx(
            stale.repo,
            CHANGESET_SCOPE.HEAD_REF,
            reconcile_run=ABSENT_RUN_TOKEN,
            scope_identity=SENTINEL_SCOPE_IDENTITY,
        )

        assert completed.returncode == EXIT_COMMAND_FAILURE
        assert completed.stderr.startswith(RECONCILE_PREFIX)
        assert not completed.stdout


def test_a_recorded_run_reconciles_against_a_fresh_resolution_of_its_selector() -> None:
    with stale_local_base_repo() as stale:
        identity = SENTINEL_SCOPE_IDENTITY
        (phantom,) = distinct_subject_paths(1)
        unit = audit_scope_unit(
            stale.feature_file,
            language=LANGUAGE,
            concern=CONCERN,
            requirement=REQUIRED_COVERAGE,
            status=FINAL,
        )
        phantom_unit = audit_scope_unit(
            phantom,
            language=LANGUAGE,
            concern=CONCERN,
            requirement=REQUIRED_COVERAGE,
            status=FINAL,
        )

        agreed = run_implementation_scope_against_recorded_run(
            stale.repo,
            CHANGESET_SCOPE.HEAD_REF,
            reconcile_run=ABSENT_RUN_TOKEN,
            scope_identity=identity,
            recorded_input={
                CHANGESET_SCOPE.ScopeField.CHANGED_PATHS: [stale.feature_file]
            },
            scope_units=[unit],
        )
        drifted = run_implementation_scope_against_recorded_run(
            stale.repo,
            CHANGESET_SCOPE.HEAD_REF,
            reconcile_run=ABSENT_RUN_TOKEN,
            scope_identity=identity,
            recorded_input={
                CHANGESET_SCOPE.ScopeField.CHANGED_PATHS: [stale.feature_file, phantom]
            },
            scope_units=[unit, phantom_unit],
        )

        assert agreed.returncode == 0
        assert json.loads(agreed.stdout)[RECONCILE_FIELD.RECONCILED] is True
        # The locator addresses the run by the sealed identity handed in, never
        # by the fresh resolution: the sentinel identity cannot match any commit.
        assert spx_subcommands(agreed) == (INPUT_COMMAND, RENDER_COMMAND)
        assert spx_scope_arguments(agreed) == (identity, identity)
        assert drifted.returncode == EXIT_UNRECONCILED
        verdict = json.loads(drifted.stdout)
        assert verdict[RECONCILE_FIELD.DRIFTED] == [phantom]
        assert verdict[RECONCILE_FIELD.UNACCOUNTED] == []
        assert verdict[RECONCILE_FIELD.RECONCILED] is False


def test_an_advisory_live_path_is_expected_beside_the_committed_inventory() -> None:
    with stale_local_base_repo() as stale:
        (live,) = distinct_subject_paths(1)
        recorded_input = {
            CHANGESET_SCOPE.ScopeField.CHANGED_PATHS: [stale.feature_file],
            LIVE_PATHS_KEY: [live],
        }
        committed_unit = audit_scope_unit(
            stale.feature_file,
            language=LANGUAGE,
            concern=CONCERN,
            requirement=REQUIRED_COVERAGE,
            status=FINAL,
        )
        live_unit = audit_scope_unit(
            live,
            language=LANGUAGE,
            concern=CONCERN,
            requirement=REQUIRED_COVERAGE,
            status=FINAL,
        )

        covered = run_implementation_scope_against_recorded_run(
            stale.repo,
            CHANGESET_SCOPE.HEAD_REF,
            reconcile_run=ABSENT_RUN_TOKEN,
            scope_identity=SENTINEL_SCOPE_IDENTITY,
            recorded_input=recorded_input,
            scope_units=[committed_unit, live_unit],
        )
        uncovered = run_implementation_scope_against_recorded_run(
            stale.repo,
            CHANGESET_SCOPE.HEAD_REF,
            reconcile_run=ABSENT_RUN_TOKEN,
            scope_identity=SENTINEL_SCOPE_IDENTITY,
            recorded_input=recorded_input,
            scope_units=[committed_unit],
        )

        # A live path is an expected subject, never unexpected, and it never
        # counts as drift: drift is judged on the committed inventory alone.
        assert covered.returncode == 0
        assert json.loads(covered.stdout)[RECONCILE_FIELD.DRIFTED] == []
        assert uncovered.returncode == EXIT_UNRECONCILED
        assert json.loads(uncovered.stdout)[RECONCILE_FIELD.UNACCOUNTED] == [live]


def test_a_run_document_the_comparison_cannot_read_yields_a_diagnostic() -> None:
    with stale_local_base_repo() as stale:
        completed = run_implementation_scope_against_recorded_run(
            stale.repo,
            CHANGESET_SCOPE.HEAD_REF,
            reconcile_run=ABSENT_RUN_TOKEN,
            scope_identity=SENTINEL_SCOPE_IDENTITY,
            recorded_input={
                CHANGESET_SCOPE.ScopeField.CHANGED_PATHS: [stale.feature_file]
            },
            scope_units={AUDIT_FIELD.SUBJECT: stale.feature_file},
        )

        assert completed.returncode == EXIT_COMMAND_FAILURE
        assert completed.stderr.startswith(RECONCILE_PREFIX)
        assert not completed.stdout


def test_a_missing_skill_unit_names_its_absent_skill_and_is_never_unexpected() -> None:
    (path,) = distinct_subject_paths(1)
    absent_concern = ImplementationAuditConcern.ARCHITECTURE
    path_unit = audit_scope_unit(
        path,
        language=LANGUAGE,
        concern=CONCERN,
        requirement=REQUIRED_COVERAGE,
        status=FINAL,
    )
    missing_unit = audit_scope_unit(
        implementation_audit_concern_skill_name(LANGUAGE, absent_concern),
        language=LANGUAGE,
        concern=absent_concern,
        requirement=REQUIRED_COVERAGE,
        status=MISSING_SKILL_STATUS,
    )

    verdict = reconcile((path,), (path,), (path_unit, missing_unit))

    # The absent skill's name is the unit's subject, not a path, so it stands
    # beside the path units without counting as a subject outside the inventory.
    assert verdict[RECONCILE_FIELD.UNEXPECTED] == []
    assert verdict[RECONCILE_FIELD.NONFINAL] == []
    assert verdict[RECONCILE_FIELD.RECONCILED] is True
