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
import subprocess

from collections.abc import Callable
from typing import Any

import pytest
from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    load_journal_emit_module,
    load_review_result_module,
    make_finding_dict,
    run_journal_emit_in_process,
)

je = load_journal_emit_module()
jp = load_journal_projection_module()
review_result = load_review_result_module()

NOW = "2026-06-23T00:00:06Z"
COMPLETED_AT = "2026-06-23T00:00:05Z"


def _metadata() -> Any:
    return jp.RunMetadata(
        target="working-diff",
        scope_hash="abc123def456",
        branch_name="work/example",
        branch_slug="work__example",
        head_sha="1" * 40,
        base_ref="main",
        base_sha="2" * 40,
        config_digest="cfg-abc123",
        participants=("review",),
        scope={"include": ["README.md"]},
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:00Z",
        output_paths=(),
    )


def _finding(*, severity: Any, identifier: str) -> Any:
    return review_result.parse_finding_json(
        json.dumps(
            make_finding_dict(
                id=identifier,
                severity=severity,
                file="README.md",
                line=1,
                rule=(
                    "spx/21-spec-tree.enabler/68-reviewing.enabler/"
                    "21-reviewing-changes.enabler/reviewing-changes.md:ALWAYS:1"
                ),
                message=f"{identifier} evidence",
                action=f"{identifier} action",
            )
        )
    )


def _streamed_events(metadata: Any, findings: tuple[Any, ...]) -> list[dict[str, Any]]:
    """Assemble the event prefix the streaming review appends as it advances."""
    events = [je.scope_entered_event(metadata, now=NOW, attempt=1)]
    events.extend(
        je.finding_reported_event(finding, now=NOW, attempt=1) for finding in findings
    )
    events.append(
        je.run_completed_event(
            metadata, events, completed_at=COMPLETED_AT, now=NOW, attempt=1
        )
    )
    return events


@pytest.mark.parametrize(
    ("severity", "expected_severity", "expected_overall"),
    (
        (review_result.Severity.BLOCKING, jp.Severity.REJECT, jp.Outcome.REJECTED),
        (review_result.Severity.DEBT, jp.Severity.WARNING, jp.Outcome.APPROVED),
    ),
)
def test_adapter_maps_review_severity_to_projection(
    severity: Any, expected_severity: Any, expected_overall: Any
) -> None:
    event = je.finding_reported_event(
        _finding(severity=severity, identifier="F-001"), now=NOW, attempt=1
    )

    assert event["type"] == jp.FINDING_REPORTED
    assert event["data"]["id"] == "F-001"
    assert event["data"]["severity"] == expected_severity
    assert jp.compute_overall([event]) == expected_overall


def test_adapter_terminal_event_carries_core_run_state_identity() -> None:
    metadata = _metadata()
    event = je.run_completed_event(
        metadata, [], completed_at=COMPLETED_AT, now=NOW, attempt=1
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
    assert data[jp.RUN_STATE_PARTICIPANTS] == ["review"]
    assert data[jp.RUN_STATE_SCOPE] == {"include": ["README.md"]}
    assert data[jp.RUN_STATE_STARTED_AT] == metadata.started_at
    # The run-completed event carries the real completion time, not the
    # provisional start-time the start-of-run metadata bakes in.
    assert data[jp.RUN_STATE_COMPLETED_AT] == COMPLETED_AT
    assert data[jp.RUN_STATE_STATUS] == jp.JournalRunStatus.APPROVED


def test_adapter_terminal_event_carries_pull_request_identity() -> None:
    metadata = jp.RunMetadata(
        target="working-diff",
        scope_hash="abc123def456",
        branch_name="work/example",
        branch_slug="work__example",
        head_sha="1" * 40,
        base_ref="main",
        base_sha="2" * 40,
        config_digest="cfg-abc123",
        participants=("review",),
        scope={"include": ["README.md"]},
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:00Z",
        target_kind=jp.JournalTargetKind.PULL_REQUEST,
        pull_request_number=123,
    )
    event = je.run_completed_event(
        metadata, [], completed_at=COMPLETED_AT, now=NOW, attempt=1
    )
    data = event["data"]

    assert data[jp.RUN_STATE_TARGET_KIND] == jp.JournalTargetKind.PULL_REQUEST
    assert data[jp.RUN_STATE_PULL_REQUEST_NUMBER] == 123


def test_render_events_counts_review_findings_by_render_class() -> None:
    events = _streamed_events(
        _metadata(),
        (
            _finding(severity=review_result.Severity.BLOCKING, identifier="F-001"),
            _finding(severity=review_result.Severity.DEBT, identifier="F-002"),
        ),
    )
    rendered = je.render_events(events)

    assert rendered["blocking"] == "1"
    assert rendered["debt"] == "1"
    assert rendered["countLine"] == "BLOCKING: 1, DEBT: 1"


def test_terminal_event_rejects_missing_base_identity() -> None:
    metadata = jp.RunMetadata(
        target="working-diff",
        scope_hash="abc123def456",
        branch_name="work/example",
        branch_slug="work__example",
        head_sha="1" * 40,
        base_ref="main",
        base_sha="",
        config_digest="cfg-abc123",
        participants=("review",),
        scope={"include": ["README.md"]},
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:00Z",
    )

    with pytest.raises(ValueError, match=jp.RUN_STATE_BASE_SHA):
        je.run_completed_event(
            metadata, [], completed_at=COMPLETED_AT, now=NOW, attempt=1
        )


def _write_skill_config(root: pathlib.Path, *, prompt: str) -> None:
    references = root / "references"
    references.mkdir(parents=True)
    (references / "review-prompt.md").write_text(prompt, encoding="utf-8")


def _write_review_manifest(
    root: pathlib.Path,
    *,
    base_ref: str = "origin/main",
    head_ref: str = "HEAD",
    files: list[str] | None = None,
    diff_sha256: str = "a" * 64,
) -> pathlib.Path:
    manifest = {
        "schema_version": je.MANIFEST_SCHEMA_VERSION,
        "base_ref": base_ref,
        "head_ref": head_ref,
        "diff_path": "diff.md",
        "diff_sha256": diff_sha256,
        "diff_bytes": 1,
        "sections": [
            {
                "title": "Committed diff",
                "files": files or ["README.md"],
                "start_line": 1,
                "line_count": 1,
                "byte_start": 0,
                "byte_length": 1,
            }
        ],
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _stub_review_metadata_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(je, "review_config_digest", lambda: "cfg-abc123")
    monkeypatch.setattr(
        je.changeset_scope, "branch_slug", lambda branch: "work__example"
    )
    monkeypatch.setattr(
        je.changeset_scope, "commit_oid", lambda ref, repo: f"{ref}:sha"
    )


def _stub_review_refs(
    monkeypatch: pytest.MonkeyPatch,
    *,
    base_ref: str = "origin/main",
    head_ref: str = "HEAD",
    branch_name: str = "work/example",
) -> None:
    monkeypatch.setattr(je, "_resolve_base_ref", lambda: base_ref)
    monkeypatch.setattr(je, "_resolve_head_ref", lambda: head_ref)
    monkeypatch.setattr(je, "_resolve_branch_name", lambda: branch_name)


def _stub_review_diff(
    monkeypatch: pytest.MonkeyPatch,
    *,
    changed_files: list[str] | None = None,
    combined_diff: Callable[[str, str], str] | None = None,
) -> None:
    files = changed_files if changed_files is not None else ["README.md"]
    diff = combined_diff
    if diff is None:

        def default_combined_diff(_base_ref: str, _head_ref: str) -> str:
            return "### Committed diff\n\nREADME change"

        diff = default_combined_diff
    monkeypatch.setattr(
        je.changeset_scope,
        "expand_diff_range",
        lambda range_spec, *, repo: list(files),
    )
    monkeypatch.setattr(je.compute_diff, "combined_diff", diff)


def test_config_digest_changes_with_review_prompt(tmp_path: pathlib.Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write_skill_config(first, prompt="review prompt one")
    _write_skill_config(second, prompt="review prompt two")

    assert je.review_config_digest(first) != je.review_config_digest(second)


def test_config_digest_ignores_root_review_policy(
    tmp_path: pathlib.Path,
) -> None:
    skill = tmp_path / "skill"
    _write_skill_config(skill, prompt="same review prompt")
    review_policy = tmp_path / "REVIEW.md"
    review_policy.write_text("ignored review policy", encoding="utf-8")
    first_digest = je.review_config_digest(skill)

    review_policy.write_text("changed ignored review policy", encoding="utf-8")

    assert first_digest == je.review_config_digest(skill)


def test_metadata_config_digest_ignores_root_review_policy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    repo_root = tmp_path / "repo"
    subdir = repo_root / "nested"
    subdir.mkdir(parents=True)
    (repo_root / "REVIEW.md").write_text("ignored review policy", encoding="utf-8")

    monkeypatch.chdir(subdir)
    _stub_review_refs(monkeypatch)
    _stub_review_metadata_identity(monkeypatch)
    _stub_review_diff(monkeypatch)

    metadata = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
    )

    assert metadata[jp.RUN_STATE_CONFIG_DIGEST] == "cfg-abc123"


def test_metadata_scope_hash_includes_changed_file_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    changed_files = ["README.md"]
    review_input = "### Committed diff\n\nREADME change"

    _stub_review_refs(monkeypatch)
    _stub_review_metadata_identity(monkeypatch)
    _stub_review_diff(
        monkeypatch,
        changed_files=changed_files,
        combined_diff=lambda base_ref, head_ref: review_input,
    )

    first = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
    )
    changed_files.append("src/plugins/spec-tree/skills/review-changes/SKILL.md")
    second = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
    )

    assert first[jp.RUN_STATE_SCOPE]["changedFiles"] == ["README.md"]
    assert second[jp.RUN_STATE_SCOPE]["changedFiles"] == [
        "README.md",
        "src/plugins/spec-tree/skills/review-changes/SKILL.md",
    ]
    assert first[jp.RUN_STATE_SCOPE_HASH] != second[jp.RUN_STATE_SCOPE_HASH]


def test_metadata_scope_uses_computed_review_manifest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    manifest_path = _write_review_manifest(
        tmp_path,
        base_ref="origin/main",
        head_ref="HEAD",
        files=["src/plugins/spec-tree/skills/review-changes/SKILL.md", "README.md"],
        diff_sha256="b" * 64,
    )

    monkeypatch.setattr(je, "_resolve_branch_name", lambda: "work/example")
    _stub_review_metadata_identity(monkeypatch)

    metadata = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
        review_manifest_path=manifest_path,
    )

    assert metadata[jp.RUN_STATE_SCOPE]["changedFiles"] == [
        "src/plugins/spec-tree/skills/review-changes/SKILL.md",
        "README.md",
    ]
    assert metadata[jp.RUN_STATE_SCOPE]["reviewInputSha256"] == "b" * 64
    assert metadata[jp.RUN_STATE_BASE_REF] == "origin/main"
    assert metadata[jp.RUN_STATE_HEAD_SHA] == "HEAD:sha"


def test_metadata_for_worktree_records_pull_request_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPX_VERIFY_TARGET_KIND", "pull-request")
    monkeypatch.setenv("SPX_VERIFY_PULL_REQUEST_NUMBER", "123")
    _stub_review_refs(monkeypatch, head_ref="origin/work/example")
    _stub_review_metadata_identity(monkeypatch)
    _stub_review_diff(monkeypatch)

    metadata = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
    )

    assert metadata[jp.RUN_STATE_TARGET_KIND] == jp.JournalTargetKind.PULL_REQUEST
    assert metadata[jp.RUN_STATE_PULL_REQUEST_NUMBER] == 123


def test_metadata_for_worktree_uses_env_branch_in_detached_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_current_branch(repo: pathlib.Path) -> str:
        raise je.changeset_scope.DetachedHeadError(f"detached HEAD at {repo}")

    monkeypatch.setenv("SPX_VERIFY_BASE_REF", "origin/main")
    monkeypatch.setenv("SPX_VERIFY_HEAD_REF", "origin/work/example")
    monkeypatch.setenv("SPX_VERIFY_BRANCH", "work/example")
    monkeypatch.setenv("SPX_VERIFY_TARGET_KIND", "pull-request")
    monkeypatch.setenv("SPX_VERIFY_PULL_REQUEST_NUMBER", "123")
    monkeypatch.setattr(
        je.changeset_scope, "detect_current_branch", fail_current_branch
    )
    _stub_review_metadata_identity(monkeypatch)
    _stub_review_diff(monkeypatch)

    metadata = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
    )

    assert metadata[jp.RUN_STATE_BRANCH_NAME] == "work/example"
    assert metadata[jp.RUN_STATE_BRANCH_SLUG] == "work__example"
    assert metadata[jp.RUN_STATE_TARGET_KIND] == jp.JournalTargetKind.PULL_REQUEST
    assert metadata[jp.RUN_STATE_PULL_REQUEST_NUMBER] == 123


def test_metadata_scope_hash_includes_full_review_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review_inputs = ["### Staged diff\n\nfirst", "### Staged diff\n\nsecond"]

    _stub_review_refs(monkeypatch)
    _stub_review_metadata_identity(monkeypatch)
    _stub_review_diff(
        monkeypatch,
        combined_diff=lambda base_ref, head_ref: review_inputs.pop(0),
    )

    first = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
    )
    second = je.metadata_for_worktree(
        started_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:05Z",
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
    _stub_review_metadata_identity(monkeypatch)
    _stub_review_diff(monkeypatch)

    result = run_journal_emit_in_process(
        "metadata",
        "--started-at",
        "2026-06-23T00:00:00Z",
        "--completed-at",
        "2026-06-23T00:00:05Z",
        "--manifest",
        str(
            _write_review_manifest(
                tmp_path, base_ref="origin/main", head_ref="feature/head"
            )
        ),
        repo=tmp_path,
        env={
            je.ENV_BASE_REF: "origin/main",
            je.ENV_HEAD_REF: "feature/head",
            je.ENV_BRANCH: "work/example",
        },
    )

    assert result.returncode == 0, result.stderr
    metadata = json.loads(result.stdout)
    assert metadata[jp.RUN_STATE_BRANCH_NAME] == "work/example"
    assert metadata[jp.RUN_STATE_BRANCH_SLUG] == "work__example"
    assert metadata[jp.RUN_STATE_HEAD_SHA] == "feature/head:sha"
    assert metadata[jp.RUN_STATE_BASE_REF] == "origin/main"
    assert metadata[jp.RUN_STATE_BASE_SHA] == "origin/main:sha"
    assert metadata[jp.RUN_STATE_CONFIG_DIGEST] == "cfg-abc123"
    assert metadata[jp.RUN_STATE_SCOPE]["baseRef"] == "origin/main"
    assert metadata[jp.RUN_STATE_SCOPE]["headRef"] == "feature/head"
    assert metadata[jp.RUN_STATE_SCOPE]["changedFiles"] == ["README.md"]
    assert metadata[jp.RUN_STATE_STARTED_AT] == "2026-06-23T00:00:00Z"
    assert metadata[jp.RUN_STATE_COMPLETED_AT] == "2026-06-23T00:00:05Z"


def test_metadata_cli_reports_git_failure_without_traceback(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_expand_diff_range(
        range_spec: str, *, repo: pathlib.Path
    ) -> je.changeset_scope.DiffIdentity:
        raise subprocess.CalledProcessError(128, ["git", "diff", range_spec])

    monkeypatch.setattr(je, "_resolve_base_ref", lambda: "origin/nope")
    monkeypatch.setattr(je, "_resolve_head_ref", lambda: "HEAD")
    monkeypatch.setattr(je, "_resolve_branch_name", lambda: "work/example")
    monkeypatch.setattr(
        je.changeset_scope,
        "expand_diff_range",
        fail_expand_diff_range,
    )

    exit_code = je.main(
        [
            "metadata",
            "--started-at",
            "2026-06-23T00:00:00Z",
            "--completed-at",
            "2026-06-23T00:00:05Z",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "returned non-zero exit status 128" in captured.err
    assert "Traceback" not in captured.err


def _metadata_wire_json() -> str:
    """Serialize ``_metadata()`` to the wire shape the streaming CLI reads.

    Mirrors ``metadata_for_worktree``'s output so the CLI-path tests exercise
    the real ``--metadata`` parse without spawning git.
    """
    m = _metadata()
    return json.dumps(
        {
            "target": m.target,
            jp.RUN_STATE_SCOPE_HASH: m.scope_hash,
            jp.RUN_STATE_BRANCH_NAME: m.branch_name,
            jp.RUN_STATE_BRANCH_SLUG: m.branch_slug,
            jp.RUN_STATE_TARGET_KIND: str(jp.JournalTargetKind.BRANCH),
            jp.RUN_STATE_HEAD_SHA: m.head_sha,
            jp.RUN_STATE_BASE_REF: m.base_ref,
            jp.RUN_STATE_BASE_SHA: m.base_sha,
            jp.RUN_STATE_CONFIG_DIGEST: m.config_digest,
            jp.RUN_STATE_PARTICIPANTS: list(m.participants),
            jp.RUN_STATE_SCOPE: dict(m.scope),
            jp.RUN_STATE_STARTED_AT: m.started_at,
            jp.RUN_STATE_COMPLETED_AT: m.completed_at,
            jp.RUN_STATE_OUTPUT_PATHS: [],
        }
    )


def test_scope_entered_cli_emits_identity_event() -> None:
    result = run_journal_emit_in_process(
        "scope-entered",
        "--now",
        NOW,
        "--metadata",
        _metadata_wire_json(),
    )
    assert result.returncode == 0, result.stderr
    event = json.loads(result.stdout)
    assert event["type"] == jp.SCOPE_ENTERED
    assert event["data"]["target"] == "working-diff"
    assert event["data"][jp.RUN_STATE_HEAD_SHA] == "1" * 40


def test_scope_advanced_cli_names_the_unit() -> None:
    result = run_journal_emit_in_process(
        "scope-advanced", "--now", NOW, "--unit", "README.md"
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
    result = run_journal_emit_in_process(
        "finding-reported", "--now", NOW, stdin=json.dumps(make_finding_dict())
    )
    assert result.returncode == 0, result.stderr
    event = json.loads(result.stdout)
    assert event["type"] == jp.FINDING_REPORTED


def test_finding_reported_cli_maps_malformed_finding_to_error_with_no_event() -> None:
    malformed = make_finding_dict()
    del malformed["action"]
    result = run_journal_emit_in_process(
        "finding-reported", "--now", NOW, stdin=json.dumps(malformed)
    )
    assert result.returncode != 0
    assert "action" in result.stderr
    assert result.stdout.strip() == ""


def test_run_completed_cli_reads_prefix_and_sets_completion_time() -> None:
    metadata_json = _metadata_wire_json()
    metadata = json.loads(metadata_json)
    scope_entered = run_journal_emit_in_process(
        "scope-entered", "--now", NOW, "--metadata", metadata_json
    ).stdout.strip()
    finding = run_journal_emit_in_process(
        "finding-reported",
        "--now",
        NOW,
        stdin=json.dumps(make_finding_dict(severity=review_result.Severity.BLOCKING)),
    ).stdout.strip()
    prefix = json.dumps([json.loads(scope_entered), json.loads(finding)])

    result = run_journal_emit_in_process(
        "run-completed",
        "--now",
        NOW,
        "--completed-at",
        COMPLETED_AT,
        "--metadata",
        metadata_json,
        stdin=prefix,
    )
    assert result.returncode == 0, result.stderr
    event = json.loads(result.stdout)
    assert event["type"] == jp.RUN_COMPLETED
    assert event["data"][jp.RUN_STATE_STARTED_AT] == metadata[jp.RUN_STATE_STARTED_AT]
    assert event["data"][jp.RUN_STATE_COMPLETED_AT] == COMPLETED_AT
    # A blocking finding in the streamed prefix rolls up to a rejected run.
    assert event["data"][jp.RUN_STATE_STATUS] == jp.JournalRunStatus.REJECTED
