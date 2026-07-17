"""Mapping evidence for pickup claim reconciliation.

The finite claim-relation domain, source-owned command scripts, and controlled
runner live in ``outcomeeng_testing.harnesses.verify_session_claims``. The real
git repository remains the ``l1`` oracle for git behavior.
"""

from outcomeeng_testing.harnesses.git_context import (
    accepted_git_context,
    handoff_git_env,
)
from outcomeeng_testing.harnesses.verify_session_claims import (
    ABSENT_WORK_BRANCH,
    CHILD_NODE_PATH,
    CLOSED_PR_STATE,
    FAILING_STATUS,
    FULL_HEX_WORK_BRANCH,
    HEX_LIKE_WORK_BRANCH,
    MISSING_SESSION_ERROR,
    NODE_PATH,
    NODE_SPEC,
    PASSING_STATUS,
    PRESENT_FILE,
    PR_NUMBER,
    REACHABLE_WORK_BRANCH,
    RecordingRunner,
    SESSION_ID,
    claim_mapping_cases,
    create_present_file,
    external_state_script,
    head_sha,
    load_verify_session_claims_module,
    missing_session_script,
    node_status_script,
    session_command_scripts,
    verdict_for_kind,
)

module = load_verify_session_claims_module()
Verdict = module.Verdict
ClaimKind = module.ClaimKind


def test_claim_maps_to_verdict() -> None:
    for case in claim_mapping_cases(module):
        with accepted_git_context() as repo:
            session_kwargs, scripted = case.build(repo)
            runner = RecordingRunner(
                repo=repo,
                scripted=session_command_scripts(**session_kwargs) | scripted,
            )

            actual = verdict_for_kind(
                module.verify(SESSION_ID, repo, runner), case.kind
            )

            assert actual.verdict == case.verdict, case.id


def test_node_status_surfaces_changed_value() -> None:
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(specs=(NODE_SPEC,))
            | node_status_script(module, status=FAILING_STATUS),
        )

        verdict = verdict_for_kind(
            module.verify(SESSION_ID, repo, runner), ClaimKind.NODE_STATUS
        )

        assert verdict.verdict == Verdict.CONFIRMED
        assert FAILING_STATUS in verdict.evidence


def test_node_status_evidence_excludes_child_tree() -> None:
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(specs=(NODE_SPEC,))
            | node_status_script(
                module,
                status=PASSING_STATUS,
                include_child=True,
            ),
        )

        verdict = verdict_for_kind(
            module.verify(SESSION_ID, repo, runner), ClaimKind.NODE_STATUS
        )

        assert verdict.verdict == Verdict.CONFIRMED
        assert PASSING_STATUS in verdict.evidence
        assert CHILD_NODE_PATH not in verdict.evidence


def test_external_id_surfaces_changed_state() -> None:
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(pr_numbers=(PR_NUMBER,))
            | external_state_script(module, CLOSED_PR_STATE),
        )

        verdict = verdict_for_kind(
            module.verify(SESSION_ID, repo, runner), ClaimKind.EXTERNAL_ID
        )

        assert verdict.verdict == Verdict.CONFIRMED
        assert CLOSED_PR_STATE in verdict.evidence


def test_spec_entry_emits_both_path_and_node_status() -> None:
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(specs=(NODE_SPEC,))
            | node_status_script(module, status=PASSING_STATUS),
        )

        verdicts = module.verify(SESSION_ID, repo, runner)
        path_verdict = verdict_for_kind(verdicts, ClaimKind.INJECTED_PATH)
        node_verdict = verdict_for_kind(verdicts, ClaimKind.NODE_STATUS)

        assert path_verdict.subject == NODE_SPEC
        assert node_verdict.subject == NODE_PATH


def test_git_ref_branch_on_origin_confirms() -> None:
    with handoff_git_env() as env:
        branch = env.push_work_branch(REACHABLE_WORK_BRANCH)
        runner = RecordingRunner(
            repo=env.root,
            scripted=session_command_scripts(git_ref=branch),
        )

        verdict = verdict_for_kind(
            module.verify(SESSION_ID, env.root, runner), ClaimKind.GIT_REF
        )

        assert verdict.verdict == Verdict.CONFIRMED


def test_hex_like_branch_on_origin_confirms() -> None:
    with handoff_git_env() as env:
        branch = env.push_work_branch(HEX_LIKE_WORK_BRANCH)
        runner = RecordingRunner(
            repo=env.root,
            scripted=session_command_scripts(git_ref=branch),
        )

        verdict = verdict_for_kind(
            module.verify(SESSION_ID, env.root, runner), ClaimKind.GIT_REF
        )

        assert verdict.verdict == Verdict.CONFIRMED


def test_full_hex_branch_on_origin_confirms() -> None:
    with handoff_git_env() as env:
        branch = env.push_work_branch(FULL_HEX_WORK_BRANCH)
        runner = RecordingRunner(
            repo=env.root,
            scripted=session_command_scripts(git_ref=branch),
        )

        verdict = verdict_for_kind(
            module.verify(SESSION_ID, env.root, runner), ClaimKind.GIT_REF
        )

        assert verdict.verdict == Verdict.CONFIRMED


def test_git_ref_branch_absent_from_origin_is_discrepancy() -> None:
    with handoff_git_env() as env:
        runner = RecordingRunner(
            repo=env.root,
            scripted=session_command_scripts(git_ref=ABSENT_WORK_BRANCH),
        )

        verdict = verdict_for_kind(
            module.verify(SESSION_ID, env.root, runner), ClaimKind.GIT_REF
        )

        assert verdict.verdict == Verdict.DISCREPANCY


def test_current_session_frontmatter_shape_still_emits_claims() -> None:
    with accepted_git_context() as repo:
        create_present_file(repo)
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(
                git_ref=head_sha(repo),
                files=(PRESENT_FILE,),
            ),
        )

        verdicts = module.verify(SESSION_ID, repo, runner)

        assert [item.kind for item in verdicts] == [
            ClaimKind.GIT_REF,
            ClaimKind.INJECTED_PATH,
        ]
        assert {item.verdict for item in verdicts} == {Verdict.CONFIRMED}


def test_session_load_failure_is_unverifiable() -> None:
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=missing_session_script(module),
        )

        verdict = verdict_for_kind(
            module.verify(SESSION_ID, repo, runner), ClaimKind.SESSION_METADATA
        )

        assert verdict.verdict == Verdict.UNVERIFIABLE
        assert MISSING_SESSION_ERROR in verdict.evidence
