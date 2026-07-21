"""Compliance evidence for pickup claim verification."""

import __future__
import json
import sys

from outcomeeng_testing.harnesses.verify_session_claims import (
    absent_node_status_observation,
    default_runner_failure_observations,
    load_verify_session_claims_module,
    metadata_loading_observation,
    node_status_observations,
    read_only_verification_observation,
    script_import_roots,
    spec_entry_observation,
    subprocess_call_owners,
    unloadable_session_observations,
    verify_parameters,
)


def test_verify_accepts_injected_runner() -> None:
    module = load_verify_session_claims_module()

    assert any(
        parameter.annotation in (module.CommandRunner, module.CommandRunner.__name__)
        for parameter in verify_parameters()
    )


def test_script_imports_are_stdlib_only() -> None:
    assert script_import_roots() <= sys.stdlib_module_names | {__future__.__name__}


def test_external_calls_go_through_the_runner() -> None:
    module = load_verify_session_claims_module()
    owners = subprocess_call_owners()

    assert owners
    assert all(
        owner
        == (module.SubprocessRunner.__name__, module.SubprocessRunner.run.__name__)
        for owner in owners
    )


def test_default_runner_launch_failure_emits_unverifiable() -> None:
    module = load_verify_session_claims_module()
    observations = default_runner_failure_observations()

    assert len(observations) == 1
    assert observations[0].kind is module.ClaimKind.SESSION_METADATA
    assert observations[0].verdict is module.Verdict.UNVERIFIABLE


def test_verification_is_read_only_and_uses_source_commands() -> None:
    module = load_verify_session_claims_module()
    observation = read_only_verification_observation()

    assert observation.calls
    for call in observation.calls:
        assert any(
            call[: len(prefix)] == prefix
            for prefix in (
                tuple(module.SPX_SESSION_SHOW_COMMAND),
                tuple(module.SPX_SPEC_STATUS_COMMAND),
                tuple(module.GIT_VERIFY_REF_COMMAND),
                tuple(module.GIT_STATUS_COMMAND),
                tuple(module.GH_PR_VIEW_COMMAND),
            )
        ), f"unexpected command: {call}"
    assert observation.status_after == observation.status_before


def test_node_status_evidence_is_the_target_node_record_without_children() -> None:
    module = load_verify_session_claims_module()

    for observation in node_status_observations():
        assert observation.actual.verdict is module.Verdict.CONFIRMED
        evidence = json.loads(observation.actual.evidence)
        record = observation.projected_record

        assert (
            evidence[module.NODE_RECORD_ID_FIELD] == record[module.NODE_RECORD_ID_FIELD]
        ), f"{observation.node_path} surfaced another node's record"
        assert module.NODE_RECORD_CHILDREN_FIELD not in evidence
        assert evidence == {
            key: value
            for key, value in record.items()
            if not isinstance(value, list | dict)
        }, f"{observation.node_path} evidence departs from its projection record"


def test_absent_node_resolves_to_unverifiable_naming_the_node() -> None:
    module = load_verify_session_claims_module()
    observation = absent_node_status_observation()

    assert observation.actual.verdict is module.Verdict.UNVERIFIABLE
    assert observation.node_path in observation.actual.evidence


def test_unloadable_session_resolves_to_one_unverifiable_verdict() -> None:
    module = load_verify_session_claims_module()

    for observation in unloadable_session_observations():
        assert len(observation.verdicts) == 1, (
            f"{observation.condition} produced {len(observation.verdicts)} verdicts"
        )
        assert observation.verdicts[0].kind is module.ClaimKind.SESSION_METADATA
        assert observation.verdicts[0].verdict is module.Verdict.UNVERIFIABLE, (
            f"{observation.condition} emitted {observation.verdicts[0].verdict}"
        )


def test_spec_entry_emits_both_path_and_node_status() -> None:
    module = load_verify_session_claims_module()
    observation = spec_entry_observation()

    assert module.ClaimKind.INJECTED_PATH in observation.kinds
    assert module.ClaimKind.NODE_STATUS in observation.kinds


def test_metadata_loading_does_not_require_local_session_file_body() -> None:
    module = load_verify_session_claims_module()
    observation = metadata_loading_observation()

    assert (
        *module.SPX_SESSION_SHOW_COMMAND,
        module.SPX_SESSION_SHOW_JSON_FLAG,
        observation.session_id,
    ) in observation.calls
    assert (
        *module.SPX_SESSION_SHOW_COMMAND,
        observation.session_id,
    ) in observation.calls
    assert observation.actual.verdict is module.Verdict.CONFIRMED
