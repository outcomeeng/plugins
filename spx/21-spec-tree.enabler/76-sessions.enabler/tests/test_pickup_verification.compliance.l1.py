"""Compliance evidence for pickup claim verification.

The assertion file checks the shipped script through source-owned command and
metadata contracts plus reusable inspection infrastructure. The injected
recording runner exercises the approved Stage 5 exception boundary without
framework mocking.
"""

import json

from outcomeeng_testing.harnesses.git_context import accepted_git_context
from outcomeeng_testing.harnesses.verify_session_claims import (
    EXPECTED_SUBPROCESS_CALL_SITES,
    CLEAN_GIT_STATUS,
    INVALID_JSON_ERROR,
    INVALID_JSON_FRAGMENT,
    MALFORMED_METADATA_ERROR,
    NODE_SPEC,
    PASSING_STATUS,
    PR_NUMBER,
    RUNNER_PARAMETER,
    SESSION_ID,
    SINGLE_VERDICT_COUNT,
    UNREACHABLE_SHA,
    WRONG_SHAPE_ERROR,
    WRONG_SHAPE_JSON,
    RecordingRunner,
    empty_path_environment,
    expected_node_status_evidence,
    head_sha,
    load_verify_session_claims_module,
    malformed_metadata_payloads,
    metadata_payload_script,
    metadata_script,
    node_status_script,
    non_stdlib_import_roots,
    session_command_scripts,
    session_show_command,
    session_show_json_command,
    subprocess_call_sites,
    unexpected_runner_calls,
    verdict_for_kind,
    verify_runner_parameter_name,
)

module = load_verify_session_claims_module()
ClaimKind = module.ClaimKind
Verdict = module.Verdict


def test_verify_accepts_injected_runner() -> None:
    assert verify_runner_parameter_name(module) == RUNNER_PARAMETER


def test_script_imports_are_stdlib_only() -> None:
    assert not non_stdlib_import_roots()


def test_external_calls_go_through_the_runner() -> None:
    assert subprocess_call_sites() == EXPECTED_SUBPROCESS_CALL_SITES


def test_default_runner_launch_failure_emits_unverifiable() -> None:
    with accepted_git_context() as repo:
        verdicts = module.verify(
            SESSION_ID,
            repo,
            module.SubprocessRunner(repo, env=empty_path_environment()),
        )

    assert len(verdicts) == SINGLE_VERDICT_COUNT
    assert verdicts[0].kind == ClaimKind.SESSION_METADATA
    assert verdicts[0].verdict == Verdict.UNVERIFIABLE


def test_verification_is_read_only_and_uses_source_commands() -> None:
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(
                git_ref=UNREACHABLE_SHA,
                git_status=CLEAN_GIT_STATUS,
                specs=(NODE_SPEC,),
                pr_numbers=(PR_NUMBER,),
            )
            | node_status_script(module, status=PASSING_STATUS),
        )

        module.verify(SESSION_ID, repo, runner)

        assert session_show_json_command(module) in runner.calls
        assert session_show_command(module) in runner.calls
        assert not unexpected_runner_calls(module, runner.calls)
        dirty = RecordingRunner(repo=repo).run(list(module.GIT_STATUS_COMMAND))[1]
        assert not dirty.strip()


def test_node_status_evidence_keeps_target_node_scalar_fields_only() -> None:
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(specs=(NODE_SPEC,))
            | node_status_script(
                module,
                status=PASSING_STATUS,
                include_child=True,
                include_non_scalar=True,
            ),
        )

        verdict = verdict_for_kind(
            module.verify(SESSION_ID, repo, runner), ClaimKind.NODE_STATUS
        )

        assert json.loads(verdict.evidence) == expected_node_status_evidence(
            module,
            status=PASSING_STATUS,
        )


def test_invalid_session_metadata_is_unverifiable() -> None:
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=metadata_script(module, INVALID_JSON_FRAGMENT),
        )

        verdict = verdict_for_kind(
            module.verify(SESSION_ID, repo, runner), ClaimKind.SESSION_METADATA
        )

        assert verdict.verdict == Verdict.UNVERIFIABLE
        assert INVALID_JSON_ERROR in verdict.evidence


def test_wrong_shape_session_metadata_is_unverifiable() -> None:
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=metadata_script(module, WRONG_SHAPE_JSON),
        )

        verdict = verdict_for_kind(
            module.verify(SESSION_ID, repo, runner), ClaimKind.SESSION_METADATA
        )

        assert verdict.verdict == Verdict.UNVERIFIABLE
        assert WRONG_SHAPE_ERROR in verdict.evidence


def test_malformed_session_metadata_fields_are_unverifiable() -> None:
    for payload in malformed_metadata_payloads(module):
        with accepted_git_context() as repo:
            runner = RecordingRunner(
                repo=repo,
                scripted=metadata_payload_script(module, payload),
            )

            verdict = verdict_for_kind(
                module.verify(SESSION_ID, repo, runner), ClaimKind.SESSION_METADATA
            )

            assert verdict.verdict == Verdict.UNVERIFIABLE
            assert MALFORMED_METADATA_ERROR in verdict.evidence


def test_metadata_loading_does_not_require_local_session_file_body() -> None:
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(git_ref=head_sha(repo)),
        )

        verdict = verdict_for_kind(
            module.verify(SESSION_ID, repo, runner), ClaimKind.GIT_REF
        )

        assert verdict.verdict == Verdict.CONFIRMED
