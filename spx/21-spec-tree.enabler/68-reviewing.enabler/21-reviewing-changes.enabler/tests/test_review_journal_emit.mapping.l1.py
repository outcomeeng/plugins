"""Mapping evidence for the review consumer's run-journal adapter.

Covers the reviewing-changes assertions that the streaming review records the
run on ``spx journal --type review`` through the shared projection's per-event
builders — a finding maps onto a finding-reported event and the terminal
run-completed event carries the reviewed diff's identity — and that the
per-finding parse (``journal_emit.py finding-reported``) is the live validity
gate before any journal append.
"""

from __future__ import annotations

import json
import pathlib

from typing import Any

import pytest
from outcomeeng_testing.generators.reviewing_changes import (
    changed_review_file_sets,
    distinct_review_inputs,
    finding_without_required_field,
    review_severity_projection_cases,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    REVIEW_COMPLETION_TIME,
    REVIEW_EVENT_TIME,
    ReviewMetadataHarness,
    make_finding_dict,
    review_contract_modules,
    review_config_digests,
    review_finding,
    review_metadata_wire_json,
    review_run_metadata,
    run_journal_emit_in_process,
    streamed_review_events,
    write_review_manifest,
    write_review_skill_config,
)


@pytest.mark.parametrize(
    ("severity", "expected_severity", "expected_overall"),
    review_severity_projection_cases(),
)
def test_adapter_maps_review_severity_to_projection(
    severity: Any, expected_severity: Any, expected_overall: Any
) -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    finding = review_finding(severity=severity)
    event = je.finding_reported_event(finding, now=REVIEW_EVENT_TIME, attempt=1)

    assert event["type"] == jp.FINDING_REPORTED
    assert event["data"]["id"] == finding.id
    assert event["data"]["severity"] == expected_severity
    assert jp.compute_overall([event]) == expected_overall


def test_adapter_terminal_event_carries_core_run_state_identity() -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    metadata = review_run_metadata()
    event = je.run_completed_event(
        metadata,
        [],
        completed_at=REVIEW_COMPLETION_TIME,
        now=REVIEW_EVENT_TIME,
        attempt=1,
    )
    data = event["data"]

    assert event["type"] == jp.RUN_COMPLETED
    assert data[jp.RUN_STATE_BRANCH_NAME] == metadata.branch_name
    assert data[jp.RUN_STATE_BRANCH_SLUG] == metadata.branch_slug
    assert data[jp.RUN_STATE_TARGET_KIND] == jp.JournalTargetKind.BRANCH
    assert data[jp.RUN_STATE_HEAD_SHA] == metadata.head_sha
    assert data[jp.RUN_STATE_BASE_REF] == metadata.base_ref
    assert data[jp.RUN_STATE_BASE_SHA] == metadata.base_sha
    assert data[jp.RUN_STATE_CONFIG_DIGEST] == metadata.config_digest
    assert data[jp.RUN_STATE_PARTICIPANTS] == list(metadata.participants)
    assert data[jp.RUN_STATE_SCOPE] == dict(metadata.scope)
    assert data[jp.RUN_STATE_STARTED_AT] == metadata.started_at
    # The run-completed event carries the real completion time, not the
    # provisional start-time the start-of-run metadata bakes in.
    assert data[jp.RUN_STATE_COMPLETED_AT] == REVIEW_COMPLETION_TIME
    assert data[jp.RUN_STATE_STATUS] == jp.JournalRunStatus.APPROVED


def test_adapter_terminal_event_carries_pull_request_identity() -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    metadata = review_run_metadata(pull_request=True)
    event = je.run_completed_event(
        metadata,
        [],
        completed_at=REVIEW_COMPLETION_TIME,
        now=REVIEW_EVENT_TIME,
        attempt=1,
    )
    data = event["data"]

    assert data[jp.RUN_STATE_TARGET_KIND] == jp.JournalTargetKind.PULL_REQUEST
    assert data[jp.RUN_STATE_PULL_REQUEST_NUMBER] == metadata.pull_request_number


def test_render_events_counts_review_findings_by_render_class() -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    review_result = contracts.review_result
    events = streamed_review_events(
        review_run_metadata(),
        (
            review_finding(severity=review_result.Severity.BLOCKING),
            review_finding(severity=review_result.Severity.DEBT),
        ),
    )
    rendered = je.render_events(events)

    assert rendered[je.RENDER_BLOCKING_FIELD] == "1"
    assert rendered[je.RENDER_DEBT_FIELD] == "1"
    assert rendered[je.RENDER_COUNT_LINE_FIELD] == "BLOCKING: 1, DEBT: 1"
    assert rendered[je.RENDER_OVERALL_FIELD] == str(jp.Outcome.REJECTED)
    assert rendered[je.RENDER_SURFACE_FIELD] == jp.render_surface(events)


def test_terminal_event_rejects_missing_base_identity() -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    metadata = review_run_metadata(missing_base_identity=True)

    with pytest.raises(ValueError, match=jp.RUN_STATE_BASE_SHA):
        je.run_completed_event(
            metadata,
            [],
            completed_at=REVIEW_COMPLETION_TIME,
            now=REVIEW_EVENT_TIME,
            attempt=1,
        )


def test_config_digest_changes_with_review_prompt(tmp_path: pathlib.Path) -> None:
    je = review_contract_modules().journal_emit
    first = tmp_path / "first"
    second = tmp_path / "second"
    write_review_skill_config(first, prompt="review prompt one")
    write_review_skill_config(second, prompt="review prompt two")

    assert je.review_config_digest(first) != je.review_config_digest(second)


def test_runner_and_adapter_share_review_config_identity() -> None:
    assert len(set(review_config_digests())) == 1


def test_config_digest_ignores_root_review_policy(
    tmp_path: pathlib.Path,
) -> None:
    je = review_contract_modules().journal_emit
    skill = tmp_path / "skill"
    write_review_skill_config(skill, prompt="same review prompt")
    review_policy = tmp_path / "REVIEW.md"
    review_policy.write_text("ignored review policy", encoding="utf-8")
    first_digest = je.review_config_digest(skill)

    review_policy.write_text("changed ignored review policy", encoding="utf-8")

    assert first_digest == je.review_config_digest(skill)


def test_metadata_config_digest_ignores_root_review_policy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    repo_root = tmp_path / "repo"
    subdir = repo_root / "nested"
    subdir.mkdir(parents=True)
    (repo_root / "REVIEW.md").write_text("ignored review policy", encoding="utf-8")

    monkeypatch.chdir(subdir)
    harness = ReviewMetadataHarness()

    metadata = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
        deps=harness.deps(),
    )

    assert metadata[jp.RUN_STATE_CONFIG_DIGEST] == "cfg-abc123"


def test_metadata_scope_hash_includes_changed_file_set() -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    first_files, second_files = changed_review_file_sets()
    harness = ReviewMetadataHarness(changed_files=first_files)

    first = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
        deps=harness.deps(),
    )
    harness.changed_files = second_files
    second = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
        deps=harness.deps(),
    )

    assert first[jp.RUN_STATE_SCOPE][je.SCOPE_CHANGED_FILES_FIELD] == first_files
    assert second[jp.RUN_STATE_SCOPE][je.SCOPE_CHANGED_FILES_FIELD] == second_files
    assert first[jp.RUN_STATE_SCOPE_HASH] != second[jp.RUN_STATE_SCOPE_HASH]


def test_metadata_scope_uses_computed_review_manifest(
    tmp_path: pathlib.Path,
) -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    manifest_path = write_review_manifest(
        tmp_path,
        base_ref="origin/main",
        head_ref="HEAD",
        files=["src/plugins/spec-tree/skills/review-changes/SKILL.md", "README.md"],
        diff_sha256="b" * 64,
    )

    harness = ReviewMetadataHarness()

    metadata = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
        review_manifest_path=manifest_path,
        deps=harness.deps(manifest_scope=True),
    )

    assert metadata[jp.RUN_STATE_SCOPE]["changedFiles"] == [
        "src/plugins/spec-tree/skills/review-changes/SKILL.md",
        "README.md",
    ]
    assert metadata[jp.RUN_STATE_SCOPE]["reviewInputSha256"] == "b" * 64
    assert metadata[jp.RUN_STATE_BASE_REF] == "origin/main"
    assert metadata[jp.RUN_STATE_HEAD_SHA] == harness.metadata.head_sha


def test_metadata_for_worktree_records_pull_request_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    monkeypatch.setenv("SPX_VERIFY_TARGET_KIND", "pull-request")
    monkeypatch.setenv("SPX_VERIFY_PULL_REQUEST_NUMBER", "123")
    harness = ReviewMetadataHarness(head_ref="origin/work/example")

    metadata = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
        deps=harness.deps(source_target=True),
    )

    assert metadata[jp.RUN_STATE_TARGET_KIND] == jp.JournalTargetKind.PULL_REQUEST
    assert metadata[jp.RUN_STATE_PULL_REQUEST_NUMBER] == 123


def test_metadata_for_worktree_uses_env_branch_in_detached_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    monkeypatch.setenv("SPX_VERIFY_BASE_REF", "origin/main")
    monkeypatch.setenv("SPX_VERIFY_HEAD_REF", "origin/work/example")
    monkeypatch.setenv("SPX_VERIFY_BRANCH", "work/example")
    monkeypatch.setenv("SPX_VERIFY_TARGET_KIND", "pull-request")
    monkeypatch.setenv("SPX_VERIFY_PULL_REQUEST_NUMBER", "123")
    harness = ReviewMetadataHarness(head_ref="origin/work/example")

    metadata = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
        deps=harness.deps(source_branch=True, source_target=True),
    )

    assert metadata[jp.RUN_STATE_BRANCH_NAME] == "work/example"
    assert metadata[jp.RUN_STATE_BRANCH_SLUG] == "work__example"
    assert metadata[jp.RUN_STATE_TARGET_KIND] == jp.JournalTargetKind.PULL_REQUEST
    assert metadata[jp.RUN_STATE_PULL_REQUEST_NUMBER] == 123


def test_metadata_scope_hash_includes_full_review_input() -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    harness = ReviewMetadataHarness(
        review_inputs=list(distinct_review_inputs()),
    )

    first = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
        deps=harness.deps(),
    )
    second = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
        deps=harness.deps(),
    )

    assert first[jp.RUN_STATE_SCOPE]["changedFiles"] == ["README.md"]
    assert (
        first[jp.RUN_STATE_SCOPE]["reviewInputSha256"]
        != second[jp.RUN_STATE_SCOPE]["reviewInputSha256"]
    )
    assert first[jp.RUN_STATE_SCOPE_HASH] != second[jp.RUN_STATE_SCOPE_HASH]


def test_metadata_cli_emits_env_derived_run_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    harness = ReviewMetadataHarness(
        base_ref="origin/main",
        head_ref="feature/head",
    )

    result = run_journal_emit_in_process(
        "metadata",
        "--started-at",
        "2026-06-23T00:00:00Z",
        "--completed-at",
        "2026-06-23T00:00:05Z",
        "--manifest",
        str(
            write_review_manifest(
                tmp_path, base_ref="origin/main", head_ref="feature/head"
            )
        ),
        repo=tmp_path,
        env={
            je.ENV_BASE_REF: "origin/main",
            je.ENV_HEAD_REF: "feature/head",
            je.ENV_BRANCH: "work/example",
        },
        metadata_deps=harness.deps(
            source_branch=True,
            manifest_scope=True,
        ),
    )

    assert result.returncode == 0, result.stderr
    metadata = json.loads(result.stdout)
    assert metadata[jp.RUN_STATE_BRANCH_NAME] == "work/example"
    assert metadata[jp.RUN_STATE_BRANCH_SLUG] == "work__example"
    assert metadata[jp.RUN_STATE_HEAD_SHA] == harness.metadata.head_sha
    assert metadata[jp.RUN_STATE_BASE_REF] == "origin/main"
    assert metadata[jp.RUN_STATE_BASE_SHA] == harness.metadata.base_sha
    assert metadata[jp.RUN_STATE_CONFIG_DIGEST] == "cfg-abc123"
    assert metadata[jp.RUN_STATE_SCOPE]["baseRef"] == "origin/main"
    assert metadata[jp.RUN_STATE_SCOPE]["headRef"] == "feature/head"
    assert metadata[jp.RUN_STATE_SCOPE]["changedFiles"] == ["README.md"]
    assert metadata[jp.RUN_STATE_STARTED_AT] == "2026-06-23T00:00:00Z"
    assert metadata[jp.RUN_STATE_COMPLETED_AT] == "2026-06-23T00:00:05Z"


def test_metadata_cli_reports_git_failure_without_traceback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    je = review_contract_modules().journal_emit
    harness = ReviewMetadataHarness(base_ref="origin/nope")

    exit_code = je.main(
        [
            "metadata",
            "--started-at",
            "2026-06-23T00:00:00Z",
            "--completed-at",
            "2026-06-23T00:00:05Z",
        ],
        metadata_deps=harness.deps(fail_scope=True),
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "returned non-zero exit status 128" in captured.err
    assert "Traceback" not in captured.err


def test_scope_entered_cli_emits_identity_event() -> None:
    contracts = review_contract_modules()
    jp = contracts.journal_projection
    result = run_journal_emit_in_process(
        "scope-entered",
        "--now",
        REVIEW_EVENT_TIME,
        "--metadata",
        review_metadata_wire_json(),
    )
    assert result.returncode == 0, result.stderr
    event = json.loads(result.stdout)
    assert event["type"] == jp.SCOPE_ENTERED
    assert event["data"]["target"] == "working-diff"
    assert event["data"][jp.RUN_STATE_HEAD_SHA] == "1" * 40


def test_scope_advanced_cli_names_the_unit() -> None:
    jp = review_contract_modules().journal_projection
    result = run_journal_emit_in_process(
        "scope-advanced", "--now", REVIEW_EVENT_TIME, "--unit", "README.md"
    )
    assert result.returncode == 0, result.stderr
    event = json.loads(result.stdout)
    assert event["type"] == jp.SCOPE_ADVANCED
    assert event["data"]["unit"] == "README.md"


# finding-reported is the per-finding validity gate: a conforming finding maps
# to one finding-reported event (exit 0); a malformed finding maps to a
# non-zero exit naming the violation with no event emitted. The domain is the
# finite {conforming, malformed} set — the per-finding parse rejection is the
# live gate before any journal append.
def test_finding_reported_cli_maps_conforming_finding_to_event() -> None:
    jp = review_contract_modules().journal_projection
    result = run_journal_emit_in_process(
        "finding-reported",
        "--now",
        REVIEW_EVENT_TIME,
        stdin=json.dumps(make_finding_dict()),
    )
    assert result.returncode == 0, result.stderr
    event = json.loads(result.stdout)
    assert event["type"] == jp.FINDING_REPORTED


def test_finding_reported_cli_maps_malformed_finding_to_error_with_no_event() -> None:
    malformed = finding_without_required_field("action")
    result = run_journal_emit_in_process(
        "finding-reported", "--now", REVIEW_EVENT_TIME, stdin=json.dumps(malformed)
    )
    assert result.returncode != 0
    assert "action" in result.stderr
    assert result.stdout.strip() == ""


def test_run_completed_cli_reads_prefix_and_sets_completion_time() -> None:
    contracts = review_contract_modules()
    jp = contracts.journal_projection
    review_result = contracts.review_result
    metadata_json = review_metadata_wire_json()
    metadata = json.loads(metadata_json)
    scope_entered = run_journal_emit_in_process(
        "scope-entered", "--now", REVIEW_EVENT_TIME, "--metadata", metadata_json
    ).stdout.strip()
    finding = run_journal_emit_in_process(
        "finding-reported",
        "--now",
        REVIEW_EVENT_TIME,
        stdin=json.dumps(make_finding_dict(severity=review_result.Severity.BLOCKING)),
    ).stdout.strip()
    prefix = json.dumps([json.loads(scope_entered), json.loads(finding)])

    result = run_journal_emit_in_process(
        "run-completed",
        "--now",
        REVIEW_EVENT_TIME,
        "--completed-at",
        REVIEW_COMPLETION_TIME,
        "--metadata",
        metadata_json,
        stdin=prefix,
    )
    assert result.returncode == 0, result.stderr
    event = json.loads(result.stdout)
    assert event["type"] == jp.RUN_COMPLETED
    assert event["data"][jp.RUN_STATE_STARTED_AT] == metadata[jp.RUN_STATE_STARTED_AT]
    assert event["data"][jp.RUN_STATE_COMPLETED_AT] == REVIEW_COMPLETION_TIME
    # A blocking finding in the streamed prefix rolls up to a rejected run.
    assert event["data"][jp.RUN_STATE_STATUS] == jp.JournalRunStatus.REJECTED
