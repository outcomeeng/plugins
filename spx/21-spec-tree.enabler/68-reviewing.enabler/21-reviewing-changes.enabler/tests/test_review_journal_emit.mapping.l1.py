"""Mapping evidence for the review consumer's run-journal adapter.

Covers the reviewing-changes assertions that the skill records the validated
review result on ``spx journal --type review`` through the shared projection,
and that the terminal event carries the reviewed diff's identity.
"""

from __future__ import annotations

import pathlib

from typing import Any

import pytest
from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    load_journal_emit_module,
    load_review_result_module,
    make_review_result_dict,
)

je = load_journal_emit_module()
jp = load_journal_projection_module()
review_result = load_review_result_module()


def _metadata() -> Any:
    return je.ReviewRunMetadata(
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
        completed_at="2026-06-23T00:00:05Z",
        output_paths=(),
    )


def _review_with_findings(findings: list[dict[str, Any]]) -> Any:
    return review_result.from_json_dict(make_review_result_dict(findings=findings))


def _finding(*, severity: Any, identifier: str) -> dict[str, Any]:
    return {
        "id": identifier,
        "concern": review_result.Concern.STANDARDS,
        "severity": severity,
        "file": "README.md",
        "line": 1,
        "rule": (
            "spx/21-spec-tree.enabler/68-reviewing.enabler/"
            "21-reviewing-changes.enabler/reviewing-changes.md:ALWAYS:1"
        ),
        "message": f"{identifier} evidence",
        "action": f"{identifier} action",
    }


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
    result = _review_with_findings([_finding(severity=severity, identifier="F-001")])
    events = je.events_for_review(result, _metadata(), now="2026-06-23T00:00:06Z")
    finding_events = [event for event in events if event["type"] == jp.FINDING_REPORTED]

    assert finding_events[0]["data"]["severity"] == expected_severity
    assert jp.compute_overall(events) == expected_overall


def test_adapter_terminal_event_carries_core_run_state_identity() -> None:
    result = _review_with_findings([])
    metadata = _metadata()
    events = je.events_for_review(result, metadata, now="2026-06-23T00:00:06Z")
    data = events[-1]["data"]

    assert events[-1]["type"] == jp.RUN_COMPLETED
    assert data[jp.RUN_STATE_BRANCH_NAME] == metadata.branch_name
    assert data[jp.RUN_STATE_BRANCH_SLUG] == metadata.branch_slug
    assert data[jp.RUN_STATE_HEAD_SHA] == metadata.head_sha
    assert data[jp.RUN_STATE_BASE_REF] == metadata.base_ref
    assert data[jp.RUN_STATE_BASE_SHA] == metadata.base_sha
    assert data[jp.RUN_STATE_CONFIG_DIGEST] == metadata.config_digest
    assert data[jp.RUN_STATE_PARTICIPANTS] == ["review"]
    assert data[jp.RUN_STATE_SCOPE] == {"include": ["README.md"]}
    assert data[jp.RUN_STATE_STATUS] == jp.JournalRunStatus.APPROVED


def test_adapter_rejects_missing_base_identity() -> None:
    result = _review_with_findings([])
    metadata = je.ReviewRunMetadata(
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
        completed_at="2026-06-23T00:00:05Z",
    )

    with pytest.raises(ValueError, match=jp.RUN_STATE_BASE_SHA):
        je.events_for_review(result, metadata, now="2026-06-23T00:00:06Z")


def _write_skill_config(
    root: pathlib.Path, *, prompt: str, document_template: str = "document"
) -> None:
    references = root / "references"
    render = references / "render"
    render.mkdir(parents=True)
    (references / "review-prompt.md").write_text(prompt, encoding="utf-8")
    (render / "document.md").write_text(document_template, encoding="utf-8")
    (render / "finding.md").write_text("finding", encoding="utf-8")


def test_config_digest_changes_with_review_prompt(tmp_path: pathlib.Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write_skill_config(first, prompt="review prompt one")
    _write_skill_config(second, prompt="review prompt two")

    assert je.review_config_digest(first) != je.review_config_digest(second)


def test_config_digest_changes_with_render_template(tmp_path: pathlib.Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write_skill_config(first, prompt="review prompt", document_template="document one")
    _write_skill_config(
        second, prompt="review prompt", document_template="document two"
    )

    assert je.review_config_digest(first) != je.review_config_digest(second)
